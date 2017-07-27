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

import binascii as ba

import mmgen.bitcoin as mmb
from mmgen.common import *
from mmgen.crypto import *
from mmgen.tx import *

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
	('Hexaddr2addr', ['<btc address in hex format> [str-]']),
	('Addr2hexaddr', ['<btc address> [str-]']),
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
	('Listaddresses',["addrs [str='']",'minconf [int=1]','showempty [bool=False]','pager [bool=False]','showbtcaddrs [bool=False]']),
	('Getbalance',   ['minconf [int=1]']),
	('Txview',       ['<{} TX file(s)> [str]'.format(pnm),'pager [bool=False]','terse [bool=False]',"sort [str='mtime'] (options: 'ctime','atime')",'MARGS']),
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
])

stdin_msg = """
To force a command to read from STDIN in place of its first argument (for
supported commands), use '-' as the first argument.
""".strip()

cmd_help = """
Bitcoin address/key operations (compressed public keys supported):
  addr2hexaddr   - convert Bitcoin address from base58 to hex format
  hex2wif        - convert a private key from hex to WIF format
  hexaddr2addr   - convert Bitcoin address from hex to base58 format
  privhex2addr   - generate Bitcoin address from private key in hex format
  privhex2pubhex - generate a hex public key from a hex private key
  pubhex2addr    - convert a hex pubkey to an address
  pubhex2redeem_script - convert a hex pubkey to a witness redeem script
  wif2redeem_script - convert a WIF private key to a witness redeem script
  wif2segwit_pair - generate both a Segwit redeem script and address from WIF
  pubkey2addr    - convert Bitcoin public key to address
  randpair       - generate a random private key/address pair
  randwif        - generate a random private key in WIF format
  wif2addr       - generate a Bitcoin address from a key in WIF format
  wif2hex        - convert a private key from WIF to hex format

Wallet/TX operations (bitcoind must be running):
  getbalance    - like 'bitcoin-cli getbalance' but shows confirmed/unconfirmed,
                  spendable/unspendable balances for individual {pnm} wallets
  listaddress   - list the specified {pnm} address and its balance
  listaddresses - list {pnm} addresses and their balances
  txview        - show raw/signed {pnm} transaction in human-readable form
  twview        - view tracking wallet

General utilities:
  hexdump      - encode data into formatted hexadecimal form (file or stdin)
  unhexdump    - decode formatted hexadecimal data (file or stdin)
  bytespec     - convert a byte specifier such as '1GB' into an integer
  hexlify      - display string in hexadecimal format
  hexreverse   - reverse bytes of a hexadecimal string
  rand2file    - write 'n' bytes of random data to specified file
  randhex      - print 'n' bytes (default 32) of random data in hex format
  hash256      - compute sha256(sha256(data)) (double sha256)
  hash160      - compute ripemd160(sha256(data)) (converts hexpubkey to hexaddr)
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
  passwdfile_chksum  - compute checksum for {pnm} password file
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

  {sm}
""".format(pnm=pnm,sm='\n  '.join(stdin_msg.split('\n')))

def usage(command):

	for v in cmd_data.values():
		if v and v[0][-2:] == '-]':
			v[0] = v[0][:-2] + ' or STDIN]'
		if 'MARGS' in v: v.remove('MARGS')

	if not command:
		Msg('Usage information for mmgen-tool commands:')
		for k,v in cmd_data.items():
			Msg('  {:18} {}'.format(k.lower(),' '.join(v)))
		Msg('\n  '+'\n  '.join(stdin_msg.split('\n')))
		sys.exit(0)

	Command = command.capitalize()
	if Command in cmd_data:
		import re
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
	enc = mmb.b58encode(r)
	dec = mmb.b58decode(enc)
	print_convert_results(r,enc,dec,'str')

def Randhex(nbytes='32'):
	Msg(ba.hexlify(get_random(int(nbytes))))

def Randwif(compressed=False):
	r_hex = ba.hexlify(get_random(32))
	enc = mmb.hex2wif(r_hex,compressed)
	dec = wif2hex(enc)
	print_convert_results(r_hex,enc,dec,'hex')

