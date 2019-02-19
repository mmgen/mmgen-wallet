#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>
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
tool.py:  Routines and data for the 'mmgen-tool' utility
"""

import binascii
from collections import OrderedDict

from mmgen.protocol import hash160
from mmgen.common import *
from mmgen.crypto import *
from mmgen.tx import *
from mmgen.addr import *

pnm = g.proj_name
cmd_data = OrderedDict([
	('help',         ['<tool command> [str]']),
	('usage',        ['<tool command> [str]']),
	('strtob58',     ['<string> [str-]','pad [int=0]']),
	('b58tostr',     ['<b58 number> [str-]']),
	('hextob58',     ['<hex number> [str-]','pad [int=0]']),
	('hextob58chk',  ['<hex number> [str-]']),
	('b58tohex',     ['<b58 number> [str-]','pad [int=0]']),
	('b58chktohex',  ['<b58 number> [str-]']),
	('b58randenc',   []),
	('b32tohex',     ['<b32 num> [str-]','pad [int=0]']),
	('hextob32',     ['<hex num> [str-]','pad [int=0]']),
	('randhex',      ['nbytes [int=32]']),
	('id8',          ['<infile> [str]']),
	('id6',          ['<infile> [str]']),
	('hash160',      ['<hexadecimal string> [str-]']),
	('hash256',      ['<str, hexstr or filename> [str]', # TODO handle stdin
							'hex_input [bool=False]','file_input [bool=False]']),
	('str2id6',      ['<string (spaces are ignored)> [str-]']),
	('hexdump',      ['<infile> [str]', 'cols [int=8]', 'line_nums [bool=True]']),
	('unhexdump',    ['<infile> [str]']),
	('hexreverse',   ['<hexadecimal string> [str-]']),
	('hexlify',      ['<string> [str-]']),
	('rand2file',    ['<outfile> [str]','<nbytes> [str]','threads [int=4]','silent [bool=False]']),

	('randwif',    []),
	('randpair',   []),
	('hex2wif',    ['<private key in hex format> [str-]']),
	('wif2hex',    ['<wif> [str-]']),
	('wif2addr',   ['<wif> [str-]']),
	('wif2segwit_pair',['<wif> [str-]']),
	('pubhash2addr', ['<coin address in hex format> [str-]']),
	('addr2hexaddr', ['<coin address> [str-]']),
	('privhex2addr', ['<private key in hex format> [str-]']),
	('privhex2pubhex',['<private key in hex format> [str-]']),
	('pubhex2addr',  ['<public key in hex format> [str-]']), # new
	('pubhex2redeem_script',['<public key in hex format> [str-]']), # new
	('wif2redeem_script', ['<private key in WIF format> [str-]']), # new

	('hex2mn',       ['<hexadecimal string> [str-]',"wordlist [str='electrum']"]),
	('mn2hex',       ['<mnemonic> [str-]', "wordlist [str='electrum']"]),
	('mn_rand128',   ["wordlist [str='electrum']"]),
	('mn_rand192',   ["wordlist [str='electrum']"]),
	('mn_rand256',   ["wordlist [str='electrum']"]),
	('mn_stats',     ["wordlist [str='electrum']"]),
	('mn_printlist', ["wordlist [str='electrum']"]),

	('gen_addr',     ['<{} ID> [str]'.format(pnm),"wallet [str='']"]),
	('gen_key',      ['<{} ID> [str]'.format(pnm),"wallet [str='']"]),

	('listaddress',['<{} address> [str]'.format(pnm),'minconf [int=1]','pager [bool=False]','showempty [bool=True]','showbtcaddr [bool=True]','show_age [bool=False]','show_days [bool=True]']),
	('listaddresses',["addrs [str='']",'minconf [int=1]','showempty [bool=False]','pager [bool=False]','showbtcaddrs [bool=True]','all_labels [bool=False]',"sort [str=''] (options: reverse, age)",'show_age [bool=False]','show_days [bool=True]']),
	('getbalance',   ['minconf [int=1]','quiet [bool=False]','pager [bool=False]']),
	('txview',       ['<{} TX file(s)> [str]'.format(pnm),'pager [bool=False]','terse [bool=False]',"sort [str='mtime'] (options: ctime, atime)",'MARGS']),
	('twview',       ["sort [str='age']",'reverse [bool=False]','show_days [bool=True]','show_mmid [bool=True]','minconf [int=1]','wide [bool=False]','pager [bool=False]']),

	('add_label',       ['<{} or coin address> [str]'.format(pnm),'<label> [str]']),
	('remove_label',    ['<{} or coin address> [str]'.format(pnm)]),
	('remove_address',  ['<{} or coin address> [str]'.format(pnm)]),
	('addrfile_chksum', ['<{} addr file> [str]'.format(pnm),"mmtype [str='']"]),
	('keyaddrfile_chksum', ['<{} addr file> [str]'.format(pnm),"mmtype [str='']"]),
	('passwdfile_chksum', ['<{} password file> [str]'.format(pnm)]),
	('find_incog_data', ['<file or device name> [str]','<Incog ID> [str]','keep_searching [bool=False]']),

	('encrypt',      ['<infile> [str]',"outfile [str='']","hash_preset [str='']"]),
	('decrypt',      ['<infile> [str]',"outfile [str='']","hash_preset [str='']"]),
	('bytespec',     ['<bytespec> [str]']),

	('keyaddrlist2monerowallets',['<{} XMR key-address file> [str]'.format(pnm),'blockheight [int=(current height)]',"addrs [str=''] (addr idx list or range)"]),
	('syncmonerowallets',        ['<{} XMR key-address file> [str]'.format(pnm),"addrs [str=''] (addr idx list or range)"]),
])

def _usage(cmd=None,exit_val=1):

	for v in cmd_data.values():
		if v and v[0][-2:] == '-]':
			v[0] = v[0][:-2] + ' or STDIN]'
		if 'MARGS' in v: v.remove('MARGS')

	if not cmd:
		Msg('Usage information for mmgen-tool commands:')
		for k,v in list(cmd_data.items()):
			Msg('  {:18} {}'.format(k,' '.join(v)))
		from mmgen.main_tool import stdin_msg
		Msg('\n  '+'\n  '.join(stdin_msg.split('\n')))
		sys.exit(0)

	if cmd in cmd_data:
		import re
		from mmgen.main_tool import cmd_help
		for line in cmd_help.split('\n'):
			if re.match(r'\s+{}\s+'.format(cmd),line):
				c,h = line.split('-',1)
				Msg('MMGEN-TOOL {}: {}'.format(c.strip().upper(),h.strip()))
		cd = cmd_data[cmd]
		msg('USAGE: {} {} {}'.format(g.prog_name,cmd,' '.join(cd)))
	else:
		die(1,"'{}': no such tool command".format(cmd))

	sys.exit(exit_val)

def _process_args(cmd,cmd_args):
	if 'MARGS' in cmd_data[cmd]:
		cmd_data[cmd].remove('MARGS')
		margs = True
	else:
		margs = False

	c_args = [[i.split(' [')[0],i.split(' [')[1][:-1]]
		for i in cmd_data[cmd] if '=' not in i]
	c_kwargs = dict([[
			i.split(' [')[0],
			[i.split(' [')[1].split('=')[0],i.split(' [')[1].split('=')[1][:-1]]
		] for i in cmd_data[cmd] if '=' in i])

	if not margs:
		u_args = [a for a in cmd_args[:len(c_args)]]

		if c_args and c_args[0][1][-1] == '-':
			c_args[0][1] = c_args[0][1][:-1] # [str-] -> [str]
			# If we're reading from a pipe, replace '-' with output of previous command
			if u_args and u_args[0] == '-':
				if not sys.stdin.isatty():
					u_args[0] = sys.stdin.read().strip()
					if not u_args[0]:
						die(2,'{}: ERROR: no output from previous command in pipe'.format(cmd))

		if not margs and len(u_args) < len(c_args):
			m1 = 'Command requires exactly {} non-keyword argument{}'
			msg(m1.format(len(c_args),suf(c_args,'s')))
			_usage(cmd)

	extra_args = len(cmd_args) - len(c_args)
	u_kwargs = {}
	if margs:
		t = [a.split('=') for a in cmd_args if '=' in a]
		tk = [a[0] for a in t]
		tk_bad = [a for a in tk if a not in c_kwargs]
		if set(tk_bad) != set(tk[:len(tk_bad)]):
			die(1,"'{}': illegal keyword argument".format(tk_bad[-1]))
		u_kwargs = dict(t[len(tk_bad):])
		u_args = cmd_args[:-len(u_kwargs) or None]
	elif extra_args > 0:
		u_kwargs = dict([a.split('=') for a in cmd_args[len(c_args):] if '=' in a])
		if len(u_kwargs) != extra_args:
			msg('Command requires exactly {} non-keyword argument{}'.format(len(c_args),suf(c_args,'s')))
			_usage(cmd)
		if len(u_kwargs) > len(c_kwargs):
			msg('Command requires exactly {} keyword argument{}'.format(len(c_kwargs),suf(c_kwargs,'s')))
			_usage(cmd)

	# mdie(c_args,c_kwargs,u_args,u_kwargs)

	for k in u_kwargs:
		if k not in c_kwargs:
			msg("'{}': invalid keyword argument".format(k))
			_usage(cmd)

	def conv_type(arg,arg_name,arg_type):
		if arg_type == 'bytes': pdie(arg,arg_name,arg_type)
		if arg_type == 'bool':
			if arg.lower() in ('true','yes','1','on'): arg = True
			elif arg.lower() in ('false','no','0','off'): arg = False
			else:
				msg("'{}': invalid boolean value for keyword argument".format(arg))
				_usage(cmd)
		try:
			return __builtins__[arg_type](arg)
		except:
			die(1,"'{}': Invalid argument for argument {} ('{}' required)".format(arg,arg_name,arg_type))

	if margs:
		args = [conv_type(u_args[i],c_args[0][0],c_args[0][1]) for i in range(len(u_args))]
	else:
		args = [conv_type(u_args[i],c_args[i][0],c_args[i][1]) for i in range(len(c_args))]
	kwargs = dict([(k,conv_type(u_kwargs[k],k,c_kwargs[k][0])) for k in u_kwargs])

	return args,kwargs

def _get_result(ret): # returns a string or string subclass
	if issubclass(type(ret),str):
		return ret
	elif type(ret) == tuple:
		return '\n'.join([r.decode() if issubclass(type(r),bytes) else r for r in ret])
	elif issubclass(type(ret),bytes):
		try: return ret.decode()
		except: return repr(ret)
	elif ret == True:
		return ''
	elif ret in (False,None):
		ydie(1,"tool command returned '{}'".format(ret))
	else:
		ydie(1,"tool.py: can't handle return value of type '{}'".format(type(ret).__name__))

def _print_result(ret,pager):
	if issubclass(type(ret),str):
		do_pager(ret) if pager else Msg(ret)
	elif type(ret) == tuple:
		o = '\n'.join([r.decode() if issubclass(type(r),bytes) else r for r in ret])
		do_pager(o) if pager else Msg(o)
	elif issubclass(type(ret),bytes):
		try:
			o = ret.decode()
			do_pager(o) if pager else Msg(o)
		except: os.write(1,ret)
	elif ret == True:
		pass
	elif ret in (False,None):
		ydie(1,"tool command returned '{}'".format(ret))
	else:
		ydie(1,"tool.py: can't handle return value of type '{}'".format(type(ret).__name__))

from mmgen.obj import MMGenAddrType
at = MMGenAddrType((hasattr(opt,'type') and opt.type) or g.proto.dfl_mmtype)
kg = KeyGenerator(at)
ag = AddrGenerator(at)
wordlists = 'electrum','tirosh'
dfl_wl_id = 'electrum'

class MMGenToolCmd(object):

	def help(self,cmd=None):
		_usage(cmd,exit_val=0)

	def usage(self,cmd=None):
		_usage(cmd,exit_val=0)

	def hexdump(self,infile,cols=8,line_nums=True):
		return pretty_hexdump(
				get_data_from_file(infile,dash=True,silent=True,binary=True),
					cols=cols,line_nums=line_nums)

	def unhexdump(self,infile):
		if g.platform == 'win':
			import msvcrt
			msvcrt.setmode(sys.stdout.fileno(),os.O_BINARY)
		hexdata = get_data_from_file(infile,dash=True,silent=True)
		return decode_pretty_hexdump(hexdata)

	def b58randenc(self):
		r = get_random(32)
		return baseconv.b58encode(r,pad=True)

	def randhex(self,nbytes='32'):
		return binascii.hexlify(get_random(int(nbytes)))

	def randwif(self):
		return PrivKey(get_random(32),pubkey_type=at.pubkey_type,compressed=at.compressed).wif

	def randpair(self):
		privhex = PrivKey(get_random(32),pubkey_type=at.pubkey_type,compressed=at.compressed)
		addr = ag.to_addr(kg.to_pubhex(privhex))
		return (privhex.wif,addr)

	def wif2addr(self,wif):
		privhex = PrivKey(wif=wif)
		addr = ag.to_addr(kg.to_pubhex(privhex))
		return addr

	def wif2segwit_pair(self,wif):
		pubhex = kg.to_pubhex(PrivKey(wif=wif))
		addr = ag.to_addr(pubhex)
		rs = ag.to_segwit_redeem_script(pubhex)
		return (rs,addr)

	def pubhash2addr(self,pubhash):
		if opt.type == 'bech32':
			return g.proto.pubhash2bech32addr(pubhash.encode())
		else:
			return g.proto.pubhash2addr(pubhash.encode(),at.addr_fmt=='p2sh')

	def addr2hexaddr(self,addr):
		return g.proto.verify_addr(addr,CoinAddr.hex_width,return_dict=True)['hex']

	def hash160(self,pubkeyhex):
		return hash160(pubkeyhex)

	def pubhex2addr(self,pubkeyhex):
		return self.pubhash2addr(hash160(pubkeyhex.encode()).decode())

	def wif2hex(self,wif):
		return PrivKey(wif=wif)

	def hex2wif(self,hexpriv):
		return g.proto.hex2wif(hexpriv.encode(),pubkey_type=at.pubkey_type,compressed=at.compressed)

	def privhex2addr(self,privhex,output_pubhex=False):
		pk = PrivKey(binascii.unhexlify(privhex),compressed=at.compressed,pubkey_type=at.pubkey_type)
		ph = kg.to_pubhex(pk)
		return ph if output_pubhex else ag.to_addr(ph)

	def privhex2pubhex(self,privhex): # new
		return self.privhex2addr(privhex,output_pubhex=True)

	def pubhex2redeem_script(self,pubhex): # new
		return g.proto.pubhex2redeem_script(pubhex)

	def wif2redeem_script(self,wif): # new
		privhex = PrivKey(wif=wif)
		return ag.to_segwit_redeem_script(kg.to_pubhex(privhex))

	def do_random_mn(self,nbytes,wordlist):
		hexrand = binascii.hexlify(get_random(nbytes))
		Vmsg('Seed: {}'.format(hexrand))
		for wl_id in ([wordlist],wordlists)[wordlist=='all']:
			if wordlist == 'all': # TODO
				Msg('{} mnemonic:'.format(capfirst(wl_id)))
			mn = baseconv.fromhex(hexrand,wl_id)
			return ' '.join(mn)

	def mn_rand128(self,wordlist=dfl_wl_id):
		return self.do_random_mn(16,wordlist)

	def mn_rand192(self,wordlist=dfl_wl_id):
		return self.do_random_mn(24,wordlist)

	def mn_rand256(self,wordlist=dfl_wl_id):
		return self.do_random_mn(32,wordlist)

	def hex2mn(self,s,wordlist=dfl_wl_id):
		return ' '.join(baseconv.fromhex(s.encode(),wordlist))

	def mn2hex(self,s,wordlist=dfl_wl_id):
		return baseconv.tohex(s.split(),wordlist)

	def strtob58(self,s,pad=None):
		return baseconv.fromhex(binascii.hexlify(s.encode()),'b58',pad,tostr=True)

	def hextob58(self,s,pad=None):
		return baseconv.fromhex(s.encode(),'b58',pad,tostr=True)

	def hextob58chk(self,s):
		from mmgen.protocol import _b58chk_encode
		return _b58chk_encode(s.encode())

	def hextob32(self,s,pad=None):
		return baseconv.fromhex(s.encode(),'b32',pad,tostr=True)

	def b58tostr(self,s):
		return binascii.unhexlify(baseconv.tohex(s,'b58'))

	def b58tohex(self,s,pad=None):
		return baseconv.tohex(s,'b58',pad)

	def b58chktohex(self,s):
		from mmgen.protocol import _b58chk_decode
		return _b58chk_decode(s)

	def b32tohex(self,s,pad=None):
		return baseconv.tohex(s.upper(),'b32',pad)

	def mn_stats(self,wordlist=dfl_wl_id):
		wordlist in baseconv.digits or die(1,"'{}': not a valid wordlist".format(wordlist))
		baseconv.check_wordlist(wordlist)
		return True

	def mn_printlist(self,wordlist=dfl_wl_id):
		wordlist in baseconv.digits or die(1,"'{}': not a valid wordlist".format(wordlist))
		return '\n'.join(baseconv.digits[wordlist])

	def id8(self,infile):
		return make_chksum_8(
			get_data_from_file(infile,dash=True,silent=True,binary=True))

	def id6(self,infile):
		return make_chksum_6(
			get_data_from_file(infile,dash=True,silent=True,binary=True))

	def str2id6(self,s): # retain ignoring of space for backwards compat
		return make_chksum_6(''.join(s.split()))

	def addrfile_chksum(self,infile,mmtype=''):
		from mmgen.addr import AddrList
		mmtype = None if not mmtype else MMGenAddrType(mmtype)
		return AddrList(infile,mmtype=mmtype).chksum

	def keyaddrfile_chksum(self,infile,mmtype=''):
		from mmgen.addr import KeyAddrList
		mmtype = None if not mmtype else MMGenAddrType(mmtype)
		return KeyAddrList(infile,mmtype=mmtype).chksum

	def passwdfile_chksum(self,infile):
		from mmgen.addr import PasswordList
		return PasswordList(infile=infile).chksum

	def hexreverse(self,s):
		return binascii.hexlify(binascii.unhexlify(s.strip())[::-1])

	def hexlify(self,s):
		return binascii.hexlify(s.encode())

	def hash256(self,s,file_input=False,hex_input=False):
		from hashlib import sha256
		if file_input:  b = get_data_from_file(s,binary=True)
		elif hex_input: b = decode_pretty_hexdump(s)
		else:           b = s
		return sha256(sha256(b.encode()).digest()).hexdigest()

	def encrypt(self,infile,outfile='',hash_preset=''):
		data = get_data_from_file(infile,'data for encryption',binary=True)
		enc_d = mmgen_encrypt(data,'user data',hash_preset)
		if not outfile:
			outfile = '{}.{}'.format(os.path.basename(infile),g.mmenc_ext)
		write_data_to_file(outfile,enc_d,'encrypted data',binary=True)
		return True

	def decrypt(self,infile,outfile='',hash_preset=''):
		enc_d = get_data_from_file(infile,'encrypted data',binary=True)
		while True:
			dec_d = mmgen_decrypt(enc_d,'user data',hash_preset)
			if dec_d: break
			msg('Trying again...')
		if not outfile:
			o = os.path.basename(infile)
			outfile = remove_extension(o,g.mmenc_ext)
			if outfile == o: outfile += '.dec'
		write_data_to_file(outfile,dec_d,'decrypted data',binary=True)
		return True

	def find_incog_data(self,filename,iv_id,keep_searching=False):
		ivsize,bsize,mod = g.aesctr_iv_len,4096,4096*8
		n,carry = 0,b' '*ivsize
		flgs = os.O_RDONLY|os.O_BINARY if g.platform == 'win' else os.O_RDONLY
		f = os.open(filename,flgs)
		for ch in iv_id:
			if ch not in '0123456789ABCDEF':
				die(2,"'{}': invalid Incog ID".format(iv_id))
		while True:
			d = os.read(f,bsize)
			if not d: break
			d = carry + d
			for i in range(bsize):
				if sha256(d[i:i+ivsize]).hexdigest()[:8].upper() == iv_id:
					if n+i < ivsize: continue
					msg('\rIncog data for ID {} found at offset {}'.format(iv_id,n+i-ivsize))
					if not keep_searching: sys.exit(0)
			carry = d[len(d)-ivsize:]
			n += bsize
			if not n % mod:
				msg_r('\rSearched: {} bytes'.format(n))

		msg('')
		os.close(f)
		return True

	def rand2file(self,outfile,nbytes,threads=4,silent=False):
		nbytes = parse_nbytes(nbytes)
		from Crypto import Random
		rh = Random.new()
		from queue import Queue
		from threading import Thread
		bsize = 2**20
		roll = bsize * 4
		if opt.outdir: outfile = make_full_path(opt.outdir,outfile)
		f = open(outfile,'wb')

		from Crypto.Cipher import AES
		from Crypto.Util import Counter

		key = get_random(32)

		def encrypt_worker(wid):
			while True:
				i,d = q1.get()
				c = AES.new(key,AES.MODE_CTR,counter=Counter.new(g.aesctr_iv_len*8,initial_value=i))
				enc_data = c.encrypt(d)
				q2.put(enc_data)
				q1.task_done()

		def output_worker():
			while True:
				data = q2.get()
				f.write(data)
				q2.task_done()

		q1 = Queue()
		for i in range(max(1,threads-2)):
			t = Thread(target=encrypt_worker,args=(i,))
			t.daemon = True
			t.start()

		q2 = Queue()
		t = Thread(target=output_worker)
		t.daemon = True
		t.start()

		i = 1; rbytes = nbytes
		while rbytes > 0:
			d = rh.read(min(bsize,rbytes))
			q1.put((i,d))
			rbytes -= bsize
			i += 1
			if not (bsize*i) % roll:
				msg_r('\rRead: {} bytes'.format(bsize*i))

		if not silent:
			msg('\rRead: {} bytes'.format(nbytes))
			qmsg("\r{} bytes of random data written to file '{}'".format(nbytes,outfile))
		q1.join()
		q2.join()
		f.close()
		return True

	def bytespec(self,s):
		return str(parse_nbytes(s))

	def keyaddrlist2monerowallets(self,infile,blockheight=None,addrs=None):
		return self.monero_wallet_ops(infile=infile,op='create',blockheight=blockheight,addrs=addrs)

	def syncmonerowallets(self,infile,addrs=None):
		return self.monero_wallet_ops(infile=infile,op='sync',addrs=addrs)

	def monero_wallet_ops(self,infile,op,blockheight=None,addrs=None):

		def run_cmd(cmd):
			import subprocess as sp
			p = sp.Popen(cmd,stdin=sp.PIPE,stdout=sp.PIPE,stderr=sp.PIPE)
			return p

		def test_rpc():
			p = run_cmd(['monero-wallet-cli','--version'])
			if not b'Monero' in p.stdout.read():
				die(1,"Unable to run 'monero-wallet-cli'!")
			p = run_cmd(['monerod','status'])
			import re
			m = re.search(r'Height: (\d+)/\d+ ',p.stdout.read().decode())
			if not m:
				die(1,'Unable to connect to monerod!')
			return int(m.group(1))

		def my_expect(p,m,s,regex=False):
			if m: msg_r('  {}...'.format(m))
			ret = (p.expect_exact,p.expect)[regex](s)
			vmsg("\nexpect: '{}' => {}".format(s,ret))
			if not (ret == 0 or (type(s) == list and ret in (0,1))):
				die(2,"Expect failed: '{}' (return value: {})".format(s,ret))
			if m: msg('OK')
			return ret

		def my_sendline(p,m,s,usr_ret):
			if m: msg_r('  {}...'.format(m))
			ret = p.sendline(s)
			if ret != usr_ret:
				die(2,"Unable to send line '{}' (return value {})".format(s,ret))
			if m: msg('OK')
			vmsg("sendline: '{}' => {}".format(s,ret))

		def create(n,d,fn):
			try: os.stat(fn)
			except: pass
			else: die(1,"Wallet '{}' already exists!".format(fn))
			p = pexpect.spawn('monero-wallet-cli --generate-from-spend-key {}'.format(fn))
			if g.debug: p.logfile = sys.stdout
			my_expect(p,'Awaiting initial prompt','Secret spend key: ')
			my_sendline(p,'',d.sec.decode(),65)
			my_expect(p,'','Enter.* new.* password.*: ',regex=True)
			my_sendline(p,'Sending password',d.wallet_passwd,33)
			my_expect(p,'','Confirm password: ')
			my_sendline(p,'Sending password again',d.wallet_passwd,33)
			my_expect(p,'','of your choice: ')
			my_sendline(p,'','1',2)
			my_expect(p,'monerod generating wallet','Generated new wallet: ')
			my_expect(p,'','\n')
			if d.addr not in p.before.decode():
				die(3,'Addresses do not match!\n  MMGen: {}\n Monero: {}'.format(d.addr,p.before.decode()))
			my_expect(p,'','View key: ')
			my_expect(p,'','\n')
			if d.viewkey not in p.before.decode():
				die(3,'View keys do not match!\n  MMGen: {}\n Monero: {}'.format(d.viewkey,p.before.decode()))
			my_expect(p,'','(YYYY-MM-DD): ')
			h = str(blockheight or cur_height-1)
			my_sendline(p,'',h,len(h)+1)
			ret = my_expect(p,'',['Starting refresh','Still apply restore height?  (Y/Yes/N/No): '])
			if ret == 1:
				my_sendline(p,'','Y',2)
				m = '  Warning: {}: blockheight argument is higher than current blockheight'
				ymsg(m.format(blockheight))
			elif blockheight != None:
				p.logfile = sys.stderr
			my_expect(p,'Syncing wallet','\[wallet.*$',regex=True)
			p.logfile = None
			my_sendline(p,'Exiting','exit',5)
			p.read()

		def sync(n,d,fn):
			try: os.stat(fn)
			except: die(1,"Wallet '{}' does not exist!".format(fn))
			p = pexpect.spawn('monero-wallet-cli --wallet-file={}'.format(fn))
			if g.debug: p.logfile = sys.stdout
			my_expect(p,'Awaiting password prompt','Wallet password: ')
			my_sendline(p,'Sending password',d.wallet_passwd,33)

			msg('  Starting refresh...')
			height = None
			while True:
				ret = p.expect([r' / .*',r'\[wallet.*:.*'])
				if ret == 0: # TODO: coverage
					height = p.after
					msg_r('\r  Block {}{}'.format(p.before.split()[-1],height))
				elif ret == 1:
					if height:
						height = height.split()[-1]
						msg('\r  Block {h} / {h}'.format(h=height))
					else:
						msg('  Wallet in sync')
					b = [l for l in p.before.decode().splitlines() if len(l) > 7 and l[:8] == 'Balance:'][0].split()
					msg('  Balance: {} Unlocked balance: {}'.format(b[1],b[4]))
					from mmgen.obj import XMRAmt
					bals[fn] = ( XMRAmt(b[1][:-1]), XMRAmt(b[4]) )
					my_sendline(p,'Exiting','exit',5)
					p.read()
					break
				else:
					die(2,"\nExpect failed: (return value: {})".format(ret))

		def process_wallets():
			m =   { 'create': ('Creat','Generat',create,False),
					'sync':   ('Sync', 'Sync',   sync,  True) }
			opt.accept_defaults = opt.accept_defaults or m[op][3]
			from mmgen.protocol import init_coin
			init_coin('xmr')
			from mmgen.addr import AddrList
			al = KeyAddrList(infile)
			data = [d for d in al.data if addrs == None or d.idx in AddrIdxList(addrs)]
			dl = len(data)
			assert dl,"No addresses in addrfile within range '{}'".format(addrs)
			gmsg('\n{}ing {} wallet{}'.format(m[op][0],dl,suf(dl)))
			for n,d in enumerate(data): # [d.sec,d.wallet_passwd,d.viewkey,d.addr]
				fn = os.path.join(
					opt.outdir or '','{}-{}-MoneroWallet{}'.format(
						al.al_id.sid,
						d.idx,
						'-α' if g.debug_utf8 else ''))
				gmsg('\n{}ing wallet {}/{} ({})'.format(m[op][1],n+1,dl,fn))
				m[op][2](n,d,fn)
			gmsg('\n{} wallet{} {}ed'.format(dl,suf(dl),m[op][0].lower()))
			if op == 'sync':
				col1_w = max(map(len,bals)) + 1
				fs = '{:%s} {} {}' % col1_w
				msg('\n'+fs.format('Wallet','Balance           ','Unlocked Balance  '))
				from mmgen.obj import XMRAmt
				tbals = [XMRAmt('0'),XMRAmt('0')]
				for bal in bals:
					for i in (0,1): tbals[i] += bals[bal][i]
					msg(fs.format(bal+':',*[XMRAmt(b).fmt(fs='5.12',color=True) for b in bals[bal]]))
				msg(fs.format('-'*col1_w,'-'*18,'-'*18))
				msg(fs.format('TOTAL:',*[XMRAmt(b).fmt(fs='5.12',color=True) for b in tbals]))

		os.environ['LANG'] = 'C'
		import pexpect
		if blockheight != None and int(blockheight) < 0:
			blockheight = 0 # TODO: non-zero coverage
		cur_height = test_rpc()
		bals = OrderedDict() # locked,unlocked

		try:
			process_wallets()
		except KeyboardInterrupt:
			rdie(1,'\nUser interrupt\n')
		except EOFError:
			rdie(2,'\nEnd of file\n')
		except Exception as e:
			try:
				die(1,'Error: {}'.format(e.args[0]))
			except:
				rdie(1,'Error: {!r}'.format(e.args[0]))

		return True

	# ================ RPC commands ================== #

	def gen_addr(self,addr,wallet='',target='addr'):
		addr = MMGenID(addr)
		sf = get_seed_file([wallet] if wallet else [],1)
		opt.quiet = True
		from mmgen.seed import SeedSource
		ss = SeedSource(sf)
		if ss.seed.sid != addr.sid:
			m = 'Seed ID of requested address ({}) does not match wallet ({})'
			die(1,m.format(addr.sid,ss.seed.sid))
		al = AddrList(seed=ss.seed,addr_idxs=AddrIdxList(str(addr.idx)),mmtype=addr.mmtype)
		d = al.data[0]
		ret = d.sec.wif if target=='wif' else d.addr
		return ret

	def gen_key(self,addr,wallet=''):
		return self.gen_addr(addr,wallet,target='wif')

	def listaddress(self,addr,minconf=1,pager=False,showempty=True,showbtcaddr=True,show_age=False,show_days=None):
		return self.listaddresses(addrs=addr,minconf=minconf,pager=pager,
				showempty=showempty,showbtcaddrs=showbtcaddr,show_age=show_age,show_days=show_days)

	def listaddresses(self,addrs='',minconf=1,
		showempty=False,pager=False,showbtcaddrs=True,all_labels=False,sort=None,show_age=False,show_days=None):

		if show_days == None: show_days = False # user-set show_days triggers show_age
		else: show_age = True

		if sort:
			sort = set(sort.split(','))
			sort_params = set(['reverse','age'])
			if not sort.issubset(sort_params):
				die(1,"The sort option takes the following parameters: '{}'".format("','".join(sort_params)))

		usr_addr_list = []
		if addrs:
			a = addrs.rsplit(':',1)
			if len(a) != 2:
				m = "'{}': invalid address list argument (must be in form <seed ID>:[<type>:]<idx list>)"
				die(1,m.format(addrs))
			usr_addr_list = [MMGenID('{}:{}'.format(a[0],i)) for i in AddrIdxList(a[1])]

		from mmgen.tw import TwAddrList
		al = TwAddrList(usr_addr_list,minconf,showempty,showbtcaddrs,all_labels)
		if not al:
			die(0,('No tracked addresses with balances!','No tracked addresses!')[showempty])
		return al.format(showbtcaddrs,sort,show_age,show_days)

	def getbalance(self,minconf=1,quiet=False,pager=False):
		from mmgen.tw import TwGetBalance
		return TwGetBalance(minconf,quiet).format()

	def txview(self,*infiles,**kwargs):
		from mmgen.filename import MMGenFileList
		terse = 'terse' in kwargs and kwargs['terse']
		sort_key = kwargs['sort'] if 'sort' in kwargs else 'mtime'
		flist = MMGenFileList(infiles,ftype=MMGenTX)
		flist.sort_by_age(key=sort_key) # in-place sort
		from mmgen.term import get_terminal_size
		sep = '—'*77+'\n'
		return sep.join([MMGenTX(fn).format_view(terse=terse) for fn in flist.names()]).rstrip()

	def twview(self,pager=False,reverse=False,wide=False,minconf=1,sort='age',show_days=True,show_mmid=True):
		rpc_init()
		from mmgen.tw import TwUnspentOutputs
		tw = TwUnspentOutputs(minconf=minconf)
		tw.do_sort(sort,reverse=reverse)
		tw.show_days = show_days
		tw.show_mmid = show_mmid
		return tw.format_for_printing(color=True) if wide else tw.format_for_display()

	def add_label(self,mmaddr_or_coin_addr,label):
		rpc_init()
		from mmgen.tw import TrackingWallet
		TrackingWallet(mode='w').add_label(mmaddr_or_coin_addr,label,on_fail='raise')
		return True

	def remove_label(self,mmaddr_or_coin_addr):
		self.add_label(mmaddr_or_coin_addr,'')
		return True

	def remove_address(self,mmaddr_or_coin_addr):
		from mmgen.tw import TrackingWallet
		tw = TrackingWallet(mode='w')
		ret = tw.remove_address(mmaddr_or_coin_addr) # returns None on failure
		if ret:
			msg("Address '{}' deleted from tracking wallet".format(ret))
		return ret
