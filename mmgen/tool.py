#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2016 Philemon <mmgen-py@yandex.com>
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

import binascii as ba

import mmgen.bitcoin as bitcoin
from mmgen.common import *
from mmgen.crypto import *
from mmgen.tx import *

pnm = g.proj_name

from collections import OrderedDict
cmd_data = OrderedDict([
	('help',         ['<tool command> [str]']),
	('usage',        ['<tool command> [str]']),
	('strtob58',     ['<string> [str]']),
	('b58tostr',     ['<b58 number> [str]']),
	('hextob58',     ['<hex number> [str]']),
	('b58tohex',     ['<b58 number> [str]']),
	('b58randenc',   []),
	('b32tohex',     ['<b32 num> [str]']),
	('hextob32',     ['<hex num> [str]']),
	('randhex',      ['nbytes [int=32]']),
	('id8',          ['<infile> [str]']),
	('id6',          ['<infile> [str]']),
	('sha256x2',     ['<str, hexstr or filename> [str]',
							'hex_input [bool=False]','file_input [bool=False]']),
	('str2id6',      ['<string (spaces are ignored)> [str]']),
	('hexdump',      ['<infile> [str]', 'cols [int=8]', 'line_nums [bool=True]']),
	('unhexdump',    ['<infile> [str]']),
	('hexreverse',   ['<hexadecimal string> [str]']),
	('hexlify',      ['<string> [str]']),
	('rand2file',    ['<outfile> [str]','<nbytes> [str]','threads [int=4]','silent [bool=False]']),

	('randwif',    ['compressed [bool=False]']),
	('randpair',   ['compressed [bool=False]']),
	('hex2wif',    ['<private key in hex format> [str]', 'compressed [bool=False]']),
	('wif2hex',    ['<wif> [str]', 'compressed [bool=False]']),
	('wif2addr',   ['<wif> [str]', 'compressed [bool=False]']),
	('hexaddr2addr', ['<btc address in hex format> [str]']),
	('addr2hexaddr', ['<btc address> [str]']),
	('pubkey2addr',  ['<public key in hex format> [str]']),
	('pubkey2hexaddr', ['<public key in hex format> [str]']),
	('privhex2addr', ['<private key in hex format> [str]','compressed [bool=False]']),

	('hex2mn',       ['<hexadecimal string> [str]',"wordlist [str='electrum']"]),
	('mn2hex',       ['<mnemonic> [str]', "wordlist [str='electrum']"]),
	('mn_rand128',   ["wordlist [str='electrum']"]),
	('mn_rand192',   ["wordlist [str='electrum']"]),
	('mn_rand256',   ["wordlist [str='electrum']"]),
	('mn_stats',     ["wordlist [str='electrum']"]),
	('mn_printlist', ["wordlist [str='electrum']"]),


	('listaddresses',["addrs [str='']",'minconf [int=1]','showempty [bool=False]','pager [bool=False]','showbtcaddrs [bool=False]']),
	('getbalance',   ['minconf [int=1]']),
	('txview',       ['<{} TX file> [str]'.format(pnm),'pager [bool=False]','terse [bool=False]']),

	('add_label',       ['<{} address> [str]'.format(pnm),'<label> [str]']),
	('remove_label',    ['<{} address> [str]'.format(pnm)]),
	('addrfile_chksum', ['<{} addr file> [str]'.format(pnm)]),
	('keyaddrfile_chksum', ['<{} addr file> [str]'.format(pnm)]),
	('find_incog_data', ['<file or device name> [str]','<Incog ID> [str]','keep_searching [bool=False]']),

	('encrypt',      ['<infile> [str]',"outfile [str='']","hash_preset [str='']"]),
	('decrypt',      ['<infile> [str]',"outfile [str='']","hash_preset [str='']"]),
	('bytespec',     ['<bytespec> [str]']),
])

