#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2017 Philemon <mmgen-py@yandex.com>
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

from mmgen.protocol import hash160
from mmgen.common import *
from mmgen.crypto import *
from mmgen.tx import *
from mmgen.addr import *

pnm = g.proj_name

from collections import OrderedDict
cmd_data = OrderedDict([
	('Help',         ['<tool command> [str]']),
	('Usage',        ['<tool command> [str]']),
	('Strtob58',     ['<string> [str-]','pad [int=0]']),
	('B58tostr',     ['<b58 number> [str-]']),
	('Hextob58',     ['<hex number> [str-]','pad [int=0]']),
	('B58tohex',     ['<b58 number> [str-]','pad [int=0]']),
	('B58randenc',   []),
	('B32tohex',     ['<b32 num> [str-]','pad [int=0]']),
	('Hextob32',     ['<hex num> [str-]','pad [int=0]']),
	('Randhex',      ['nbytes [int=32]']),
	('Id8',          ['<infile> [str]']),
	('Id6',          ['<infile> [str]']),
	('Hash160',      ['<hexadecimal string> [str-]']),
	('Hash256',      ['<str, hexstr or filename> [str]', # TODO handle stdin
							'hex_input [bool=False]','file_input [bool=False]']),
	('Str2id6',      ['<string (spaces are ignored)> [str-]']),
	('Hexdump',      ['<infile> [str]', 'cols [int=8]', 'line_nums [bool=True]']),
	('Unhexdump',    ['<infile> [str]']),
	('Hexreverse',   ['<hexadecimal string> [str-]']),
	('Hexlify',      ['<string> [str-]']),
	('Rand2file',    ['<outfile> [str]','<nbytes> [str]','threads [int=4]','silent [bool=False]']),

	('Randwif',    ['compressed [bool=False]']),
	('Randpair',   ['compressed [bool=False]','segwit [bool=False]']),
	('Hex2wif',    ['<private key in hex format> [str-]','compressed [bool=False]']),
	('Wif2hex',    ['<wif> [str-]']),
	('Wif2addr',   ['<wif> [str-]','segwit [bool=False]']),
	('Wif2segwit_pair',['<wif> [str-]']),
	('Hexaddr2addr', ['<coin address in hex format> [str-]','p2sh [bool=False]']),
	('Addr2hexaddr', ['<coin address> [str-]']),
	('Privhex2addr', ['<private key in hex format> [str-]','compressed [bool=False]','segwit [bool=False]']),
	('Privhex2pubhex',['<private key in hex format> [str-]','compressed [bool=False]']),
	('Pubhex2addr',  ['<public key in hex format> [str-]','p2sh [bool=False]']), # new
	('Pubhex2redeem_script',['<public key in hex format> [str-]']), # new
	('Wif2redeem_script', ['<private key in WIF format> [str-]']), # new

	('Hex2mn',       ['<hexadecimal string> [str-]',"wordlist [str='electrum']"]),
	('Mn2hex',       ['<mnemonic> [str-]', "wordlist [str='electrum']"]),
	('Mn_rand128',   ["wordlist [str='electrum']"]),
	('Mn_rand192',   ["wordlist [str='electrum']"]),
	('Mn_rand256',   ["wordlist [str='electrum']"]),
	('Mn_stats',     ["wordlist [str='electrum']"]),
	('Mn_printlist', ["wordlist [str='electrum']"]),

	('Listaddress',['<{} address> [str]'.format(pnm),'minconf [int=1]','pager [bool=False]','showempty [bool=True]''showbtcaddr [bool=True]']),
	('Listaddresses',["addrs [str='']",'minconf [int=1]','showempty [bool=False]','pager [bool=False]','showbtcaddrs [bool=True]','all_labels [bool=False]',"sort [str=''] (options: reverse, age)"]),
	('Getbalance',   ['minconf [int=1]','quiet [bool=False]']),
	('Txview',       ['<{} TX file(s)> [str]'.format(pnm),'pager [bool=False]','terse [bool=False]',"sort [str='mtime'] (options: ctime, atime)",'MARGS']),
	('Twview',       ["sort [str='age']",'reverse [bool=False]','show_days [bool=True]','show_mmid [bool=True]','minconf [int=1]','wide [bool=False]','pager [bool=False]']),

	('Add_label',       ['<{} address> [str]'.format(pnm),'<label> [str]']),
	('Remove_label',    ['<{} address> [str]'.format(pnm)]),
	('Addrfile_chksum', ['<{} addr file> [str]'.format(pnm)]),
	('Keyaddrfile_chksum', ['<{} addr file> [str]'.format(pnm)]),
	('Passwdfile_chksum', ['<{} password file> [str]'.format(pnm)]),
	('Find_incog_data', ['<file or device name> [str]','<Incog ID> [str]','keep_searching [bool=False]']),

	('Encrypt',      ['<infile> [str]',"outfile [str='']","hash_preset [str='']"]),
	('Decrypt',      ['<infile> [str]',"outfile [str='']","hash_preset [str='']"]),
	('Bytespec',     ['<bytespec> [str]']),
	('Regtest_setup',[]),
])

