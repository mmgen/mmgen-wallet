#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C) 2013 by philemon <mmgen-py@yandex.com>
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
utils.py:  Shared routines for the mmgen suite
"""

import sys
from mmgen.config import *
from binascii import hexlify,unhexlify
from mmgen.bitcoin import b58decode_pad

def msg(s):   sys.stderr.write(s + "\n")
def msg_r(s): sys.stderr.write(s)

def bail(): sys.exit(9)

def my_getpass(prompt):

	from getpass import getpass
	# getpass prompts to stderr, so no trickery required as with raw_input()
	try: pw = getpass(prompt)
	except:
		msg("\nUser interrupt")
		sys.exit(1)

	return pw

def get_char(prompt):

	import os
	msg_r(prompt)
	os.system(
"stty -icanon min 1 time 0 -echo -echoe -echok -echonl -crterase noflsh"
	)
	try: ch = sys.stdin.read(1)
	except:
		os.system("stty sane")
		msg("\nUser interrupt")
		sys.exit(1)
	else:
		os.system("stty sane")

	return ch


def my_raw_input(prompt):

	msg_r(prompt)
	try: reply = raw_input()
	except:
		msg("\nUser interrupt")
		sys.exit(1)

	return reply


def _get_hash_params(hash_preset):
	if hash_preset in hash_presets:
		return hash_presets[hash_preset] # N,p,r,buflen
	else:
		# Shouldn't be here
		msg("%s: invalid 'hash_preset' value" % hash_preset)
		sys.exit(3)

def show_hash_presets():
	fs = "  {:<7} {:<6} {:<3}  {}"
	msg("Available parameters for scrypt.hash():")
	msg(fs.format("Preset","N","r","p"))
	for i in sorted(hash_presets.keys()):
		msg(fs.format("'%s'" % i, *hash_presets[i]))
	msg("N = memory usage (power of two), p = iterations (rounds)")
	sys.exit(0)


def check_opts(opts,keys):

	for key in keys:
		if key not in opts: continue

		val = opts[key]
		what = "parameter for '--%s' option" % key.replace("_","-")

		if key == 'outdir':
			what = "output directory"
			import re, os, stat
			d = re.sub(r'/*$','', val)
			opts[key] = d

			try: mode = os.stat(d).st_mode
			except:
				msg("Unable to stat requested %s '%s'.  Aborting" % (what,d))
				sys.exit(1)

			if not stat.S_ISDIR(mode):
				msg("Requested %s '%s' is not a directory.  Aborting" %(what,d))
				sys.exit(1)

			if not os.access(d, os.W_OK|os.X_OK):
				msg("Requested %s '%s' is unwritable by you. Aborting"%(what,d))
				sys.exit(1)

		elif key == 'label':
			label = val.strip()
			opts[key] = label

			if len(label) > 32:
				msg("Label must be 32 characters or less")
				sys.exit(1)

			from string import ascii_letters, digits
			label_chrs = list(ascii_letters + digits) + [".", "_", " "]
			for ch in list(label):
				if ch not in label_chrs:
					msg("'%s': illegal character in label" % ch)
					sys.exit(1)

		elif key == 'from_brain':
			try:
				l,p = val.split(",")
			except:
				msg("'%s': invalid %s" % (val,what))
				sys.exit(1)

			try:
				int(l)
			except:
				msg("'%s': invalid 'l' %s (not an integer)" % (l,what))
				sys.exit(1)

			if int(l) not in seed_lens:
				msg("'%s': invalid 'l' %s.  Options: %s" % 
						(l, what, ", ".join([str(i) for i in seed_lens])))
				sys.exit(1)

			if p not in hash_presets:
				hps = ", ".join([i for i in sorted(hash_presets.keys())])
				msg("'%s': invalid 'p' %s.  Options: %s" % (p, what, hps))
				sys.exit(1)
		elif key == 'seed_len':
			if val not in seed_lens:
				msg("'%s': invalid %s.  Options: %s"
				% (val,what,", ".join([str(i) for i in seed_lens])))
				sys.exit(2)
		elif key == 'hash_preset':
			if val not in hash_presets:
				msg("'%s': invalid %s.  Options: %s"
				% (val,what,", ".join(sorted(hash_presets.keys()))))
				sys.exit(2)
		elif key == 'usr_randlen':
			if val > max_randlen or val < min_randlen:
				msg("'%s': invalid %s (must be >= %s and <= %s)"
				% (val,what,min_randlen,max_randlen))
				sys.exit(2)


cmessages = {
	'null': "",
	'unencrypted_secret_keys': """