cmd_help = """
  Bitcoin address/key operations (compressed public keys supported):
  addr2hexaddr - convert Bitcoin address from base58 to hex format
  hex2wif      - convert a private key from hex to WIF format
  hexaddr2addr - convert Bitcoin address from hex to base58 format
  privhex2addr - generate Bitcoin address from private key in hex format
  pubkey2addr  - convert Bitcoin public key to address
  pubkey2hexaddr - convert Bitcoin public key to address in hex format
  randpair     - generate a random private key/address pair
  randwif      - generate a random private key in WIF format
  wif2addr     - generate a Bitcoin address from a key in WIF format
  wif2hex      - convert a private key from WIF to hex format

  Wallet/TX operations (bitcoind must be running):
  getbalance    - like 'bitcoind getbalance' but shows confirmed/unconfirmed,
                  spendable/unspendable balances for individual {pnm} wallets
  listaddresses - list {pnm} addresses and their balances
  txview        - show raw/signed {pnm} transaction in human-readable form

  General utilities:
  hexdump      - encode data into formatted hexadecimal form (file or stdin)
  unhexdump    - decode formatted hexadecimal data (file or stdin)
  bytespec     - convert a byte specifier such as '1GB' into an integer
  hexlify      - display string in hexadecimal format
  hexreverse   - reverse bytes of a hexadecimal string
  rand2file    - write 'n' bytes of random data to specified file
  randhex      - print 'n' bytes (default 32) of random data in hex format
  sha256x2     - compute a double sha256 hash of data
  b58randenc   - generate a random 32-byte number and convert it to base 58
  b58tostr     - convert a base 58 number to a string
  strtob58     - convert a string to base 58
  b58tohex     - convert a base 58 number to hexadecimal
  hextob58     - convert a hexadecimal number to base 58
  b32tohex     - convert a base 32 number to hexadecimal
  hextob32     - convert a hexadecimal number to base 32

  File encryption:
  encrypt      - encrypt a file
  decrypt      - decrypt a file
    {pnm} encryption suite:
      * Key: Scrypt (user-configurable hash parameters, 32-byte salt)
      * Enc: AES256_CTR, 16-byte rand IV, sha256 hash + 32-byte nonce + data
      * The encrypted file is indistinguishable from random data

  {pnm}-specific operations:
  add_label    - add descriptive label for {pnm} address in tracking wallet
  remove_label - remove descriptive label for {pnm} address in tracking wallet
  addrfile_chksum    - compute checksum for {pnm} address file
  keyaddrfile_chksum - compute checksum for {pnm} key-address file
  find_incog_data    - Use an Incog ID to find hidden incognito wallet data
  id6          - generate 6-character {pnm} ID for a file (or stdin)
  id8          - generate 8-character {pnm} ID for a file (or stdin)
  str2id6      - generate 6-character {pnm} ID for a string, ignoring spaces

  Mnemonic operations (choose 'electrum' (default), 'tirosh' or 'all'
  wordlists):
  mn_rand128   - generate random 128-bit mnemonic
  mn_rand192   - generate random 192-bit mnemonic
  mn_rand256   - generate random 256-bit mnemonic
  mn_stats     - show stats for mnemonic wordlist
  mn_printlist - print mnemonic wordlist
  hex2mn       - convert a 16, 24 or 32-byte number in hex format to a mnemonic
  mn2hex       - convert a 12, 18 or 24-word mnemonic to a number in hex format

  IMPORTANT NOTE: Though {pnm} mnemonics use the Electrum wordlist, they're
  computed using a different algorithm and are NOT Electrum-compatible!
""".format(pnm=pnm)

def tool_usage(prog_name, command):
	if command in cmd_data:
		Msg('USAGE: %s %s %s' % (prog_name, command, ' '.join(cmd_data[command])))
	else:
		Msg("'%s': no such tool command" % command)