def usage(command):

	for v in cmd_data.values():
		if v and v[0][-2:] == '-]':
			v[0] = v[0][:-2] + ' or STDIN]'
		if 'MARGS' in v: v.remove('MARGS')

	if not command:
		Msg('Usage information for mmgen-tool commands:')
		for k,v in cmd_data.items():
			Msg('  {:18} {}'.format(k.lower(),' '.join(v)))
		from mmgen.main_tool import stdin_msg
		Msg('\n  '+'\n  '.join(stdin_msg.split('\n')))
		sys.exit(0)

	Command = command.capitalize()
	if Command in cmd_data:
		import re
		from mmgen.main_tool import cmd_help
		for line in cmd_help.split('\n'):
			if re.match(r'\s+{}\s+'.format(command),line):
				c,h = line.split('-',1)
				Msg('MMGEN-TOOL {}: {}'.format(c.strip().upper(),h.strip()))
		cd = cmd_data[Command]
		msg('USAGE: %s %s %s' % (g.prog_name, command, ' '.join(cd)))
	else:
		msg("'%s': no such tool command" % command)
	sys.exit(1)

Help = usage

def process_args(command,cmd_args):
	if 'MARGS' in cmd_data[command]:
		cmd_data[command].remove('MARGS')
		margs = True
	else:
		margs = False

	c_args = [[i.split(' [')[0],i.split(' [')[1][:-1]]
		for i in cmd_data[command] if '=' not in i]
	c_kwargs = dict([[
			i.split(' [')[0],
			[i.split(' [')[1].split('=')[0], i.split(' [')[1].split('=')[1][:-1]]
		] for i in cmd_data[command] if '=' in i])

	if not margs:
		u_args = [a for a in cmd_args[:len(c_args)]]

		if c_args and c_args[0][1][-1] == '-':
			c_args[0][1] = c_args[0][1][:-1] # [str-] -> [str]
			# If we're reading from a pipe, replace '-' with output of previous command
			if u_args and u_args[0] == '-':
				if not sys.stdin.isatty():
					u_args[0] = sys.stdin.read().strip()
					if not u_args[0]:
						die(2,'{}: ERROR: no output from previous command in pipe'.format(command.lower()))

		if not margs and len(u_args) < len(c_args):
			m1 = 'Command requires exactly %s non-keyword argument%s'
			msg(m1 % (len(c_args),suf(c_args,'s')))
			usage(command)

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
			msg('Command requires exactly %s non-keyword argument%s'
				% (len(c_args),suf(c_args,'s')))
			usage(command)
		if len(u_kwargs) > len(c_kwargs):
			msg('Command requires exactly %s keyword argument%s'
				% (len(c_kwargs),suf(c_kwargs,'s')))
			usage(command)