def Randpair(compressed=False,segwit=False):
	if segwit: compressed = True
	r_hex = ba.hexlify(get_random(32))
	wif = mmb.hex2wif(r_hex,compressed)
	addr = mmb.privnum2addr(int(r_hex,16),compressed,segwit=segwit)
	Vmsg('Key (hex):  %s' % r_hex)
	Vmsg_r('Key (WIF):  '); Msg(wif)
	Vmsg_r('Addr:       '); Msg(addr)

def Wif2addr(wif,segwit=False):
	compressed = mmb.wif_is_compressed(wif)
	if segwit and not compressed:
		die(1,'Segwit address cannot be generated from uncompressed WIF')
	privhex = wif2hex(wif)
	addr = mmb.privnum2addr(int(privhex,16),compressed,segwit=segwit)
	Vmsg_r('Addr: '); Msg(addr)

def Wif2segwit_pair(wif):
	if not mmb.wif_is_compressed(wif):
		die(1,'Segwit address cannot be generated from uncompressed WIF')
	privhex = wif2hex(wif)
	pubhex = mmb.privnum2pubhex(int(privhex,16),compressed=True)
	rs = mmb.pubhex2redeem_script(pubhex)
	addr = mmb.hexaddr2addr(mmb.hash160(rs),p2sh=True)
	addr_chk = mmb.privnum2addr(int(privhex,16),compressed=True,segwit=True)
	assert addr == addr_chk
	Msg('{}\n{}'.format(rs,addr))

def Hexaddr2addr(hexaddr):                     Msg(mmb.hexaddr2addr(hexaddr))
def Addr2hexaddr(addr):                        Msg(mmb.verify_addr(addr,return_hex=True))
def Hash160(pubkeyhex):                        Msg(mmb.hash160(pubkeyhex))
def Pubhex2addr(pubkeyhex,p2sh=False):         Msg(mmb.hexaddr2addr(mmb.hash160(pubkeyhex),p2sh=p2sh))
def Wif2hex(wif):                              Msg(wif2hex(wif))
def Hex2wif(hexpriv,compressed=False):
	Msg(mmb.hex2wif(hexpriv,compressed))
def Privhex2addr(privhex,compressed=False,segwit=False):
	if segwit and not compressed:
		die(1,'Segwit address can be generated only from a compressed pubkey')
	Msg(mmb.privnum2addr(int(privhex,16),compressed,segwit=segwit))
def Privhex2pubhex(privhex,compressed=False): # new
	Msg(mmb.privnum2pubhex(int(privhex,16),compressed))
def Pubhex2redeem_script(pubhex): # new
	Msg(mmb.pubhex2redeem_script(pubhex))
def Wif2redeem_script(wif): # new
	if not mmb.wif_is_compressed(wif):
		die(1,'Witness redeem script cannot be generated from uncompressed WIF')
	pubhex = mmb.privnum2pubhex(int(wif2hex(wif),16),compressed=True)
	Msg(mmb.pubhex2redeem_script(pubhex))

def wif2hex(wif): # wrapper
	ret = mmb.wif2hex(wif)
	return ret or die(1,'{}: Invalid WIF'.format(wif))

wordlists = 'electrum','tirosh'
dfl_wl_id = 'electrum'

def do_random_mn(nbytes,wordlist):
	hexrand = ba.hexlify(get_random(nbytes))
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

def Strtob58(s,pad=None): Msg(''.join(baseconv.fromhex(ba.hexlify(s),'b58',pad)))
def Hextob58(s,pad=None): Msg(''.join(baseconv.fromhex(s,'b58',pad)))
def Hextob32(s,pad=None): Msg(''.join(baseconv.fromhex(s,'b32',pad)))
def B58tostr(s):          Msg(ba.unhexlify(baseconv.tohex(s,'b58')))
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

def Listaddress(addr,minconf=1,pager=False,showempty=True,showbtcaddr=True):
	return Listaddresses(addrs=addr,minconf=minconf,pager=pager,showempty=showempty,showbtcaddrs=showbtcaddr)