def process_args(prog_name, command, cmd_args):
	c_args = [[i.split(' [')[0],i.split(' [')[1][:-1]]
		for i in cmd_data[command] if '=' not in i]
	c_kwargs = dict([[
			i.split(' [')[0],
			[i.split(' [')[1].split('=')[0], i.split(' [')[1].split('=')[1][:-1]]
		] for i in cmd_data[command] if '=' in i])

	u_args = cmd_args[:len(c_args)]
	u_kwargs = cmd_args[len(c_args):]

	if len(u_args) < len(c_args):
		msg('%s argument%s required' % (len(c_args),suf(c_args,'k')))
		tool_usage(prog_name, command)
		sys.exit(1)

	if len(u_kwargs) > len(c_kwargs):
		msg('Too many arguments')
		tool_usage(prog_name, command)
		sys.exit(1)

	u_kwargs = dict([a.split('=') for a in u_kwargs])

#	print c_args; print c_kwargs; print u_args; print u_kwargs; sys.exit()

	if set(u_kwargs) > set(c_kwargs):
		die(1,'Invalid named argument')

	def convert_type(arg,arg_name,arg_type):
		try:
			return __builtins__[arg_type](arg)
		except:
			die(1,"'%s': Invalid argument for argument %s ('%s' required)" % \
				(arg, arg_name, arg_type))

	def convert_to_bool_maybe(arg, arg_type):
		if arg_type == 'bool':
			if arg.lower() in ('true','yes','1','on'): return True
			if arg.lower() in ('false','no','0','off'): return False
		return arg

	args = []
	for i in range(len(c_args)):
		arg_type = c_args[i][1]
		arg = convert_to_bool_maybe(u_args[i], arg_type)
		args.append(convert_type(arg,c_args[i][0],arg_type))

	kwargs = {}
	for k in u_kwargs:
		arg_type = c_kwargs[k][0]
		arg = convert_to_bool_maybe(u_kwargs[k], arg_type)
		kwargs[k] = convert_type(arg,k,arg_type)

	return args,kwargs

# Individual cmd_data

# def help():
# 	Msg('Available commands:')
# 	for k in sorted(cmd_data.keys()):
# 		Msg('%-16s %s' % (k,' '.join(cmd_data[k])))

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

def usage(cmd):
	tool_usage(g.prog_name, cmd)

help = usage

def hexdump(infile, cols=8, line_nums=True):
	Msg(pretty_hexdump(
			get_data_from_file(infile,dash=True,silent=True,binary=True),
				cols=cols,line_nums=line_nums))

def unhexdump(infile):
	if sys.platform[:3] == 'win':
		import msvcrt
		msvcrt.setmode(sys.stdout.fileno(),os.O_BINARY)
	sys.stdout.write(decode_pretty_hexdump(
			get_data_from_file(infile,dash=True,silent=True)))

def strtob58(s):
	enc = bitcoin.b58encode(s)
	dec = bitcoin.b58decode(enc)
	print_convert_results(s,enc,dec,'str')

def hextob58(s,f_enc=bitcoin.b58encode, f_dec=bitcoin.b58decode):
	enc = f_enc(ba.unhexlify(s))
	dec = ba.hexlify(f_dec(enc))
	print_convert_results(s,enc,dec,'hex')

def b58tohex(s,f_enc=bitcoin.b58decode, f_dec=bitcoin.b58encode):
	tmp = f_enc(s)
	if tmp == False: sys.exit(1)
	enc = ba.hexlify(tmp)
	dec = f_dec(ba.unhexlify(enc))
	print_convert_results(s,enc,dec,'b58')

def b58tostr(s,f_enc=bitcoin.b58decode, f_dec=bitcoin.b58encode):
	enc = f_enc(s)
	if enc == False: sys.exit(1)
	dec = f_dec(enc)
	print_convert_results(s,enc,dec,'b58')

def b58randenc():
	r = get_random(32)
	enc = bitcoin.b58encode(r)
	dec = bitcoin.b58decode(enc)
	print_convert_results(r,enc,dec,'str')