#	mdie(c_args,c_kwargs,u_args,u_kwargs)

	for k in u_kwargs:
		if k not in c_kwargs:
			msg("'%s': invalid keyword argument" % k)
			usage(command)

	def conv_type(arg,arg_name,arg_type):
		if arg_type == 'str': arg_type = 'unicode'
		if arg_type == 'bool':
			if arg.lower() in ('true','yes','1','on'): arg = True
			elif arg.lower() in ('false','no','0','off'): arg = False
			else:
				msg("'%s': invalid boolean value for keyword argument" % arg)
				usage(command)
		try:
			return __builtins__[arg_type](arg)
		except:
			die(1,"'%s': Invalid argument for argument %s ('%s' required)" % \
				(arg, arg_name, arg_type))

	if margs:
		args = [conv_type(u_args[i],c_args[0][0],c_args[0][1]) for i in range(len(u_args))]
	else:
		args = [conv_type(u_args[i],c_args[i][0],c_args[i][1]) for i in range(len(c_args))]
	kwargs = dict([(k,conv_type(u_kwargs[k],k,c_kwargs[k][0])) for k in u_kwargs])

	return args,kwargs

# Individual cmd_data

def are_equal(a,b,dtype=''):
	if dtype == 'str': return a.lstrip('\0') == b.lstrip('\0')
	if dtype == 'hex': return a.lstrip('0') == b.lstrip('0')
	if dtype == 'b58': return a.lstrip('1') == b.lstrip('1')
	else:              return a == b

def print_convert_results(indata,enc,dec,dtype):
	error = (True,False)[are_equal(indata,dec,dtype)]
	if error or opt.verbose:
		Msg('Input:         %s' % repr(indata))
		Msg('Encoded data:  %s' % repr(enc))
		Msg('Recoded data:  %s' % repr(dec))
	else: Msg(enc)
	if error:
		die(3,"Error! Recoded data doesn't match input!")

kg = KeyGenerator()

def Hexdump(infile, cols=8, line_nums=True):
	Msg(pretty_hexdump(
			get_data_from_file(infile,dash=True,silent=True,binary=True),
				cols=cols,line_nums=line_nums))

def Unhexdump(infile):
	if g.platform == 'win':
		import msvcrt
		msvcrt.setmode(sys.stdout.fileno(),os.O_BINARY)
	sys.stdout.write(decode_pretty_hexdump(
			get_data_from_file(infile,dash=True,silent=True)))

def B58randenc():
	r = get_random(32)
	enc = baseconv.b58encode(r,pad=True)
	dec = baseconv.b58decode(enc,pad=True)
	print_convert_results(r,enc,dec,'str')

def Randhex(nbytes='32'):
	Msg(binascii.hexlify(get_random(int(nbytes))))

def Randwif(compressed=False):
	Msg(PrivKey(get_random(32),compressed).wif)

def Randpair(compressed=False,segwit=False):
	if segwit: compressed = True
	ag = AddrGenerator(('p2pkh','segwit')[bool(segwit)])
	privhex = PrivKey(get_random(32),compressed)
	addr = ag.to_addr(kg.to_pubhex(privhex))
	Vmsg('Key (hex):  %s' % privhex)
	Vmsg_r('Key (WIF):  '); Msg(privhex.wif)
	Vmsg_r('Addr:       '); Msg(addr)

def Wif2addr(wif,segwit=False):
	privhex = PrivKey(wif=wif)
	if segwit and not privhex.compressed:
		die(2,'Segwit addresses must use compressed public keys')
	ag = AddrGenerator(('p2pkh','segwit')[bool(segwit)])
	addr = ag.to_addr(kg.to_pubhex(privhex))
	Vmsg_r('Addr: '); Msg(addr)

def Wif2segwit_pair(wif):
	privhex = PrivKey(wif=wif)
	if not privhex.compressed:
		die(1,'Segwit address cannot be generated from uncompressed WIF')
	ag = AddrGenerator('segwit')
	pubhex = kg.to_pubhex(privhex)
	addr = ag.to_addr(pubhex)
	rs = ag.to_segwit_redeem_script(pubhex)
	Msg('{}\n{}'.format(rs,addr))

def Hexaddr2addr(hexaddr,p2sh=False):          Msg(g.proto.hexaddr2addr(hexaddr,p2sh=p2sh))
def Addr2hexaddr(addr):                        Msg(g.proto.verify_addr(addr,return_dict=True)['hex'])
def Hash160(pubkeyhex):                        Msg(hash160(pubkeyhex))
def Pubhex2addr(pubkeyhex,p2sh=False):         Msg(g.proto.hexaddr2addr(hash160(pubkeyhex),p2sh=p2sh))
def Wif2hex(wif):                              Msg(wif2hex(wif))
def Hex2wif(hexpriv,compressed=False):
	Msg(g.proto.hex2wif(hexpriv,compressed))