# List MMGen addresses and their balances.  TODO: move this code to AddrList
def Listaddresses(addrs='',minconf=1,showempty=False,pager=False,showbtcaddrs=False):

	c = bitcoin_connection()

	def check_dup_mmid(accts):
		help_msg = """
    Your tracking wallet is corrupted or has been altered by a non-{pnm} program.

    You might be able to salvage your wallet by determining which of the offending
    addresses doesn't belong to {pnm} ID {mid} and then typing:

        bitcoin-cli importaddress <offending address> "" false
	"""
		m_prev = None

		for m in sorted([l.mmid for l in accts]):
			if m == m_prev:
				msg('Duplicate MMGen ID ({}) discovered in tracking wallet!\n'.format(m))
				bad_accts = MMGenList([l for l in accts if l.mmid == m])
				msg('  Affected Bitcoin RPC accounts:\n    {}\n'.format('\n    '.join(bad_accts)))
				bad_addrs = [a[0] for a in c.getaddressesbyaccount([[a] for a in bad_accts],batch=True)]
				if len(set(bad_addrs)) != 1:
					msg('  Offending addresses:\n    {}'.format('\n    '.join(bad_addrs)))
					msg(help_msg.format(mid=m,pnm=pnm))
				die(3,red('Exiting on error'))
			m_prev = m

	usr_addr_list = []
	if addrs:
		a = addrs.rsplit(':',1)
		if len(a) != 2:
			m = "'{}': invalid address list argument (must be in form <seed ID>:[<type>:]<idx list>)"
			die(1,m.format(addrs))
		usr_addr_list = [MMGenID('{}:{}'.format(a[0],i)) for i in AddrIdxList(a[1])]

	class TwAddrList(dict,MMGenObject): pass

	addrs = TwAddrList() # reusing name!
	total = BTCAmt('0')

	for d in c.listunspent(0):
		if not 'account' in d: continue  # skip coinbase outputs with missing account
		if d['confirmations'] < minconf: continue
		label = TwLabel(d['account'],on_fail='silent')
		if label:
			if usr_addr_list and (label.mmid not in usr_addr_list): continue
			if label.mmid in addrs:
				if addrs[label.mmid]['addr'] != d['address']:
					die(2,'duplicate BTC address ({}) for this MMGen address! ({})'.format(
							(d['address'], addrs[label.mmid]['addr'])))
			else:
				addrs[label.mmid] = { 'amt':BTCAmt('0'), 'lbl':label, 'addr':BTCAddr(d['address']) }
			addrs[label.mmid]['amt'] += d['amount']
			total += d['amount']

	# We use listaccounts only for empty addresses, as it shows false positive balances
	if showempty:
		# args: minconf,watchonly
		accts = MMGenList([b for b in [TwLabel(a,on_fail='silent') for a in c.listaccounts(0,True)] if b])
		check_dup_mmid(accts)
		acct_addrs = c.getaddressesbyaccount([[a] for a in accts],batch=True)
		assert len(accts) == len(acct_addrs), 'listaccounts() and getaddressesbyaccount() not of same length'
		for a in acct_addrs:
			if len(a) != 1:
				die(2,"'{}': more than one BTC address in account!".format(a))
		for label,addr in zip(accts,[b[0] for b in acct_addrs]):
			if usr_addr_list and (label.mmid not in usr_addr_list): continue
			if label.mmid not in addrs:
				addrs[label.mmid] = { 'amt':BTCAmt('0'), 'lbl':label, 'addr':'' }
				if showbtcaddrs:
					addrs[label.mmid]['addr'] = BTCAddr(addr)

	if not addrs:
		die(0,('No tracked addresses with balances!','No tracked addresses!')[showempty])

	out = ([],[green('Chain: {}'.format(g.chain.upper()))])[g.chain in ('testnet','regtest')]

	fs = ('{mid} {cmt} {amt}','{mid} {addr} {cmt} {amt}')[showbtcaddrs]
	mmaddrs = [k for k in addrs.keys() if k.type == 'mmgen']
	max_mmid_len = max(len(k) for k in mmaddrs) + 2 if mmaddrs else 10
	max_cmt_len =  max(max(len(addrs[k]['lbl'].comment) for k in addrs),7)
	out += [fs.format(
			mid=MMGenID.fmtc('MMGenID',width=max_mmid_len),
			addr=BTCAddr.fmtc('ADDRESS'),
			cmt=TwComment.fmtc('COMMENT',width=max_cmt_len),
			amt='BALANCE'
			)]

	al_id_save = None
	for mmid in sorted(addrs,key=lambda j: j.sort_key):
		if mmid.type == 'mmgen':
			if al_id_save and al_id_save != mmid.obj.al_id:
				out.append('')
			al_id_save = mmid.obj.al_id
			mmid_disp = mmid
		else:
			if al_id_save:
				out.append('')
				al_id_save = None
			mmid_disp = mmid.type
		out.append(fs.format(
			mid = MMGenID.fmtc(mmid_disp,width=max_mmid_len,color=True),
			addr=(addrs[mmid]['addr'].fmt(color=True) if showbtcaddrs else None),
			cmt=addrs[mmid]['lbl'].comment.fmt(width=max_cmt_len,color=True,nullrepl='-'),
			amt=addrs[mmid]['amt'].fmt('3.0',color=True)))

	out.append('\nTOTAL: %s BTC' % total.hl(color=True))
	o = '\n'.join(out)
	return do_pager(o) if pager else Msg(o)