def randhex(nbytes='32'):
	Msg(ba.hexlify(get_random(int(nbytes))))

def randwif(compressed=False):
	r_hex = ba.hexlify(get_random(32))
	enc = bitcoin.hextowif(r_hex,compressed)
	dec = bitcoin.wiftohex(enc,compressed)
	print_convert_results(r_hex,enc,dec,'hex')

def randpair(compressed=False):
	r_hex = ba.hexlify(get_random(32))
	wif = bitcoin.hextowif(r_hex,compressed)
	addr = bitcoin.privnum2addr(int(r_hex,16),compressed)
	Vmsg('Key (hex):  %s' % r_hex)
	Vmsg_r('Key (WIF):  '); Msg(wif)
	Vmsg_r('Addr:       '); Msg(addr)

def wif2addr(wif,compressed=False):
	s_enc = bitcoin.wiftohex(wif,compressed)
	if s_enc == False:
		die(1,'Invalid address')
	addr = bitcoin.privnum2addr(int(s_enc,16),compressed)
	Vmsg_r('Addr: '); Msg(addr)

wordlists = 'electrum','tirosh'
dfl_wordlist = 'electrum'

from mmgen.seed import Mnemonic
def do_random_mn(nbytes,wordlist):
	hexrand = ba.hexlify(get_random(nbytes))
	Vmsg('Seed: %s' % hexrand)
	for wlname in ([wordlist],wordlists)[wordlist=='all']:
		if wordlist == 'all':
			Msg('%s mnemonic:' % (wlname.capitalize()))
		mn = Mnemonic.hex2mn(hexrand,wordlist=wlname)
		Msg(' '.join(mn))

def mn_rand128(wordlist=dfl_wordlist): do_random_mn(16,wordlist)
def mn_rand192(wordlist=dfl_wordlist): do_random_mn(24,wordlist)
def mn_rand256(wordlist=dfl_wordlist): do_random_mn(32,wordlist)

def hex2mn(s,wordlist=dfl_wordlist):
	mn = Mnemonic.hex2mn(s,wordlist)
	Msg(' '.join(mn))

def mn2hex(s,wordlist=dfl_wordlist):
	hexnum = Mnemonic.mn2hex(s.split(),wordlist)
	Msg(hexnum)

def b32tohex(s):
	b32a = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
	Msg(Mnemonic.baseNtohex(32,s,b32a))

def hextob32(s):
	b32a = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
	Msg(''.join(Mnemonic.hextobaseN(32,s,b32a)))

def mn_stats(wordlist=dfl_wordlist):
	Mnemonic.check_wordlist(wordlist)

def mn_printlist(wordlist=dfl_wordlist):
	wl = Mnemonic.get_wordlist(wordlist)
	Msg('\n'.join(wl))

def id8(infile):
	Msg(make_chksum_8(
		get_data_from_file(infile,dash=True,silent=True,binary=True)
	))
def id6(infile):
	Msg(make_chksum_6(
		get_data_from_file(infile,dash=True,silent=True,binary=True)
	))
def str2id6(s):  Msg(make_chksum_6(''.join(s.split())))