def Privhex2addr(privhex,compressed=False,segwit=False,output_pubhex=False):
	if segwit and not compressed:
		die(1,'Segwit address can be generated only from a compressed pubkey')
	pk = PrivKey(binascii.unhexlify(privhex),compressed=compressed)
	ph = kg.to_pubhex(pk)
	ag = AddrGenerator(('p2pkh','segwit')[bool(segwit)])
	Msg(ph if output_pubhex else ag.to_addr(ph))
def Privhex2pubhex(privhex,compressed=False): # new
	return Privhex2addr(privhex,compressed=compressed,output_pubhex=True)
def Pubhex2redeem_script(pubhex): # new
	Msg(g.proto.pubhex2redeem_script(pubhex))
def Wif2redeem_script(wif): # new
	privhex = PrivKey(wif=wif)
	if not privhex.compressed:
		die(1,'Segwit redeem script cannot be generated from uncompressed WIF')
	ag = AddrGenerator('segwit')
	Msg(ag.to_segwit_redeem_script(kg.to_pubhex(privhex)))

def wif2hex(wif): # wrapper
	ret = PrivKey(wif=wif)
	return ret or die(1,'{}: Invalid WIF'.format(wif))

wordlists = 'electrum','tirosh'
dfl_wl_id = 'electrum'

def do_random_mn(nbytes,wordlist):
	hexrand = binascii.hexlify(get_random(nbytes))
	Vmsg('Seed: %s' % hexrand)
	for wl_id in ([wordlist],wordlists)[wordlist=='all']:
		if wordlist == 'all':
			Msg('%s mnemonic:' % (capfirst(wl_id)))
		mn = baseconv.fromhex(hexrand,wl_id)
		Msg(' '.join(mn))

def Mn_rand128(wordlist=dfl_wl_id): do_random_mn(16,wordlist)
def Mn_rand192(wordlist=dfl_wl_id): do_random_mn(24,wordlist)
def Mn_rand256(wordlist=dfl_wl_id): do_random_mn(32,wordlist)

def Hex2mn(s,wordlist=dfl_wl_id): Msg(' '.join(baseconv.fromhex(s,wordlist)))
def Mn2hex(s,wordlist=dfl_wl_id): Msg(baseconv.tohex(s.split(),wordlist))

def Strtob58(s,pad=None): Msg(''.join(baseconv.fromhex(binascii.hexlify(s),'b58',pad)))
def Hextob58(s,pad=None): Msg(''.join(baseconv.fromhex(s,'b58',pad)))
def Hextob32(s,pad=None): Msg(''.join(baseconv.fromhex(s,'b32',pad)))
def B58tostr(s):          Msg(binascii.unhexlify(baseconv.tohex(s,'b58')))
def B58tohex(s,pad=None): Msg(baseconv.tohex(s,'b58',pad))
def B32tohex(s,pad=None): Msg(baseconv.tohex(s.upper(),'b32',pad))

from mmgen.seed import Mnemonic
def Mn_stats(wordlist=dfl_wl_id):
	wordlist in baseconv.digits or die(1,"'{}': not a valid wordlist".format(wordlist))
	baseconv.check_wordlist(wordlist)
def Mn_printlist(wordlist=dfl_wl_id):
	wordlist in baseconv.digits or die(1,"'{}': not a valid wordlist".format(wordlist))
	Msg('\n'.join(baseconv.digits[wordlist]))

def Id8(infile):
	Msg(make_chksum_8(
		get_data_from_file(infile,dash=True,silent=True,binary=True)
	))
def Id6(infile):
	Msg(make_chksum_6(
		get_data_from_file(infile,dash=True,silent=True,binary=True)
	))
def Str2id6(s): # retain ignoring of space for backwards compat
	Msg(make_chksum_6(''.join(s.split())))

def Addrfile_chksum(infile):
	from mmgen.addr import AddrList
	AddrList(infile,chksum_only=True)

