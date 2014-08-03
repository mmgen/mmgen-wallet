#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C) 2013-2014 by philemon <mmgen-py@yandex.com>
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
tool.py:  Routines and data for the mmgen-tool utility
"""

import sys
import mmgen.bitcoin as bitcoin
import binascii as ba

import mmgen.config as g
from mmgen.util import *
from mmgen.tx import *

def Msg(s):    sys.stdout.write(s + "\n")
def Msg_r(s):  sys.stdout.write(s)
def Vmsg(s):
	if g.verbose: sys.stdout.write(s + "\n")
def Vmsg_r(s):
	if g.verbose: sys.stdout.write(s)

opts = {}
commands = {
	"strtob58":     ['<string> [str]'],
	"hextob58":     ['<hex number> [str]'],
	"b58tohex":     ['<b58 number> [str]'],
	"b58randenc":   [],
	"randhex":      ['nbytes [int=32]'],
	"randwif":      ['compressed [bool=False]'],
	"randpair":     ['compressed [bool=False]'],
	"wif2hex":      ['<wif> [str]', 'compressed [bool=False]'],
	"wif2addr":     ['<wif> [str]', 'compressed [bool=False]'],
	"hex2wif":      ['<private key in hex format> [str]', 'compressed [bool=False]'],
	"hexdump":      ['<infile> [str]', 'cols [int=8]', 'line_nums [bool=True]'],
	"unhexdump":    ['<infile> [str]'],
	"mn_rand128":   ['wordlist [str="electrum"]'],
	"mn_rand192":   ['wordlist [str="electrum"]'],
	"mn_rand256":   ['wordlist [str="electrum"]'],
	"mn_stats":     ['wordlist [str="electrum"]'],
	"mn_printlist": ['wordlist [str="electrum"]'],
	"id8":          ['<infile> [str]'],
	"id6":          ['<infile> [str]'],
	"listaddresses": ['minconf [int=1]', 'showempty [bool=False]'],
	"getbalance":   ['minconf [int=1]'],
	"viewtx":       ['<MMGen tx file> [str]'],
	"check_addrfile": ['<MMGen addr file> [str]'],
	"find_incog_data": ['<file or device name> [str]','<Incog ID> [str]','keep_searching [bool=False]'],
	"hexreverse":   ['<hexadecimal string> [str]'],
	"sha256x2":     ['<str, hexstr or filename> [str]',
					'hex_input [bool=False]','file_input [bool=False]'],
	"hexlify":      ['<string> [str]'],
	"hexaddr2addr": ['<btc address in hex format> [str]'],
	"addr2hexaddr": ['<btc address> [str]'],
	"pubkey2addr":  ['<public key in hex format> [str]'],
	"pubkey2hexaddr": ['<public key in hex format> [str]'],
	"privhex2addr": ['<private key in hex format> [str]','compressed [bool=False]'],
	"encrypt":      ['<infile> [str]','outfile [str=""]','hash_preset [str="3"]'],
	"decrypt":      ['<infile> [str]','outfile [str=""]','hash_preset [str="3"]'],
	"rand2file":    ['<outfile> [str]','<nbytes> [str]','threads [int=4]'],
	"bytespec":     ['<bytespec> [str]'],
}

command_help = """
  Bitcoin address/key operations (compressed addresses supported):
  addr2hexaddr - convert Bitcoin address from base58 to hex format
  b58randenc   - generate a random 32-byte number and convert it to base 58
  b58tohex     - convert a base 58 number to hexadecimal
  hex2wif      - convert a private key from hex to WIF format
  hexaddr2addr - convert Bitcoin address from hex to base58 format
  hextob58     - convert a hexadecimal number to base 58
  privhex2addr - generate Bitcoin address from private key in hex format
  pubkey2addr  - convert Bitcoin public key to address
  pubkey2hexaddr - convert Bitcoin public key to address in hex format
  randpair     - generate a random private key/address pair
  randwif      - generate a random private key in WIF format
  strtob58     - convert a string to base 58
  wif2addr     - generate a Bitcoin address from a key in WIF format
  wif2hex      - convert a private key from WIF to hex format

  Wallet/TX operations (bitcoind must be running):
  getbalance    - like 'bitcoind getbalance' but shows confirmed/unconfirmed,
                  spendable/unspendable balances for individual {pnm} wallets
  listaddresses - list {pnm} addresses and their balances
  viewtx        - show raw/signed {pnm} transaction in human-readable form

  General utilities:
  bytespec     - convert a byte specifier such as '1GB' into a plain integer
  hexdump      - encode data into formatted hexadecimal form (file or stdin)
  hexlify      - display string in hexadecimal format
  hexreverse   - reverse bytes of a hexadecimal string
  rand2file    - write 'n' bytes of random data to specified file
  randhex      - print 'n' bytes (default 32) of random data in hex format
  sha256x2     - compute a double sha256 hash of data
  unhexdump    - decode formatted hexadecimal data (file or stdin)

  File encryption:
  encrypt      - encrypt a file
  decrypt      - decrypt a file
    {pnm} encryption suite:
      * Key: Scrypt (user-configurable hash parameters, 32-byte salt)
      * Enc: AES256_CTR, 16-byte rand IV, sha256 hash + 32-byte nonce + data
      * The encrypted file is indistinguishable from random data

  {pnm}-specific operations:
  check_addrfile - compute checksum and address list for {pnm} address file
  find_incog_data - Use an Incog ID to find hidden incognito wallet data
  id6          - generate 6-character {pnm} ID checksum for file (or stdin)
  id8          - generate 8-character {pnm} ID checksum for file (or stdin)

  Mnemonic operations (choose "electrum" (default), "tirosh" or "all"
  wordlists):
  mn_rand128   - generate random 128-bit mnemonic
  mn_rand192   - generate random 192-bit mnemonic
  mn_rand256   - generate random 256-bit mnemonic
  mn_stats     - show stats for mnemonic wordlist
  mn_printlist - print mnemonic wordlist

  IMPORTANT NOTE: Though {pnm} mnemonics use the Electrum wordlist, they're
  computed using a different algorithm and are NOT Electrum-compatible!