# List MMGen addresses and their balances:
def listaddresses(addrs='',minconf=1,showempty=False,pager=False,showbtcaddrs=False):

	usr_addr_list = []
	if addrs:
		sid,idxs = split2(addrs,':')
		if not idxs:
			s1 = "'%s': invalid address argument\n"
			s2 = "Address argument format: <%s Seed ID>':'<index or range>"
			die(1, (s1+s2) % (addrs,g.proj_name))
		if not is_mmgen_seed_id(sid):
			die(1,'%s: invalid %s Seed ID' % (g.proj_name,sid))
		tmp = parse_addr_idxs(idxs)
		if not tmp: return False
		usr_addr_list = ['%s:%s' % (sid,i) for i in tmp]

	c = bitcoin_connection()

	addrs = {} # reusing variable name!
	from decimal import Decimal
	total = Decimal('0')
	for d in c.listunspent(0):
		mmaddr,comment = split2(d['account'])
		if usr_addr_list and (mmaddr not in usr_addr_list): continue
		if is_mmgen_addr(mmaddr) and d['confirmations'] >= minconf:
			key = mmaddr.replace(':','_')
			if key in addrs:
				if addrs[key][2] != d['address']:
					die(2,'duplicate BTC address ({}) for this MMGen address! ({})'.format(
							(d['address'], addrs[key][2])))
			else:
				addrs[key] = [0,comment,d['address']]
			addrs[key][0] += d['amount']
			total += d['amount']

	# We use listaccounts only for empty addresses, as it shows false positive balances
	if showempty:
		accts = c.listaccounts(0,True) # minconf,watchonly
		save_a = []
		for acct in accts:
			mmaddr,comment = split2(acct)
			if usr_addr_list and (mmaddr not in usr_addr_list): continue
			if is_mmgen_addr(mmaddr):
				key = mmaddr.replace(':','_')
				if key not in addrs:
					if showbtcaddrs: save_a.append([acct])
					addrs[key] = [0,comment,'']

		for acct,addr in zip(save_a,c.getaddressesbyaccount(save_a,batch=True)):
			if len(addr) != 1:
				die(2,"Account '%s' has more or less than one BTC address!" % addr)
			key = split2(acct[0])[0].replace(':','_')
			addrs[key][2] = addr[0]

	if not addrs:
		die(1,('No addresses with balances!','No tracked addresses!')[showempty])

	fs = '%-{}s %-{}s %-{}s %s'.format(
		max(len(k) for k in addrs),
		(0,36)[showbtcaddrs],
		max(max(len(addrs[k][1]) for k in addrs) + 1,8) # pad 8 if no comments
	)

	def s_mmgen(key):
		return '{}:{:>0{w}}'.format(w=g.mmgen_idx_max_digits, *key.split('_'))

	out = []
	for k in sorted(addrs,key=s_mmgen):
		if out and k.split('_')[0] != out[-1].split(':')[0]: out.append('')
		baddr = ' ' + addrs[k][2] if showbtcaddrs else ''
		out.append(fs % (k.replace('_',':'), baddr, addrs[k][1], trim_exponent(addrs[k][0])))

	o = (fs + '\n%s\nTOTAL: %s BTC') % (
			'ADDRESS','','COMMENT','BALANCE', '\n'.join(out), trim_exponent(total)
		)
	if pager: do_pager(o)
	else: Msg(o)


def getbalance(minconf=1):

	accts = {}
	for d in bitcoin_connection().listunspent(0):
		ma = split2(d['account'])[0]
		keys = ['TOTAL']
		if d['spendable']: keys += ['SPENDABLE']
		if is_mmgen_addr(ma): keys += [ma.split(':')[0]]
		confs = d['confirmations']
		i = (1,2)[confs >= minconf]

		for key in keys:
			if key not in accts: accts[key] = [0,0,0]
			for j in ([],[0])[confs==0] + [i]:
				accts[key][j] += d['amount']

	fs = '{:12}  {:<%s} {:<%s} {:<}' % (16,16)
	mc,lbl = str(minconf),'confirms'
	Msg(fs.format('Wallet','Unconfirmed','<%s %s'%(mc,lbl),'>=%s %s'%(mc,lbl)))
	for key in sorted(accts.keys()):
		Msg(fs.format(key+':', *[str(trim_exponent(a))+' BTC'
				for a in accts[key]]))

def txview(infile,pager=False,terse=False):
	c = bitcoin_connection()
	tx_data = get_lines_from_file(infile,'transaction data')

	metadata,tx_hex,inputs_data,b2m_map,comment = parse_tx_file(tx_data,infile)
	view_tx_data(c,inputs_data,tx_hex,b2m_map,comment,metadata,pager,pause=False,terse=terse)