def Getbalance(minconf=1):
	accts = {}
	for d in bitcoin_connection().listunspent(0):
		ma = split2(d['account'] if 'account' in d else '')[0] # include coinbase outputs if spendable
		keys = ['TOTAL']
		if d['spendable']: keys += ['SPENDABLE']
		if is_mmgen_id(ma): keys += [ma.split(':')[0]]
		confs = d['confirmations']
		i = (1,2)[confs >= minconf]

		for key in keys:
			if key not in accts: accts[key] = [BTCAmt('0')] * 3
			for j in ([],[0])[confs==0] + [i]:
				accts[key][j] += d['amount']

	fs = '{:13} {} {} {}'
	mc,lbl = str(minconf),'confirms'
	Msg(fs.format('Wallet',
		*[s.ljust(16) for s in ' Unconfirmed',' <%s %s'%(mc,lbl),' >=%s %s'%(mc,lbl)]))
	for key in sorted(accts.keys()):
		Msg(fs.format(key+':', *[a.fmt(color=True,suf=' BTC') for a in accts[key]]))
	if 'SPENDABLE' in accts:
		Msg(red('Warning: this wallet contains PRIVATE KEYS for the SPENDABLE balance!'))

def Txview(*infiles,**kwargs):
	from mmgen.filename import MMGenFileList
	pager = 'pager' in kwargs and kwargs['pager']
	terse = 'terse' in kwargs and kwargs['terse']
	sort_key = kwargs['sort'] if 'sort' in kwargs else 'mtime'
	flist = MMGenFileList(infiles,ftype=MMGenTX)
	flist.sort_by_age(key=sort_key) # in-place sort
	from mmgen.term import get_terminal_size
	sep = u'—'*get_terminal_size()[0]+'\n'
	out = sep.join([MMGenTX(fn).format_view(terse=terse) for fn in flist.names()])
	(Msg,do_pager)[pager](out.rstrip())

def Twview(pager=False,reverse=False,wide=False,minconf=1,sort='age',show_days=True,show_mmid=True):
	from mmgen.tw import MMGenTrackingWallet
	tw = MMGenTrackingWallet(minconf=minconf)
	tw.do_sort(sort,reverse=reverse)
	tw.show_days = show_days
	tw.show_mmid = show_mmid
	out = tw.format_for_printing(color=True) if wide else tw.format_for_display()
	(Msg_r,do_pager)[pager](out)

def Add_label(mmaddr,label):
	from mmgen.tw import MMGenTrackingWallet
	MMGenTrackingWallet.add_label(mmaddr,label) # dies on failure

def Remove_label(mmaddr): Add_label(mmaddr,'')

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
	Msg(ba.hexlify(ba.unhexlify(s.strip())[::-1]))

def Hexlify(s):
	Msg(ba.hexlify(s))

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