""".format(pnm=g.proj_name)

def tool_usage(prog_name, command):
	print "USAGE: '%s %s%s'" % (prog_name, command,
		(" "+" ".join(commands[command]) if commands[command] else ""))

def process_args(prog_name, command, uargs):
	cargs = commands[command]
	cargs_req = [[i.split(" [")[0],i.split(" [")[1][:-1]]
		for i in cargs if "=" not in i]
	cargs_nam = dict([[
			i.split(" [")[0],
			[i.split(" [")[1].split("=")[0], i.split(" [")[1].split("=")[1][:-1]]
		] for i in cargs if "=" in i])
	uargs_req = [i for i in uargs if "=" not in i]
	uargs_nam = dict([i.split("=") for i in uargs if "=" in i])

#	print cargs_req; print cargs_nam; print uargs_req; print uargs_nam; sys.exit()

	n = len(cargs_req)
	if len(uargs_req) != n:
		tool_usage(prog_name, command)
		sys.exit(1)

	for a in uargs_nam.keys():
		if a not in cargs_nam.keys():
			print "'%s' invalid named argument" % a
			sys.exit(1)

	def test_type(arg_type,arg,name=""):
		try:
			t = type(eval(arg))
			assert(t == eval(arg_type))
		except:
			print "'%s': Invalid argument for argument %s ('%s' required)" % \
				(arg, name, arg_type)
			sys.exit(1)
		return True

	ret = []

	def normalize_arg(arg, arg_type):
		if arg_type == "bool":
			if arg.lower() in ("true","yes","1","on"): return "True"
			if arg.lower() in ("false","no","0","off"): return "False"
		return arg

	for i in range(len(cargs_req)):
		arg_type = cargs_req[i][1]
		arg = normalize_arg(uargs_req[i], arg_type)
		if arg_type == "str":
			ret.append('"%s"' % (arg))
		elif test_type(arg_type, arg, "#"+str(i+1)):
			ret.append('%s' % (arg))

	for k in uargs_nam.keys():
		arg_type = cargs_nam[k][0]
		arg = normalize_arg(uargs_nam[k], arg_type)
		if arg_type == "str":
			ret.append('%s="%s"' % (k, arg))
		elif test_type(arg_type, arg, "'"+k+"'"):
			ret.append('%s=%s' % (k, arg))

	return ret


# Individual commands

def print_convert_results(indata,enc,dec,no_recode=False):
	Vmsg("Input:         [%s]" % indata)
	Vmsg_r("Encoded data:  ["); Msg_r(enc); Vmsg_r("]"); Msg("")
	if not no_recode:
		Vmsg("Recoded data:  [%s]" % dec)
		if indata != dec:
			Msg("WARNING! Recoded number doesn't match input stringwise!")

def hexdump(infile, cols=8, line_nums=True):
	print pretty_hexdump(get_data_from_file(infile,dash=True),
			cols=cols, line_nums=line_nums)

def unhexdump(infile):
	sys.stdout.write(decode_pretty_hexdump(get_data_from_file(infile,dash=True)))

def strtob58(s):
	enc = bitcoin.b58encode(s)
	dec = bitcoin.b58decode(enc)
	print_convert_results(s,enc,dec)

def hextob58(s,f_enc=bitcoin.b58encode, f_dec=bitcoin.b58decode):
	enc = f_enc(ba.unhexlify(s))
	dec = ba.hexlify(f_dec(enc))
	print_convert_results(s,enc,dec)

def b58tohex(s,f_enc=bitcoin.b58decode, f_dec=bitcoin.b58encode):
	tmp = f_enc(s)
	if tmp == False: sys.exit(1)
	enc = ba.hexlify(tmp)
	dec = f_dec(ba.unhexlify(enc))
	print_convert_results(s,enc,dec)

def b58randenc():
	r = get_random(32,opts)
	enc = bitcoin.b58encode(r)
	dec = bitcoin.b58decode(enc)
	print_convert_results(ba.hexlify(r),enc,ba.hexlify(dec))

def randhex(nbytes='32'):
	print ba.hexlify(get_random(int(nbytes),opts))

def randwif(compressed=False):
	r_hex = ba.hexlify(get_random(32,opts))
	enc = bitcoin.hextowif(r_hex,compressed)
	print_convert_results(r_hex,enc,"",no_recode=True)

def randpair(compressed=False):
	r_hex = ba.hexlify(get_random(32,opts))
	wif = bitcoin.hextowif(r_hex,compressed)
	addr = bitcoin.privnum2addr(int(r_hex,16),compressed)
	Vmsg("Key (hex):  %s" % r_hex)
	Vmsg_r("Key (WIF):  "); Msg(wif)
	Vmsg_r("Addr:       "); Msg(addr)

def wif2addr(wif,compressed=False):
	s_enc = bitcoin.wiftohex(wif,compressed)
	if s_enc == False:
		Msg("Invalid address")
		sys.exit(1)
	addr = bitcoin.privnum2addr(int(s_enc,16),compressed)
	Vmsg_r("Addr: "); Msg(addr)

from mmgen.mnemonic import *
from mmgen.mn_electrum  import electrum_words as el
from mmgen.mn_tirosh    import tirosh_words   as tl

wordlists = sorted(wl_checksums.keys())

def get_wordlist(wordlist):
	wordlist = wordlist.lower()
	if wordlist not in wordlists:
		Msg('"%s": invalid wordlist.  Valid choices: %s' %
			(wordlist,'"'+'" "'.join(wordlists)+'"'))
		sys.exit(1)
	return el if wordlist == "electrum" else tl

def do_random_mn(nbytes,wordlist):
	r = get_random(nbytes,opts)
	wlists = wordlists if wordlist == "all" else [wordlist]
	for wl in wlists:
		l = get_wordlist(wl)
		if wl == wlists[0]: Vmsg("Seed: %s" % ba.hexlify(r))
		mn = get_mnemonic_from_seed(r,l.strip().split("\n"),
				wordlist,print_info=False)
		Vmsg("%s wordlist mnemonic:" % (wl.capitalize()))
		print " ".join(mn)

def mn_rand128(wordlist="electrum"): do_random_mn(16,wordlist)
def mn_rand192(wordlist="electrum"): do_random_mn(24,wordlist)
def mn_rand256(wordlist="electrum"): do_random_mn(32,wordlist)

def mn_stats(wordlist="electrum"):
	l = get_wordlist(wordlist)
	check_wordlist(l,wordlist)

def mn_printlist(wordlist="electrum"):
	l = get_wordlist(wordlist)
	print "%s" % l.strip()

def id8(infile): print make_chksum_8(get_data_from_file(infile,dash=True))
def id6(infile): print make_chksum_6(get_data_from_file(infile,dash=True))

# List MMGen addresses and their balances:
def listaddresses(minconf=1,showempty=False):
	from mmgen.tx import connect_to_bitcoind,trim_exponent,is_mmgen_addr
	c = connect_to_bitcoind()

	addrs = {}
	for d in c.listunspent(0):
		ma,comment = split2(d.account)
		if is_mmgen_addr(ma) and d.confirmations >= minconf:
			key = "_".join(ma.split(":"))
			if key not in addrs: addrs[key] = [0,comment]
			addrs[key][0] += d.amount

	# "bitcoind getbalance <account>" can produce a false balance
	# (sipa watchonly bitcoind), so use only for empty accounts
	if showempty:
		# Show accts with not enough confirmations as empty!
		# A feature, not a bug!
		for (ma,comment),bal in [(split2(a),c.getbalance(a,minconf=minconf))
			for a in c.listaccounts(0)]:
			if is_mmgen_addr(ma) and bal == 0:
				key = "_".join(ma.split(":"))
				if key not in addrs: addrs[key] = [0,comment]

	fs = "%-{}s  %-{}s   %s".format(
		max([len(k) for k in addrs.keys()]),
		max([len(str(addrs[k][1])) for k in addrs.keys()])
	)
	print fs % ("ADDRESS","COMMENT","BALANCE")

	def s_mmgen(ma):
		return "{}:{:>0{w}}".format(w=g.mmgen_idx_max_digits, *ma.split("_"))

	old_sid = ""
	for k in sorted(addrs.keys(),key=s_mmgen):
		sid,num = k.split("_")
		if old_sid and old_sid != sid: print
		old_sid = sid
		print fs % (sid+":"+num, addrs[k][1], trim_exponent(addrs[k][0]))


def getbalance(minconf=1):
	from mmgen.tx import connect_to_bitcoind,trim_exponent,is_mmgen_addr

	accts = {}
	for d in connect_to_bitcoind().listunspent(0):
		ma = split2(d.account)[0]
		keys = ["TOTAL"]
		if d.spendable: keys += ["SPENDABLE"]
		if is_mmgen_addr(ma): keys += [ma.split(":")[0]]
		c = d.confirmations
		i = 2 if c >= minconf else 1

		for key in keys:
			if key not in accts: accts[key] = [0,0,0]
			for j in ([0] if c == 0 else []) + [i]:
				accts[key][j] += d.amount

	fs = "{:12}  {:<%s} {:<%s} {:<}" % (16,16)
	mc,lbl = str(minconf),"confirms"
	print fs.format("Wallet","Unconfirmed",
			"<%s %s"%(mc,lbl),">=%s %s"%(mc,lbl))
	for key in sorted(accts.keys()):
		print fs.format(key+":", *[str(trim_exponent(a))+" BTC" for a in accts[key]])

def viewtx(infile):
	c = connect_to_bitcoind()
	tx_data = get_lines_from_file(infile,"transaction data")

	metadata,tx_hex,inputs_data,b2m_map = parse_tx_data(tx_data,infile)
	view_tx_data(c,inputs_data,tx_hex,b2m_map,metadata)

def check_addrfile(infile): parse_addrs_file(infile)

def hexreverse(hex_str):
	print ba.hexlify(decode_pretty_hexdump(hex_str)[::-1])

def hexlify(s):
	print ba.hexlify(s)

def sha256x2(s, file_input=False, hex_input=False):
	from hashlib import sha256
	if file_input:  b = get_data_from_file(s)
	elif hex_input: b = decode_pretty_hexdump(s)
	else:           b = s
	print sha256(sha256(b).digest()).hexdigest()

def hexaddr2addr(hexaddr):
	print bitcoin.hexaddr2addr(hexaddr)

def addr2hexaddr(addr):
	print bitcoin.verify_addr(addr,return_hex=True)

def pubkey2hexaddr(pubkeyhex):
	print bitcoin.pubhex2hexaddr(pubkeyhex)

def pubkey2addr(pubkeyhex):
	print bitcoin.pubhex2addr(pubkeyhex)

def privhex2addr(privkeyhex,compressed=False):
	print bitcoin.privnum2addr(int(privkeyhex,16),compressed)

def wif2hex(wif,compressed=False):
	print bitcoin.wiftohex(wif,compressed)

def hex2wif(hexpriv,compressed=False):
	print bitcoin.hextowif(hexpriv,compressed)

salt_len,sha256_len,nonce_len = 32,32,32

def encrypt(infile,outfile="",hash_preset=''):
	d = get_data_from_file(infile,"data for encryption")
	salt,iv,nonce = get_random(salt_len,opts),\
		get_random(g.aesctr_iv_len,opts), get_random(nonce_len,opts)
	hp,m = (hash_preset,"user-requested") if hash_preset else ('3',"default")
	qmsg("Using %s hash preset of '%s'" % (m,hp))
	passwd = get_new_passphrase("passphrase",{})
	key = make_key(passwd, salt, hp)
	from hashlib import sha256
	enc_d = encrypt_data(sha256(nonce+d).digest() + nonce + d, key,
				int(ba.hexlify(iv),16))
	if outfile == '-':  sys.stdout.write(salt+iv+enc_d)
	else:
		if not outfile:
			outfile = os.path.basename(infile) + "." + g.mmenc_ext
		write_to_file(outfile, salt+iv+enc_d, opts,"encrypted data",True,True)

def decrypt(infile,outfile="",hash_preset=''):
	d = get_data_from_file(infile,"encrypted data")
	dstart = salt_len + g.aesctr_iv_len
	salt,iv,enc_d = d[:salt_len],d[salt_len:dstart],d[dstart:]
	hp,m = (hash_preset,"user-requested") if hash_preset else ('3',"default")
	qmsg("Using %s hash preset of '%s'" % (m,hp))
	passwd = get_mmgen_passphrase("Enter passphrase: ",{})
	key = make_key(passwd, salt, hp)
	dec_d = decrypt_data(enc_d, key, int(ba.hexlify(iv),16))
	from hashlib import sha256
	if dec_d[:sha256_len] == sha256(dec_d[sha256_len:]).digest():
		out = dec_d[sha256_len+nonce_len:]
		if outfile == '-':  sys.stdout.write(out)
		else:
			if not outfile:
				outfile = os.path.basename(infile)
				if outfile[-len(g.mmenc_ext)-1:] == "."+g.mmenc_ext:
					outfile = outfile[:-len(g.mmenc_ext)-1]
				else:
					outfile = outfile + ".dec"
			write_to_file(outfile, out, opts,"decrypted data",True,True)
	else:
		msg("Incorrect passphrase or hash preset")


def find_incog_data(filename,iv_id,keep_searching=False):
	ivsize,bsize,mod = g.aesctr_iv_len,4096,4096*8
	n,carry = 0," "*ivsize
	f = os.open(filename,os.O_RDONLY)
	while True:
		d = os.read(f,bsize)
		if not d: break
		d = carry + d
		for i in range(bsize):
			if sha256(d[i:i+ivsize]).hexdigest()[:8].upper() == iv_id:
				if n+i < ivsize: continue
				msg("\rIncog data for ID %s found at offset %s" %
					(iv_id,n+i-ivsize))
				if not keep_searching: sys.exit(0)
		carry = d[len(d)-ivsize:]
		n += bsize
		if not n % mod: msg_r("\rSearched: %s bytes" % n)

	msg("")
	os.close(f)

# From "man dd":
# c=1, w=2, b=512, kB=1000, K=1024, MB=1000*1000, M=1024*1024,
# GB=1000*1000*1000, G=1024*1024*1024, and so on for T, P, E, Z, Y.

def parse_nbytes(nbytes):
	import re
	m = re.match(r'([0123456789]+)(.*)',nbytes)
	smap = ("c",1),("w",2),("b",512),("kB",1000),("K",1024),("MB",1000*1000),\
			("M",1024*1024),("GB",1000*1000*1000),("G",1024*1024*1024)
	if m:
		if m.group(2):
			for k,v in smap:
				if k == m.group(2):
					return int(m.group(1)) * v
			else:
				msg("Valid byte specifiers: '%s'" % "' '".join([i[0] for i in smap]))
		else:
			return int(nbytes)

	msg("'%s': invalid byte specifier" % nbytes)
	sys.exit(1)


def rand2file(outfile, nbytes, threads=4):
	nbytes = parse_nbytes(nbytes)
	from Crypto import Random
	rh = Random.new()
	from Queue import Queue
	from threading import Thread
	bsize = 2**20
	roll = bsize * 4
	if 'outdir' in opts: outfile = make_full_path(opts['outdir'],outfile)
	f = open(outfile,"w")

	from Crypto.Cipher import AES
	from Crypto.Util import Counter

	key = get_random(32,opts)

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
			msg_r("\rRead: %s bytes" % (bsize*i))

	msg("\rRead: %s bytes" % nbytes)
	qmsg("\r%s bytes written to file '%s'" % (nbytes,outfile))
	q1.join()
	q2.join()
	f.close()

def bytespec(s): print parse_nbytes(s)
