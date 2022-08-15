#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
tool/fileutil.py: File routines for the 'mmgen-tool' utility
"""

import os

from .common import tool_cmd_base
from ..util import msg,msg_r,qmsg,die,suf,parse_bytespec,make_full_path
from ..crypto import get_random,aesctr_iv_len

class tool_cmd(tool_cmd_base):
	"file utilities"

	def find_incog_data(self,
			filename: str,
			incog_id: str,
			keep_searching: 'continue search after finding data (ID collisions can yield false positives)' = False):
		"Use an Incog ID to find hidden incognito wallet data"

		from hashlib import sha256
		from ..globalvars import g

		ivsize,bsize,mod = ( aesctr_iv_len, 4096, 4096*8 )
		n,carry = 0,b' '*ivsize
		flgs = os.O_RDONLY|os.O_BINARY if g.platform == 'win' else os.O_RDONLY
		f = os.open(filename,flgs)
		for ch in incog_id:
			if ch not in '0123456789ABCDEF':
				die(2,f'{incog_id!r}: invalid Incog ID')
		while True:
			d = os.read(f,bsize)
			if not d:
				break
			d = carry + d
			for i in range(bsize):
				if sha256(d[i:i+ivsize]).hexdigest()[:8].upper() == incog_id:
					if n+i < ivsize:
						continue
					msg(f'\rIncog data for ID {incog_id} found at offset {n+i-ivsize}')
					if not keep_searching:
						import sys
						sys.exit(0)
			carry = d[len(d)-ivsize:]
			n += bsize
			if not n % mod:
				msg_r(f'\rSearched: {n} bytes')

		msg('')
		os.close(f)
		return True

	def rand2file(self,outfile:str,nbytes:str,threads=4,silent=False):
		"""
		write ‘nbytes’ bytes of random data to specified file (dd-style byte specifiers supported)

		Valid specifiers:

		  c  = 1
		  w  = 2
		  b  = 512
		  kB = 1000
		  K  = 1024
		  MB = 1000000
		  M  = 1048576
		  GB = 1000000000
		  G  = 1073741824
		  TB = 1000000000000
		  T  = 1099511627776
		  PB = 1000000000000000
		  P  = 1125899906842624
		  EB = 1000000000000000000
		  E  = 1152921504606846976
		"""
		from threading import Thread
		from queue import Queue
		from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
		from cryptography.hazmat.backends import default_backend

		from ..opts import opt

		def encrypt_worker(wid):
			ctr_init_val = os.urandom( aesctr_iv_len )
			c = Cipher( algorithms.AES(key), modes.CTR(ctr_init_val), backend=default_backend() )
			encryptor = c.encryptor()
			while True:
				q2.put( encryptor.update(q1.get()) )
				q1.task_done()

		def output_worker():
			while True:
				f.write( q2.get() )
				q2.task_done()

		nbytes = parse_bytespec(nbytes)
		if opt.outdir:
			outfile = make_full_path( opt.outdir, outfile )
		f = open(outfile,'wb')

		key = get_random(32)
		q1,q2 = ( Queue(), Queue() )

		for i in range(max(1,threads-2)):
			t = Thread( target=encrypt_worker, args=[i] )
			t.daemon = True
			t.start()

		t = Thread( target=output_worker )
		t.daemon = True
		t.start()

		blk_size = 1024 * 1024
		for i in range(nbytes // blk_size):
			if not i % 4:
				msg_r(f'\rRead: {i * blk_size} bytes')
			q1.put( os.urandom(blk_size) )

		if nbytes % blk_size:
			q1.put( os.urandom(nbytes % blk_size) )

		q1.join()
		q2.join()
		f.close()

		fsize = os.stat(outfile).st_size
		if fsize != nbytes:
			die(3,f'{fsize}: incorrect random file size (should be {nbytes})')

		if not silent:
			msg(f'\rRead: {nbytes} bytes')
			qmsg(f'\r{nbytes} byte{suf(nbytes)} of random data written to file {outfile!r}')

		return True

	def extract_key_from_geth_wallet( self, wallet_file:str, check_addr=True ):
		"decrypt the encrypted private key in a Geth keystore wallet, returning the decrypted key"
		from ..util import line_input
		from ..opts import opt
		from ..base_proto.ethereum.misc import extract_key_from_geth_keystore_wallet
		passwd = line_input( 'Enter passphrase: ', echo=opt.echo_passphrase ).strip().encode()
		return extract_key_from_geth_keystore_wallet( wallet_file, passwd, check_addr ).hex()