def Keyaddrfile_chksum(infile):
	from mmgen.addr import KeyAddrList
	KeyAddrList(infile,chksum_only=True)

def Passwdfile_chksum(infile):
	from mmgen.addr import PasswordList
	PasswordList(infile=infile,chksum_only=True)

def Hexreverse(s):
	Msg(binascii.hexlify(binascii.unhexlify(s.strip())[::-1]))

def Hexlify(s):
	Msg(binascii.hexlify(s))

def Hash256(s, file_input=False, hex_input=False):
	from hashlib import sha256
	if file_input:  b = get_data_from_file(s,binary=True)
	elif hex_input: b = decode_pretty_hexdump(s)
	else:           b = s
	Msg(sha256(sha256(b).digest()).hexdigest())

def Encrypt(infile,outfile='',hash_preset=''):
	data = get_data_from_file(infile,'data for encryption',binary=True)
	enc_d = mmgen_encrypt(data,'user data',hash_preset)
	if not outfile:
		outfile = '%s.%s' % (os.path.basename(infile),g.mmenc_ext)

	write_data_to_file(outfile,enc_d,'encrypted data',binary=True)

def Decrypt(infile,outfile='',hash_preset=''):
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

def Find_incog_data(filename,iv_id,keep_searching=False):
	ivsize,bsize,mod = g.aesctr_iv_len,4096,4096*8
	n,carry = 0,' '*ivsize
	flgs = os.O_RDONLY|os.O_BINARY if g.platform == 'win' else os.O_RDONLY
	f = os.open(filename,flgs)
	for ch in iv_id:
		if ch not in '0123456789ABCDEF':
			die(2,"'%s': invalid Incog ID" % iv_id)
	while True:
		d = os.read(f,bsize)
		if not d: break
		d = carry + d
		for i in range(bsize):
			if sha256(d[i:i+ivsize]).hexdigest()[:8].upper() == iv_id:
				if n+i < ivsize: continue
				msg('\rIncog data for ID %s found at offset %s' %
					(iv_id,n+i-ivsize))
				if not keep_searching: sys.exit(0)
		carry = d[len(d)-ivsize:]
		n += bsize
		if not n % mod: msg_r('\rSearched: %s bytes' % n)

	msg('')
	os.close(f)

def Rand2file(outfile, nbytes, threads=4, silent=False):
	nbytes = parse_nbytes(nbytes)
	from Crypto import Random
	rh = Random.new()
	from Queue import Queue
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
			c = AES.new(key, AES.MODE_CTR,
					counter=Counter.new(g.aesctr_iv_len*8,initial_value=i))
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
		t = Thread(target=encrypt_worker, args=(i,))
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
			msg_r('\rRead: %s bytes' % (bsize*i))

	if not silent:
		msg('\rRead: %s bytes' % nbytes)
		qmsg("\r%s bytes of random data written to file '%s'" % (nbytes,outfile))
	q1.join()
	q2.join()
	f.close()

def Bytespec(s): Msg(str(parse_nbytes(s)))

def Regtest_setup():
	print 'ok'
	return
	import subprocess as sp
	sp.check_output()
	pass

# ================ RPC commands ================== #

def Listaddress(addr,minconf=1,pager=False,showempty=True,showbtcaddr=True):
	return Listaddresses(addrs=addr,minconf=minconf,pager=pager,showempty=showempty,showbtcaddrs=showbtcaddr)