def add_label(mmaddr,label,remove=False):
	if not is_mmgen_addr(mmaddr):
		die(1,'{a}: not a valid {pnm} address'.format(pnm=pnm,a=mmaddr))
	check_addr_label(label)  # Exits on failure

	c = bitcoin_connection()

	from mmgen.addr import AddrInfoList
	btcaddr = AddrInfoList(bitcoind_connection=c).mmaddr2btcaddr(mmaddr)

	if not btcaddr:
		die(1,'{pnm} address {a} not found in tracking wallet'.format(
				pnm=pnm,a=mmaddr))

	try:
		l = ' ' + label if label else ''
		c.importaddress(btcaddr,mmaddr+l,False) # addr,label,rescan,p2sh
	except:
		die(1,'Unable to add label')

	s = '{pnm} address {a} in tracking wallet'.format(a=mmaddr,pnm=pnm)
	if remove: msg('Removed label from {}'.format(s))
	else:      msg("Added label '{}' for {}".format(label,s))

def remove_label(mmaddr): add_label(mmaddr,'',remove=True)

def addrfile_chksum(infile):
	from mmgen.addr import AddrInfo
	AddrInfo(infile,caller='tool')

def keyaddrfile_chksum(infile):
	from mmgen.addr import AddrInfo
	AddrInfo(infile,has_keys=True,caller='tool')

def hexreverse(hex_str):
	Msg(ba.hexlify(decode_pretty_hexdump(hex_str)[::-1]))

def hexlify(s):
	Msg(ba.hexlify(s))

def sha256x2(s, file_input=False, hex_input=False):
	from hashlib import sha256
	if file_input:  b = get_data_from_file(s,binary=True)
	elif hex_input: b = decode_pretty_hexdump(s)
	else:           b = s
	Msg(sha256(sha256(b).digest()).hexdigest())

def hexaddr2addr(hexaddr):
	Msg(bitcoin.hexaddr2addr(hexaddr))

def addr2hexaddr(addr):
	Msg(bitcoin.verify_addr(addr,return_hex=True))

def pubkey2hexaddr(pubkeyhex):
	Msg(bitcoin.pubhex2hexaddr(pubkeyhex))

def pubkey2addr(pubkeyhex):
	Msg(bitcoin.hexaddr2addr(bitcoin.pubhex2hexaddr(pubkeyhex)))

def privhex2addr(privkeyhex,compressed=False):
	Msg(bitcoin.privnum2addr(int(privkeyhex,16),compressed))

def wif2hex(wif,compressed=False):
	Msg(bitcoin.wiftohex(wif,compressed))

def hex2wif(hexpriv,compressed=False):
	Msg(bitcoin.hextowif(hexpriv,compressed))


def encrypt(infile,outfile='',hash_preset=''):
	data = get_data_from_file(infile,'data for encryption',binary=True)
	enc_d = mmgen_encrypt(data,'user data',hash_preset)
	if not outfile:
		outfile = '%s.%s' % (os.path.basename(infile),g.mmenc_ext)

	write_data_to_file(outfile,enc_d,'encrypted data',binary=True)


def decrypt(infile,outfile='',hash_preset=''):
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


def find_incog_data(filename,iv_id,keep_searching=False):
	ivsize,bsize,mod = g.aesctr_iv_len,4096,4096*8
	n,carry = 0,' '*ivsize
	f = os.open(filename,os.O_RDONLY)
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
				if not keep_searching: sys.exit()
		carry = d[len(d)-ivsize:]
		n += bsize
		if not n % mod: msg_r('\rSearched: %s bytes' % n)

	msg('')
	os.close(f)


def rand2file(outfile, nbytes, threads=4, silent=False):
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

def bytespec(s): Msg(str(parse_nbytes(s)))