This program generates secret keys from your {} seed, outputting them in
UNENCRYPTED form.  Generate only the key(s) you need and guard them carefully.
""".format(proj_name),
	'brain_warning': """
############################## EXPERTS ONLY! ##############################

A brainwallet will be secure only if you really know what you're doing and
have put much care into its creation.  {} assumes no responsibility for
coins stolen as a result of a poorly crafted brainwallet passphrase.

A key will be generated from your passphrase using the parameters requested
by you: seed length {}, hash preset '{}'.  For brainwallets it's highly
recommended to use one of the higher-numbered presets

Remember the seed length and hash preset parameters you've specified.  To
generate the correct keys/addresses associated with this passphrase in the
future, you must continue using these same parameters
"""
}

def confirm_or_exit(message, question, expect="YES"):

	msg("")

	m = message.strip()
	if m: msg(m)

	conf_msg = "Type uppercase '%s' to confirm: " % expect

	if question[0].isupper():
		prompt = question + "  " + conf_msg
	else:
		prompt = "Are you sure you want to %s?\n%s" % (question,conf_msg)

	if my_raw_input(prompt).strip() != expect:
		msg("Exiting at user request")
		sys.exit(2)

	msg("")


def user_confirm(prompt,default_yes=False):

	q = "(Y/n)" if default_yes else "(y/N)"

	while True:
		reply = get_char("%s %s: " % (prompt, q)).strip()
		msg("")

		if not reply:
			return True if default_yes else False
		elif reply in 'yY': return True
		elif reply in 'nN': return False
		else: msg("Invalid reply")


def set_if_unset_and_typeconvert(opts,item):

	for opt,var,dtype in item:
		if   dtype == 'int': f,s = int,"an integer"
		elif dtype == 'str': f,s = str,"a string"

		if opt in opts:
			val = opts[opt]
			what = "invalid parameter for '--%s' option" % opt.replace("_","-")
			try:
				f(val)
			except:
				msg("'%s': %s (not %s)" % (val,what,s))
				sys.exit(1)
			opts[opt] = f(val)
		else:
			opts[opt] = var


def make_chksum_8(s):
	from hashlib import sha256
	return sha256(sha256(s).digest()).hexdigest()[:8].upper()

def make_chksum_6(s):
	from hashlib import sha256
	return sha256(s).hexdigest()[:6]


def _get_from_brain_opt_params(opts):
	l,p = opts['from_brain'].split(",")
	return(int(l),p)


def check_infile(f):

	import os, stat

	try: mode = os.stat(f).st_mode
	except:
		msg("Unable to stat requested input file '%s'.  Aborting" % f)
		sys.exit(1)

	if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
		msg("Requested input file '%s' is not a file.  Aborting" % f)
		sys.exit(1)

	if not os.access(f, os.R_OK):
		msg("Requested input file '%s' is unreadable by you.  Aborting" % f)
		sys.exit(1)


def parse_address_range(arg):

	import re
	m = re.match(r'^(\d+)(-(\d+))*$', arg)

	if m == None:
		msg(arg + ": invalid argument for address range")
		sys.exit(2)

	start,end = int(m.group(1)), int(m.group(3) or m.group(1))

	if start < 1:
		msg(args + ": First address must be >= 1")
		sys.exit(2)

	if end < start:
		msg(arg + ": Last address must be >= first address")
		sys.exit(2)

	return start,end


def get_first_passphrase_from_user(what, opts):
	"""
	Prompt the user for a passphrase and return it

	Supported options: echo_passphrase
	"""

	if not 'quiet' in opts:
		msg("""