# List MMGen addresses and their balances.  TODO: move this code to AddrList
def Listaddresses(addrs='',minconf=1,showempty=False,pager=False,showbtcaddrs=True,all_labels=False,sort=None):

	if sort:
		sort = set(sort.split(','))
		sort_params = set(['reverse','age'])
		if not sort.issubset(sort_params):
			die(1,"The sort option takes the following parameters: '{}'".format("','".join(sort_params)))

	rpc_init()

	def check_dup_mmid(acct_labels):
		mmid_prev,err = None,False
		for mmid in sorted(a.mmid for a in acct_labels if a):
			if mmid == mmid_prev:
				err = True
				msg('Duplicate MMGen ID ({}) discovered in tracking wallet!\n'.format(mmid))
			mmid_prev = mmid
		if err: rdie(3,'Tracking wallet is corrupted!')

	def check_addr_array_lens(acct_pairs):
		err = False
		for label,addrs in acct_pairs:
			if not label: continue
			if len(addrs) != 1:
				err = True
				if len(addrs) == 0:
					msg("Label '{}': has no associated address!".format(label))
				else:
					msg("'{}': more than one {} address in account!".format(addrs,g.coin))
		if err: rdie(3,'Tracking wallet is corrupted!')

	usr_addr_list = []
	if addrs:
		a = addrs.rsplit(':',1)
		if len(a) != 2:
			m = "'{}': invalid address list argument (must be in form <seed ID>:[<type>:]<idx list>)"
			die(1,m.format(addrs))
		usr_addr_list = [MMGenID('{}:{}'.format(a[0],i)) for i in AddrIdxList(a[1])]

	class TwAddrList(dict,MMGenObject): pass

	addrs = TwAddrList() # reusing name!
	total = g.proto.coin_amt('0')

	for d in g.rpch.listunspent(0):
		if not 'account' in d: continue  # skip coinbase outputs with missing account
		if d['confirmations'] < minconf: continue
		label = TwLabel(d['account'],on_fail='silent')
		if label:
			if usr_addr_list and (label.mmid not in usr_addr_list): continue
			if label.mmid in addrs:
				if addrs[label.mmid]['addr'] != d['address']:
					die(2,'duplicate {} address ({}) for this MMGen address! ({})'.format(
							g.coin,d['address'],addrs[label.mmid]['addr']))
			else:
				addrs[label.mmid] = {'amt': g.proto.coin_amt('0'),
									'lbl':  label,
									'addr': CoinAddr(d['address'])}
				addrs[label.mmid]['lbl'].mmid.confs = d['confirmations']
			addrs[label.mmid]['amt'] += d['amount']
			total += d['amount']

	# We use listaccounts only for empty addresses, as it shows false positive balances
	if showempty or all_labels:
		# for compatibility with old mmids, must use raw RPC rather than native data for matching
		# args: minconf,watchonly, MUST use keys() so we get list, not dict
		acct_list = g.rpch.listaccounts(0,True).keys() # raw list, no 'L'
		acct_labels = MMGenList([TwLabel(a,on_fail='silent') for a in acct_list])
		check_dup_mmid(acct_labels)
		acct_addrs = g.rpch.getaddressesbyaccount([[a] for a in acct_list],batch=True) # use raw list here
		assert len(acct_list) == len(acct_addrs), 'listaccounts() and getaddressesbyaccount() not equal in length'
		addr_pairs = zip(acct_labels,acct_addrs)
		check_addr_array_lens(addr_pairs)
		for label,addr_arr in addr_pairs:
			if not label: continue
			if all_labels and not showempty and not label.comment: continue
			if usr_addr_list and (label.mmid not in usr_addr_list): continue
			if label.mmid not in addrs:
				addrs[label.mmid] = { 'amt':g.proto.coin_amt('0'), 'lbl':label, 'addr':'' }
				if showbtcaddrs:
					addrs[label.mmid]['addr'] = CoinAddr(addr_arr[0])

	if not addrs:
		die(0,('No tracked addresses with balances!','No tracked addresses!')[showempty])

	out = ([],[green('Chain: {}'.format(g.chain.upper()))])[g.chain in ('testnet','regtest')]

	fs = ('{mid} {cmt} {amt}','{mid} {addr} {cmt} {amt}')[showbtcaddrs]
	mmaddrs = [k for k in addrs.keys() if k.type == 'mmgen']
	max_mmid_len = max(len(k) for k in mmaddrs) + 2 if mmaddrs else 10
	max_cmt_len =  max(max(len(addrs[k]['lbl'].comment) for k in addrs),7)
	out += [fs.format(
			mid=MMGenID.fmtc('MMGenID',width=max_mmid_len),
			addr=CoinAddr.fmtc('ADDRESS'),
			cmt=TwComment.fmtc('COMMENT',width=max_cmt_len),
			amt='BALANCE'
			)]

	def sort_algo(j):
		if sort and 'age' in sort:
			return '{}_{:>012}_{}'.format(
				j.obj.rsplit(':',1)[0],
				(1000000000-j.confs if hasattr(j,'confs') else 0), # Hack, but OK for the foreseeable future
				j.sort_key)
		else:
			return j.sort_key

	al_id_save = None
	for mmid in sorted(addrs,key=sort_algo,reverse=bool(sort and 'reverse' in sort)):
		if mmid.type == 'mmgen':
			if al_id_save and al_id_save != mmid.obj.al_id:
				out.append('')
			al_id_save = mmid.obj.al_id
			mmid_disp = mmid
		else:
			if al_id_save:
				out.append('')
				al_id_save = None
			mmid_disp = 'Non-MMGen'
		out.append(fs.format(
			mid = MMGenID.fmtc(mmid_disp,width=max_mmid_len,color=True),
			addr=(addrs[mmid]['addr'].fmt(color=True) if showbtcaddrs else None),
			cmt=addrs[mmid]['lbl'].comment.fmt(width=max_cmt_len,color=True,nullrepl='-'),
			amt=addrs[mmid]['amt'].fmt('3.0',color=True)))
	out.append('\nTOTAL: {} {}'.format(total.hl(color=True),g.coin))
	o = '\n'.join(out)
	return do_pager(o) if pager else Msg(o)

def Getbalance(minconf=1,quiet=False,return_val=False):
	rpc_init()
	accts = {}
	for d in g.rpch.listunspent(0):
		ma = split2(d['account'] if 'account' in d else '')[0] # include coinbase outputs if spendable
		keys = ['TOTAL']
		if d['spendable']: keys += ['SPENDABLE']
		if is_mmgen_id(ma): keys += [ma.split(':')[0]]
		confs = d['confirmations']
		i = (1,2)[confs >= minconf]

		for key in keys:
			if key not in accts: accts[key] = [g.proto.coin_amt('0')] * 3
			for j in ([],[0])[confs==0] + [i]:
				accts[key][j] += d['amount']

	if quiet:
		o = ['{}'.format(accts['TOTAL'][2] if accts else g.proto.coin_amt('0'))]
	else:
		fs = '{:13} {} {} {}'
		mc,lbl = str(minconf),'confirms'
		o = [fs.format('Wallet', *[s.ljust(16) for s in ' Unconfirmed',' <%s %s'%(mc,lbl),' >=%s %s'%(mc,lbl)])]
		for key in sorted(accts.keys()):
			o += [fs.format(key+':', *[a.fmt(color=True,suf=' '+g.coin) for a in accts[key]])]

	if 'SPENDABLE' in accts:
		Msg(red('Warning: this wallet contains PRIVATE KEYS for the SPENDABLE balance!'))

	o = '\n'.join(o)
	if return_val: return o
	else:          Msg(o)

def Txview(*infiles,**kwargs):
	from mmgen.filename import MMGenFileList
	pager = 'pager' in kwargs and kwargs['pager']
	terse = 'terse' in kwargs and kwargs['terse']
	sort_key = kwargs['sort'] if 'sort' in kwargs else 'mtime'
	flist = MMGenFileList(infiles,ftype=MMGenTX)
	flist.sort_by_age(key=sort_key) # in-place sort
	from mmgen.term import get_terminal_size
	sep = u'—'*77+'\n'
	out = sep.join([MMGenTX(fn).format_view(terse=terse) for fn in flist.names()])
	(Msg,do_pager)[pager](out.rstrip())

def Twview(pager=False,reverse=False,wide=False,minconf=1,sort='age',show_days=True,show_mmid=True):
	rpc_init()
	from mmgen.tw import MMGenTrackingWallet
	tw = MMGenTrackingWallet(minconf=minconf)
	tw.do_sort(sort,reverse=reverse)
	tw.show_days = show_days
	tw.show_mmid = show_mmid
	out = tw.format_for_printing(color=True) if wide else tw.format_for_display()
	(Msg_r,do_pager)[pager](out)

def Add_label(mmaddr,label):
	rpc_init()
	from mmgen.tw import MMGenTrackingWallet
	MMGenTrackingWallet.add_label(mmaddr,label) # dies on failure

def Remove_label(mmaddr): Add_label(mmaddr,'')