Now you must choose a passphrase to encrypt the seed with.  A key will be
generated from your passphrase using a hash preset of '%s'.  Please note that
no strength checking of passphrases is performed.  For an empty passphrase,
just hit ENTER twice.
""" % opts['hash_preset'])

	if 'echo_passphrase' in opts:
		ret = " ".join(_get_words_from_user(opts,"Enter %s: " % what))
		if ret == "": msg("Empty passphrase")
		return ret

	for i in range(passwd_max_tries):
		ret  = " ".join(_get_words_from_user(opts,"Enter %s: " % what))
		ret2 = " ".join(_get_words_from_user(opts,"Repeat %s: " % what))
		if debug: print "Passphrases: [%s] [%s]" % (ret,ret2)
		if ret2 == ret:
			s = " (empty)" if not len(ret) else ""
			msg("%ss match%s" % (what.capitalize(),s))
			return ret
		else:
			msg("%ss do not match" % what.capitalize())

	msg("User failed to duplicate passphrase in %s attempts" % passwd_max_tries)
	sys.exit(2)


def _scrypt_hash_passphrase(passwd, salt, hash_preset, buflen=32):

	N,r,p = _get_hash_params(hash_preset)

	import scrypt
	return scrypt.hash(passwd, salt, 2**N, r, p, buflen=buflen)


def _get_seed_from_brain_passphrase(words,opts):
	bp = " ".join(words)
	if debug: print "Sanitized brain passphrase: %s" % bp
	seed_len,hash_preset = _get_from_brain_opt_params(opts)
	if debug: print "Brainwallet l = %s, p = %s" % (seed_len,hash_preset)
	msg_r("Hashing brainwallet data.  Please wait...")
	# Use buflen arg of scrypt.hash() to get seed of desired length
	seed = _scrypt_hash_passphrase(bp, "", hash_preset, buflen=seed_len/8)
	msg("Done")
	return seed


def encrypt_seed(seed, key, opts):
	"""
	Encrypt a seed for a {} deterministic wallet
	""".format(proj_name)

	# 192-bit seed is 24 bytes -> not multiple of 16.  Must use MODE_CTR
	from Crypto.Cipher import AES
	from Crypto.Util import Counter

	c = AES.new(key, AES.MODE_CTR,counter=Counter.new(128))
	enc_seed = c.encrypt(seed)

	msg_r("Performing a test decryption of the seed...")

	c = AES.new(key, AES.MODE_CTR,counter=Counter.new(128))
	dec_seed = c.decrypt(enc_seed)

	if dec_seed == seed: msg("done")
	else:
		msg("FAILED.\nDecrypted seed doesn't match original seed.  Aborting.")
		sys.exit(2)

	return enc_seed


def	write_to_stdout(data, what, confirm=True):
	if sys.stdout.isatty() and confirm:
		confirm_or_exit("",'output {} to screen'.format(what))
	elif not sys.stdout.isatty():
		import os
		of = os.readlink("/proc/%d/fd/1" % os.getpid())
		msg("Writing data to file '%s'" % of)
	sys.stdout.write(data)


def get_default_wordlist():

	wl_id = default_wl
	if wl_id == "electrum": from mmgen.mn_electrum import electrum_words as wl
	elif wl_id == "tirosh": from mmgen.mn_tirosh   import tirosh_words as wl
	return wl.strip().split("\n")


def open_file_or_exit(filename,mode):
	try:
		f = open(filename, mode)
	except:
		what = "reading" if mode == 'r' else "writing"
		msg("Unable to open file '%s' for %s" % (infile,what))
		sys.exit(2)
	return f


def write_to_file(outfile,data,confirm=False):

	if confirm:
		from os import stat
		try:
			stat(outfile)
		except:
			pass
		else:
			confirm_or_exit("","File '%s' already exists\nOverwrite?" % outfile)

	f = open_file_or_exit(outfile,'w')

	try:
		f.write(data)
	except:
		msg("Failed to write to file '%s'" % outfile)
		sys.exit(2)

	f.close


def write_seed(seed, opts):

	outfile = "%s.%s" % (make_chksum_8(seed).upper(),seed_ext)
	if 'outdir' in opts:
		outfile = "%s/%s" % (opts['outdir'], outfile)

	from mmgen.bitcoin import b58encode_pad
	data = col4(b58encode_pad(seed))
	chk = make_chksum_6(b58encode_pad(seed))

	o = "%s %s\n" % (chk,data)

	if 'stdout' in opts:
		write_to_stdout(o,"seed data",confirm=True)
	elif not sys.stdout.isatty():
		write_to_stdout(o,"seed data",confirm=False)
	else:
		write_to_file(outfile,o)
		msg("%s data saved to file '%s'" % ("Seed",outfile))


def write_mnemonic(mn, seed, opts):

	outfile = "%s.words" % make_chksum_8(seed).upper()
	if 'outdir' in opts:
		outfile = "%s/%s" % (opts['outdir'], outfile)

	o = " ".join(mn) + "\n"

	if 'stdout' in opts:
		write_to_stdout(o,"mnemonic data",confirm=True)
	elif not sys.stdout.isatty():
		write_to_stdout(o,"mnemonic data",confirm=False)
	else:
		write_to_file(outfile,o)
		msg("%s data saved to file '%s'" % ("Mnemonic",outfile))


def _display_control_data(label,metadata,hash_preset,salt,enc_seed):
	msg("WALLET DATA")
	fs = "  {:25} {}"
	pw_empty = "yes" if metadata[3] == "E" else "no"
	from mmgen.bitcoin import b58encode_pad
	for i in (
		("Label:",               label),
		("Seed ID:",             metadata[0]),
		("Key  ID:",             metadata[1]),
		("Seed length:",         metadata[2]),
		("Scrypt hash params:",  "Preset '%s' (%s)" % (hash_preset,
			" ".join([str(i) for i in _get_hash_params(hash_preset)]))),
		("Passphrase is empty:", pw_empty),
		("Timestamp:",           "%s UTC" % metadata[4]),
		("Salt:",                b58encode_pad(salt)),
		("Encrypted seed:",      b58encode_pad(enc_seed))
	): msg(fs.format(*i))


def col4(s):
	nondiv = 1 if len(s) % 4 else 0
	return " ".join([s[4*i:4*i+4] for i in range(len(s)/4 + nondiv)])

def make_timestamp():
	import time
	tv = time.gmtime(time.time())[:6]
	return "{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(*tv)

def write_wallet_to_file(seed, passwd, key_id, salt, enc_seed, opts):

	seed_id = make_chksum_8(seed)
	seed_len = str(len(seed)*8)
	pw_status = "NE" if len(passwd) else "E"

	hash_preset = opts['hash_preset']

	outfile = "{}-{}[{},{}].dat".format(seed_id,key_id,seed_len,hash_preset)
	if 'outdir' in opts:
		outfile = "%s/%s" % (opts['outdir'], outfile)

	label = opts['label'] if 'label' in opts else "None"

	from mmgen.bitcoin import b58encode_pad

	sf  = b58encode_pad(salt)
	esf = b58encode_pad(enc_seed)

	metadata = seed_id.lower(),key_id.lower(),\
		seed_len,pw_status,make_timestamp()

	lines = (
		label,
		"{} {} {} {} {}".format(*metadata),
		"{}: {} {} {}".format(hash_preset,*_get_hash_params(hash_preset)),
		"{} {}".format(make_chksum_6(sf),  col4(sf)),
		"{} {}".format(make_chksum_6(esf), col4(esf))
	)

	chk = make_chksum_6(" ".join(lines))

	confirm = False if 'quiet' in opts else True
	write_to_file(outfile, "\n".join((chk,)+lines)+"\n", confirm)

	msg("Wallet saved to file '%s'" % outfile)
	if 'verbose' in opts:
		_display_control_data(label,metadata,hash_preset,salt,enc_seed)


def	compare_checksums(chksum1, desc1, chksum2, desc2):

	if chksum1.lower() == chksum2.lower():
		msg("OK (%s)" % chksum1.upper())
		return True
	else:
		msg("ERROR!\nComputed checksum %s (%s) doesn't match checksum %s (%s)" \
			% (desc1,chksum1,desc2,chksum2))
		return False

def _is_hex(s):
	try: int(s,16)
	except: return False
	else: return True


def	check_mmseed_format(words):

	valid = False
	what = "%s data" % seed_ext
	chklen = len(words[0])

	if len(words) < 3 or len(words) > 12:
		msg("Invalid data length (%s) in %s" % (len(words),what))
	elif not _is_hex(words[0]):
		msg("Invalid format of checksum '%s' in %s"%(words[0], what))
	elif chklen != 6:
		msg("Incorrect length of checksum (%s) in %s" % (chklen,what))
	else: valid = True

	if valid == False:
		msg("Invalid %s data" % seed_ext)
		sys.exit(3)


def	check_wallet_format(infile, lines, opts):

	def vmsg(s):
		if 'verbose' in opts: msg(s)

	what = "wallet file '%s'" % infile
	valid = False
	chklen = len(lines[0])
	if len(lines) != 6:
		vmsg("Invalid number of lines (%s) in %s" % (len(lines),what))
	elif chklen != 6:
		vmsg("Incorrect length of Master checksum (%s) in %s" % (chklen,what))
	elif not _is_hex(lines[0]):
		vmsg("Invalid format of Master checksum '%s' in %s"%(lines[0], what))
	else: valid = True

	if valid == False:
		msg("Invalid %s" % what)
		sys.exit(2)


def _check_chksum_6(chk,val,desc,infile):
	comp_chk = make_chksum_6(val)
	if chk != comp_chk:
		msg("%s checksum incorrect in file '%s'!" % (desc,infile))
		msg("Checksum: %s. Computed value: %s" % (chk,comp_chk))
		sys.exit(2)
	elif debug:
		msg("%s checksum passed: %s" % (desc.capitalize(),chk))


def get_data_from_wallet(infile,opts):

	msg("Getting {} wallet data from file '{}'".format(proj_name,infile))

	f = open_file_or_exit(infile, 'r')

	lines = [i.strip() for i in f.readlines()]
	f.close()

	check_wallet_format(infile, lines, opts)

	label = lines[1]

	metadata = lines[2].split()

	for i in 0,1: metadata[i] = metadata[i].upper()

	hd = lines[3].split()
	hash_preset = hd[0][:-1]
	hash_params = [int(i) for i in hd[1:]]

	if hash_params != _get_hash_params(hash_preset):
		msg("Hash parameters '%s' don't match hash preset '%s'" %
				(" ".join(hash_params), hash_preset))
		sys.exit(9)

	res = {}
	for i,key in (4,"salt"),(5,"enc_seed"):
		l = lines[i].split()
		val = "".join(l[1:])
		_check_chksum_6(l[0], val, key, infile)
		res[key] = b58decode_pad(val)
		if res[key] == False:
			msg("Invalid b58 number: %s" % val)
			sys.exit(9)

	_check_chksum_6(lines[0], " ".join(lines[1:]), "Master", infile)

	return label,metadata,hash_preset,res['salt'],res['enc_seed']


def _get_words_from_user(opts, prompt):
	# split() also strips
	if 'echo_passphrase' in opts:
		return my_raw_input(prompt).split()
	else:
		return my_getpass(prompt).split()


def _get_words_from_file(infile,what):
	msg("Getting %s from file '%s'" % (what,infile))
	f = open_file_or_exit(infile, 'r')
	data = f.read(); f.close()
	# split() also strips
	return data.split()


def get_lines_from_file(infile,what):
	msg("Getting %s from file '%s'" % (what,infile))
	f = open_file_or_exit(infile,'r')
	lines = f.readlines(); f.close()
	return [i.strip("\n") for i in lines]


def get_words(infile,what,prompt,opts):
	if infile:
		words = _get_words_from_file(infile,what)
	else:
		words = _get_words_from_user(opts,prompt)
	if debug: print "Sanitized input: [%s]" % " ".join(words)
	return words


def get_seed_from_seed_data(words):

	check_mmseed_format(words)

	stored_chk = words[0]
	seed_b58 = "".join(words[1:])

	chk = make_chksum_6(seed_b58)
	msg_r("Validating %s checksum..." % seed_ext)

	if compare_checksums(chk, "from seed", stored_chk, "from input"):
		seed = b58decode_pad(seed_b58)
		if seed == False:
			msg("Invalid b58 number: %s" % val)
			sys.exit(9)

		msg("%s data produces seed ID: %s" % (seed_ext,make_chksum_8(seed)))
		return seed
	else:
		msg("Invalid checksum for {} seed".format(proj_name))
		sys.exit(9)


def get_seed_from_wallet(infile,opts,
		prompt="Enter {} wallet passphrase: ".format(proj_name)):

	wdata = get_data_from_wallet(infile,opts)
	label,metadata,hash_preset,salt,enc_seed = wdata

	if 'verbose' in opts: _display_control_data(*wdata)

	passwd = " ".join(get_words("","",prompt,opts))

	key = make_key(passwd, salt, hash_preset)

	return decrypt_seed(enc_seed, key, metadata[0], metadata[1])


def make_key(passwd, salt, hash_preset):

	msg_r("Hashing passphrase.  Please wait...")
	key = _scrypt_hash_passphrase(passwd, salt, hash_preset)
	msg("done")
	return key


def decrypt_seed(enc_seed, key, seed_id, key_id):

	msg_r("Checking key...")
	chk = make_chksum_8(key)
	if not compare_checksums(chk, "of key", key_id, "in header"):
		msg("Passphrase incorrect?")
		sys.exit(3)

	msg_r("Decrypting seed with key...")

	from Crypto.Cipher import AES
	from Crypto.Util import Counter

	c = AES.new(key, AES.MODE_CTR,counter=Counter.new(128))
	dec_seed = c.decrypt(enc_seed)

	chk = make_chksum_8(dec_seed)
	if compare_checksums(chk,"of decrypted seed",seed_id,"in header"):
		msg("Passphrase is OK")
	else:
		if not debug:
			msg_r("Checking key ID...")
			chk = make_chksum_8(key)
			if compare_checksums(chk, "of key", key_id, "in header"):
				msg("Key ID is correct but decryption of seed failed")
			else:
				msg("Incorrect passphrase")

		sys.exit(3)

	if debug: msg("key: %s" % hexlify(key))

	return dec_seed


def get_seed(infile,opts,no_wallet=False):
	if 'from_mnemonic' in opts:
		prompt = "Enter mnemonic: "
		words = get_words(infile,"mnemonic data",prompt,opts)

		wl = get_default_wordlist()
		from mmgen.mnemonic import get_seed_from_mnemonic
		return get_seed_from_mnemonic(words,wl)
	elif 'from_brain' in opts:
		msg("")
		if 'quiet' not in opts:
			confirm_or_exit(
				cmessages['brain_warning'].format(
					proj_name.capitalize(),
					*_get_from_brain_opt_params(opts)),
			"continue")
		prompt = "Enter brainwallet passphrase: "
		words = get_words(infile,"brainwallet data",prompt,opts)
		return _get_seed_from_brain_passphrase(words,opts)
	elif 'from_seed' in opts:
		prompt = "Enter seed in %s format: " % seed_ext
		words = get_words(infile,"seed data",prompt,opts)
		return get_seed_from_seed_data(words)
	elif no_wallet:
		return False
	else:
		return get_seed_from_wallet(infile, opts)

def remove_blanks_comments(lines):
	import re
#	re.sub(pattern, repl, string, count=0, flags=0)
	ret = []
	for i in lines:
		i = re.sub('#.*','',i,1)
		i = re.sub('\s+$','',i)
		if i: ret.append(i)

	return ret

def parse_addrs_file(f):
	lines = get_lines_from_file(f,"address data")
	lines = remove_blanks_comments(lines)

	seed_id,obrace = lines[0].split()
 	cbrace = lines[-1]

	if   obrace != '{':
		msg("'%s': invalid first line" % lines[0])
	elif cbrace != '}':
		msg("'%s': invalid last line" % cbrace)
	elif len(seed_id) != 8:
		msg("'%s': invalid Seed ID" % seed_id)
	else:
		try:
			unhexlify(seed_id)
		except:
			msg("'%s': invalid Seed ID" % seed_id)
			sys.exit(3)
		
		ret = []
		for i in lines[1:-1]:
			d = i.split()

			try: d[0] = int(d[0])
			except:
				msg("'%s': invalid address num. in line: %s" % (d[0],d))
				sys.exit(3)

			from mmgen.bitcoin import verify_addr
			if not verify_addr(d[1]):
				msg("'%s': invalid address" % d[1])
				sys.exit(3)

			ret.append(d)

		return seed_id,ret

	sys.exit(3)





if __name__ == "__main__":
	print get_lines_from_file("/tmp/lines","test file")
