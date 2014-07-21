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
util.py:  Shared routines for the mmgen suite
"""

import sys
import mmgen.config as g
from binascii import hexlify,unhexlify
from mmgen.bitcoin import b58decode_pad
from mmgen.term import *

def msg(s):    sys.stderr.write(s + "\n")
def msg_r(s):  sys.stderr.write(s)
def qmsg(s,alt=""):
	if g.quiet:
		if alt: sys.stderr.write(alt + "\n")
	else: sys.stderr.write(s + "\n")
def qmsg_r(s,alt=""):
	if g.quiet:
		if alt: sys.stderr.write(alt)
	else: sys.stderr.write(s)
def vmsg(s):
	if g.verbose: sys.stderr.write(s + "\n")
def vmsg_r(s):
	if g.verbose: sys.stderr.write(s)

def bail(): sys.exit(9)

def get_extension(f):
	try: return f.split(".")[-1]
	except: return ""

def my_raw_input(prompt,echo=True,allowed_chars=""):
	try:
		if echo:
			reply = raw_input(prompt)
		else:
			from getpass import getpass
			reply = getpass(prompt)
	except KeyboardInterrupt:
		msg("\nUser interrupt")
		sys.exit(1)

	kb_hold_protect()
	return reply


def my_raw_input_old(prompt,echo=True,allowed_chars=""):

	msg_r(prompt)
	reply = ""

	while True:
		ch = get_char(immed_chars="ALL_EXCEPT_ENTER")
		if allowed_chars and ch not in allowed_chars+"\n\r\b"+chr(0x7f):
			continue
		if echo:
			if ch in "\b"+chr(0x7f): # WIP
				pass
				# reply.pop(0)
			else: msg_r(ch)
		if ch in "\n\r":
			if not echo: msg("")
			break
		reply += ch

	return reply


def _get_hash_params(hash_preset):
	if hash_preset in g.hash_presets:
		return g.hash_presets[hash_preset] # N,p,r,buflen
	else:
		# Shouldn't be here
		msg("%s: invalid 'hash_preset' value" % hash_preset)
		sys.exit(3)


def show_hash_presets():
	fs = "  {:<7} {:<6} {:<3}  {}"
	msg("Available parameters for scrypt.hash():")
	msg(fs.format("Preset","N","r","p"))
	for i in sorted(g.hash_presets.keys()):
		msg(fs.format("'%s'" % i, *g.hash_presets[i]))
	msg("N = memory usage (power of two), p = iterations (rounds)")
	sys.exit(0)


cmessages = {
	'null': "",
	'incog_iv_id': """
   If you know your IV ID, check it against the value above.  If it's
   incorrect, then your incognito data is invalid.
""",
	'incog_iv_id_hidden': """
   If you know your IV ID, check it against the value above.  If it's
   incorrect, then your incognito data is invalid or you've supplied
   an incorrect offset.
""",
	'incog_key_id': """
   Check that the generated seed ID is correct.  If it's not, then your
   password or hash preset is incorrect or incognito data is corrupted.
""",
	'incog_key_id_hidden': """
   Check that the generated seed ID is correct.  If it's not, then your
   password or hash preset is incorrect or incognito data is corrupted.
   If the key ID is correct but the seed ID is not, then you might have
   chosen an incorrect seed length.
""",
	'unencrypted_secret_keys': """
This program generates secret keys from your {} seed, outputting them in
UNENCRYPTED form.  Generate only the key(s) you need and guard them carefully.
""".format(g.proj_name_cap),
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

	vmsg("")

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

	vmsg("")


def user_confirm(prompt,default_yes=False,verbose=False):

	q = "(Y/n)" if default_yes else "(y/N)"

	while True:
		reply = get_char("%s %s: " % (prompt, q)).strip("\n\r")

		if not reply:
			if default_yes: msg(""); return True
			else:           msg(""); return False
		elif reply in 'yY': msg(""); return True
		elif reply in 'nN': msg(""); return False
		else:
			if verbose: msg("\nInvalid reply")
			else: msg_r("\r")


def prompt_and_get_char(prompt,chars,enter_ok=False,verbose=False):

	while True:
		reply = get_char("%s: " % prompt).strip("\n\r")

		if reply in chars or (enter_ok and not reply):
			msg("")
			return reply

		if verbose: msg("\nInvalid reply")
		else: msg_r("\r")


def make_chksum_8(s):
	from hashlib import sha256
	return sha256(sha256(s).digest()).hexdigest()[:8].upper()

def make_chksum_6(s):
	from hashlib import sha256
	return sha256(s).hexdigest()[:6]


def check_infile(f):

	import os, stat

	try: mode = os.stat(f).st_mode
	except:
		msg("Unable to stat requested input file '%s'" % f)
		sys.exit(1)

	if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
		msg("Requested input file '%s' is not a file" % f)
		sys.exit(1)

	if not os.access(f, os.R_OK):
		msg("Requested input file '%s' is unreadable by you" % f)
		sys.exit(1)


def _validate_addr_num(n):

	try: n = int(n)
	except:
		msg("'%s': invalid argument for address" % n)
		return False

	if n < 1:
		msg("'%s': address must be greater than zero" % n)
		return False

	return n


def parse_address_list(arg,sep=","):

	ret = []

	for i in (arg.split(sep)):

		j = i.split("-")

		if len(j) == 1:
			i = _validate_addr_num(i)
			if not i: return False
			ret.append(i)
		elif len(j) == 2:
			beg = _validate_addr_num(j[0])
			if not beg: return False
			end = _validate_addr_num(j[1])
			if not end: return False
			if end < beg:
				msg("'%s-%s': end of range less than beginning" % (beg,end))
				return False
			for k in range(beg,end+1): ret.append(k)
		else:
			msg("'%s': invalid argument for address range" % i)
			return False

	return sorted(set(ret))


def get_new_passphrase(what, opts):

	if 'passwd_file' in opts:
		pw = " ".join(_get_words_from_file(opts['passwd_file'],what))
	elif 'echo_passphrase' in opts:
		pw = " ".join(_get_words_from_user(("Enter %s: " % what), opts))
	else:
		for i in range(g.passwd_max_tries):
			pw = " ".join(_get_words_from_user(("Enter %s: " % what),opts))
			pw2 = " ".join(_get_words_from_user(("Repeat %s: " % what),opts))
			if g.debug: print "Passphrases: [%s] [%s]" % (pw,pw2)
			if pw == pw2:
				vmsg("%ss match" % what.capitalize())
				break
			else:
				msg("%ss do not match" % what.capitalize())
		else:
			msg("User failed to duplicate passphrase in %s attempts" %
					g.passwd_max_tries)
			sys.exit(2)

	if pw == "": qmsg("WARNING: Empty passphrase")
	return pw


def _scrypt_hash_passphrase(passwd, salt, hash_preset, buflen=32):

	# Buflen arg is for brainwallets only, which use this function to generate
	# the seed directly.

	N,r,p = _get_hash_params(hash_preset)

	import scrypt
	return scrypt.hash(passwd, salt, 2**N, r, p, buflen=buflen)


def _get_from_brain_opt_params(opts):
	l,p = opts['from_brain'].split(",")
	return(int(l),p)


def _get_seed_from_brain_passphrase(words,opts):
	bp = " ".join(words)
	if g.debug: print "Sanitized brain passphrase: %s" % bp
	seed_len,hash_preset = _get_from_brain_opt_params(opts)
	if g.debug: print "Brainwallet l = %s, p = %s" % (seed_len,hash_preset)
	vmsg_r("Hashing brainwallet data.  Please wait...")
	# Use buflen arg of scrypt.hash() to get seed of desired length
	seed = _scrypt_hash_passphrase(bp, "", hash_preset, buflen=seed_len/8)
	vmsg("Done")
	return seed


def encrypt_seed(seed, key, iv=1):
	"""
	Encrypt a seed for an {} deterministic wallet
	""".format(g.proj_name_cap)

	# 192-bit seed is 24 bytes -> not multiple of 16.  Must use MODE_CTR
	from Crypto.Cipher import AES
	from Crypto.Util import Counter

	c = AES.new(key, AES.MODE_CTR,
			counter=Counter.new(g.aesctr_iv_len*8,initial_value=iv))
	enc_seed = c.encrypt(seed)

	vmsg_r("Performing a test decryption of the seed...")

	c = AES.new(key, AES.MODE_CTR,
			counter=Counter.new(g.aesctr_iv_len*8,initial_value=iv))
	dec_seed = c.decrypt(enc_seed)

	if dec_seed == seed: vmsg("done")
	else:
		msg("ERROR.\nDecrypted seed doesn't match original seed")
		sys.exit(2)

	return enc_seed


def write_to_stdout(data, what, confirm=True):
	if sys.stdout.isatty() and confirm:
		confirm_or_exit("",'output {} to screen'.format(what))
	elif not sys.stdout.isatty():
		try:
			import os
			of = os.readlink("/proc/%d/fd/1" % os.getpid())
			msg("Redirecting output to file '%s'" % of)
		except:
			msg("Redirecting output to file")
	sys.stdout.write(data)


def get_default_wordlist():

	wl_id = g.default_wl
	if wl_id == "electrum": from mmgen.mn_electrum import electrum_words as wl
	elif wl_id == "tirosh": from mmgen.mn_tirosh   import tirosh_words as wl
	return wl.strip().split("\n")


def open_file_or_exit(filename,mode):
	try:
		f = open(filename, mode)
	except:
		what = "reading" if mode == 'r' else "writing"
		msg("Unable to open file '%s' for %s" % (filename,what))
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


def export_to_file(outfile, data, label, opts):

	if 'stdout' in opts:
		write_to_stdout(data, label, confirm=True)
	elif not sys.stdout.isatty():
		write_to_stdout(data, label, confirm=False)
	else:
		if 'outdir' in opts:
			outfile = "%s/%s" % (opts['outdir'], outfile)
		write_to_file(outfile, data, confirm=False if g.quiet else True)
		msg("%s saved to file '%s'" % (label.capitalize(), outfile))


def _display_control_data(label,metadata,hash_preset,salt,enc_seed):
	msg("WALLET DATA")
	fs = "  {:18} {}"
	pw_empty = "yes" if metadata[3] == "E" else "no"
	from mmgen.bitcoin import b58encode_pad
	for i in (
		("Label:",               label),
		("Seed ID:",             metadata[0]),
		("Key  ID:",             metadata[1]),
		("Seed length:",         "%s bits (%s bytes)" %
				(metadata[2],int(metadata[2])/8)),
		("Scrypt params:",  "Preset '%s' (%s)" % (hash_preset,
				" ".join([str(i) for i in _get_hash_params(hash_preset)]))),
		("Passphrase empty?", pw_empty.capitalize()),
		("Timestamp:",           "%s UTC" % metadata[4]),
	): msg(fs.format(*i))

	fs = "  {:6} {}"
	for i in (
		("Salt:",    ""),
		("  b58:",      b58encode_pad(salt)),
		("  hex:",      hexlify(salt)),
		("Encrypted seed:", ""),
		("  b58:",      b58encode_pad(enc_seed)),
		("  hex:",      hexlify(enc_seed))
	): msg(fs.format(*i))


def col4(s):
	nondiv = 1 if len(s) % 4 else 0
	return " ".join([s[4*i:4*i+4] for i in range(len(s)/4 + nondiv)])

def make_timestamp():
	import time
	tv = time.gmtime(time.time())[:6]
	return "{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(*tv)

def make_timestr():
	import time
	tv = time.gmtime(time.time())[:6]
	return "{:04d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}".format(*tv)

def secs_to_hms(secs):
	return "{:02d}:{:02d}:{:02d}".format(secs/3600, (secs/60) % 60, secs % 60)


def write_wallet_to_file(seed, passwd, key_id, salt, enc_seed, opts):

	seed_id = make_chksum_8(seed)
	seed_len = str(len(seed)*8)
	pw_status = "NE" if len(passwd) else "E"

	hash_preset = opts['hash_preset']

	outfile="{}-{}[{},{}].{}".format(seed_id,key_id,seed_len,hash_preset,g.wallet_ext)
	if 'outdir' in opts:
		outfile = "%s/%s" % (opts['outdir'], outfile)

	label = opts['label'] if 'label' in opts else "No Label"

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

	confirm = False if g.quiet else True
	write_to_file(outfile, "\n".join((chk,)+lines)+"\n", confirm)

	msg("Wallet saved to file '%s'" % outfile)
	if g.verbose:
		_display_control_data(label,metadata,hash_preset,salt,enc_seed)


def write_walletdat_dump_to_file(wallet_id,data,num_keys,ext,what,opts):
	outfile = "wd_{}[{}].{}".format(wallet_id,num_keys,ext)
	if 'outdir' in opts:
		outfile = "%s/%s" % (opts['outdir'], outfile)
	write_to_file(outfile,data,confirm=False)
	msg("wallet.dat %s saved to file '%s'" % (what,outfile))


def _compare_checksums(chksum1, desc1, chksum2, desc2):

	if chksum1.lower() == chksum2.lower():
		vmsg("OK (%s)" % chksum1.upper())
		return True
	else:
		if g.debug:
			print \
	"ERROR!\nComputed checksum %s (%s) doesn't match checksum %s (%s)" \
			% (desc1,chksum1,desc2,chksum2)
		return False

def _is_hex(s):
	try: int(s,16)
	except: return False
	else: return True

def match_ext(addr,ext):
	return addr.split(".")[-1] == ext

def _check_mmseed_format(words):

	valid = False
	what = "%s data" % g.seed_ext
	try:
		chklen = len(words[0])
	except:
		return False

	if len(words) < 3 or len(words) > 12:
		msg("Invalid data length (%s) in %s" % (len(words),what))
	elif not _is_hex(words[0]):
		msg("Invalid format of checksum '%s' in %s"%(words[0], what))
	elif chklen != 6:
		msg("Incorrect length of checksum (%s) in %s" % (chklen,what))
	else: valid = True

	return valid


def _check_wallet_format(infile, lines):

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
	elif g.debug:
		print "%s checksum passed: %s" % (desc.capitalize(),chk)


def get_data_from_wallet(infile,silent=False):

	# Don't make this a qmsg: User will be prompted for passphrase and must see
	# the filename.
	if not silent:
		msg("Getting {} wallet data from file '{}'".format(g.proj_name_cap,infile))

	f = open_file_or_exit(infile, 'r')

	lines = [i.strip() for i in f.readlines()]
	f.close()

	_check_wallet_format(infile, lines)

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


def _get_words_from_user(prompt, opts):
	# split() also strips
	words = my_raw_input(prompt,
				echo=True if 'echo_passphrase' in opts else False).split()
	if g.debug: print "Sanitized input: [%s]" % " ".join(words)
	return words


def _get_words_from_file(infile,what):
	qmsg("Getting %s from file '%s'" % (what,infile))
	f = open_file_or_exit(infile, 'r')
	# split() also strips
	words = f.read().split()
	f.close()
	if g.debug: print "Sanitized input: [%s]" % " ".join(words)
	return words


def get_lines_from_file(infile,what="",remove_comments=False):
	if what != "":
		qmsg("Getting %s from file '%s'" % (what,infile))
	f = open_file_or_exit(infile,'r')
	lines = f.read().splitlines(); f.close()
	if remove_comments:
		import re
		# re.sub(pattern, repl, string, count=0, flags=0)
		ret = []
		for i in lines:
			i = re.sub('#.*','',i,1)
			i = re.sub('\s+$','',i)
			if i: ret.append(i)
		return ret
	else:
		return lines


def get_data_from_file(infile,what="data"):
	qmsg("Getting %s from file '%s'" % (what,infile))
	f = open_file_or_exit(infile,'r')
	data = f.read()
	f.close()
	return data


def _get_seed_from_seed_data(words):

	if not _check_mmseed_format(words):
		msg("Invalid %s data" % g.seed_ext)
		return False

	stored_chk = words[0]
	seed_b58 = "".join(words[1:])

	chk = make_chksum_6(seed_b58)
	vmsg_r("Validating %s checksum..." % g.seed_ext)

	if _compare_checksums(chk, "from seed", stored_chk, "from input"):
		seed = b58decode_pad(seed_b58)
		if seed == False:
			msg("Invalid b58 number: %s" % val)
			return False

		vmsg("%s data produces seed ID: %s" % (g.seed_ext,make_chksum_8(seed)))
		return seed
	else:
		msg("Invalid checksum for {} seed".format(g.proj_name_cap))
		return False


passwd_file_used = False

def mark_passwd_file_as_used(opts):
	global passwd_file_used
	if passwd_file_used:
		msg_r("WARNING: Reusing passphrase from file '%s'." % opts['passwd_file'])
		msg(" This may not be what you want!")
	passwd_file_used = True


def get_mmgen_passphrase(prompt,opts):
	if 'passwd_file' in opts:
		mark_passwd_file_as_used(opts)
		return " ".join(_get_words_from_file(opts['passwd_file'],"passphrase"))
	else:
		return " ".join(_get_words_from_user(prompt,opts))


def get_bitcoind_passphrase(prompt,opts):
	if 'passwd_file' in opts:
		mark_passwd_file_as_used(opts)
		return get_data_from_file(opts['passwd_file'],
				"passphrase").strip("\r\n")
	else:
		return my_raw_input(prompt,
					echo=True if 'echo_passphrase' in opts else False)


def get_seed_from_wallet(
		infile,
		opts,
		prompt="Enter {} wallet passphrase: ".format(g.proj_name_cap),
		silent=False
		):

	wdata = get_data_from_wallet(infile,silent=silent)
	label,metadata,hash_preset,salt,enc_seed = wdata

	if g.verbose: _display_control_data(*wdata)

	passwd = get_mmgen_passphrase(prompt,opts)

	key = make_key(passwd, salt, hash_preset)

	return decrypt_seed(enc_seed, key, metadata[0], metadata[1])


def check_data_fits_file_at_offset(fname,offset,dlen,action):
	# TODO: Check for Windows
	import os, stat
	if stat.S_ISBLK(os.stat(fname).st_mode):
		fd = os.open(fname, os.O_RDONLY)
		fsize = os.lseek(fd, 0, os.SEEK_END)
		os.close(fd)
	else:
		fsize = os.stat(fname).st_size

	if fsize < offset + dlen:
		msg(
"Destination file has length %s, too short to %s %s bytes of data at offset %s"
			% (fsize,action,dlen,offset))
		sys.exit(1)


def get_hidden_incog_data(opts):
		# Already sanity-checked:
		fname,offset,seed_len = opts['from_incog_hidden'].split(",")
		qmsg("Getting hidden incog data from file '%s'" % fname)

		dlen = g.aesctr_iv_len + g.salt_len + (int(seed_len)/8)

		fsize = check_data_fits_file_at_offset(fname,int(offset),dlen,"read")

		f = os.open(fname,os.O_RDONLY)
		os.lseek(f, int(offset), os.SEEK_SET)
		data = os.read(f, dlen)
		os.close(f)
		qmsg("Data read from file '%s' at offset %s" % (fname,offset),
				"Data read from file")
		return data

def get_seed_from_incog_wallet(
		infile,
		opts,
		prompt="Enter %s wallet passphrase: " % g.proj_name_cap,
		silent=False,
		hex_input=False
	):

	what = "incognito wallet data"

	if "from_incog_hidden" in opts:
		d = get_hidden_incog_data(opts)
	else:
		d = get_data_from_file(infile,what)
		if hex_input:
			try:
				d = unhexlify("".join(d.split()).strip())
			except:
				msg("Data in file '%s' is not in hexadecimal format" % infile)
				sys.exit(2)
		# File could be of invalid length, so check:
		valid_dlens = [i/8 + g.aesctr_iv_len + g.salt_len for i in g.seed_lens]
		if len(d) not in valid_dlens:
			qmsg("Invalid incognito file size: %s.  Valid sizes (in bytes): %s" %
					(len(d), " ".join([str(i) for i in valid_dlens]))
				)
			return False

	iv, enc_incog_data = d[0:g.aesctr_iv_len], d[g.aesctr_iv_len:]

	qmsg("IV ID: %s.  Check this value if possible." % make_chksum_8(iv))
	vmsg(cmessages['incog_iv_id_hidden' if "from_incog_hidden" in opts
			else 'incog_iv_id'])

	passwd = get_mmgen_passphrase(prompt,opts)

	msg("Configured hash presets: %s" % " ".join(sorted(g.hash_presets)))
	while True:
		p = "Enter hash preset for %s wallet (default='%s'): "
		hp = my_raw_input(p % (g.proj_name_cap, g.hash_preset))
		if not hp:
			hp = g.hash_preset; break
		elif hp in g.hash_presets:
			break
		msg("%s: Invalid hash preset" % hp)

	from hashlib import sha256
	# IV is used BOTH to initialize counter and to salt password!
	key = make_key(passwd, iv, hp, "wrapper key")
	d = decrypt_seed(enc_incog_data, key, "", "", iv=int(hexlify(iv),16))
	if d == False: sys.exit(2)

	salt,enc_seed = d[0:g.salt_len], d[g.salt_len:]

	key = make_key(passwd, salt, hp, "main key")
	vmsg("Key ID: %s" % make_chksum_8(key))

	seed = decrypt_seed(enc_seed, key, "", "")
	qmsg("Seed ID: %s.  Check that this value is correct." % make_chksum_8(seed))
	vmsg(cmessages['incog_key_id_hidden' if "from_incog_hidden" in opts
			else 'incog_key_id'])

	return seed


def make_key(passwd, salt, hash_preset, what="key"):

	vmsg_r("Generating %s from passphrase.  Please wait..." % what)
	key = _scrypt_hash_passphrase(passwd, salt, hash_preset)
	vmsg("done")
	if g.debug: print "Key: %s" % hexlify(key)
	return key


def decrypt_seed(enc_seed, key, seed_id, key_id, iv=1):

	vmsg("Checking key...")
	chk1 = make_chksum_8(key)
	if key_id:
		if not _compare_checksums(chk1, "of key", key_id, "in header"):
			msg("Incorrect passphrase")
			return False

	vmsg("Decrypting seed with key...")

	from Crypto.Cipher import AES
	from Crypto.Util import Counter

	c = AES.new(key, AES.MODE_CTR,
			counter=Counter.new(g.aesctr_iv_len*8,initial_value=iv))
	dec_seed = c.decrypt(enc_seed)

	chk2 = make_chksum_8(dec_seed)
	if seed_id:
		if _compare_checksums(chk2,"of decrypted seed",seed_id,"in header"):
			qmsg("Passphrase is OK")
		else:
			if not g.debug:
				msg_r("Checking key ID...")
				chk1 = make_chksum_8(key)
				if _compare_checksums(chk1, "of key", key_id, "in header"):
					msg("Key ID is correct but decryption of seed failed")
				else:
					msg("Incorrect passphrase")

			return False
#	else:
#		qmsg("Generated IDs (Seed/Key): %s/%s" % (chk2,chk1))

	if g.debug: print "Decrypted seed: %s" % hexlify(dec_seed)

	return dec_seed


def _get_words(infile,what,prompt,opts):
	if infile:
		return _get_words_from_file(infile,what)
	else:
		return _get_words_from_user(prompt,opts)


def get_seed(infile,opts,silent=False):

	ext = infile.split(".")[-1]

	if   ext == g.mn_ext:           source = "mnemonic"
	elif ext == g.brain_ext:        source = "brainwallet"
	elif ext == g.seed_ext:         source = "seed"
	elif ext == g.wallet_ext:       source = "wallet"
	elif ext == g.incog_ext:        source = "incognito wallet"
	elif ext == g.incog_hex_ext:    source = "incognito wallet"
	elif 'from_mnemonic'  in opts: source = "mnemonic"
	elif 'from_brain'     in opts: source = "brainwallet"
	elif 'from_seed'      in opts: source = "seed"
	elif 'from_incog'     in opts: source = "incognito wallet"
	else:
		if infile: msg(
			"Invalid file extension for file: %s\nValid extensions: '.%s'" %
			(infile, "', '.".join(g.seedfile_exts)))
		else: msg("No seed source type specified and no file supplied")
		sys.exit(2)

	if source == "mnemonic":
		prompt = "Enter mnemonic: "
		words = _get_words(infile,"mnemonic data",prompt,opts)
		wl = get_default_wordlist()
		from mmgen.mnemonic import get_seed_from_mnemonic
		seed = get_seed_from_mnemonic(words,wl)
	elif source == "brainwallet":
		if 'from_brain' not in opts:
			msg("'--from-brain' parameters must be specified for brainwallet file")
			sys.exit(2)
		if not g.quiet:
			confirm_or_exit(
				cmessages['brain_warning'].format(
					g.proj_name_cap, *_get_from_brain_opt_params(opts)),
				"continue")
		prompt = "Enter brainwallet passphrase: "
		words = _get_words(infile,"brainwallet data",prompt,opts)
		seed = _get_seed_from_brain_passphrase(words,opts)
	elif source == "seed":
		prompt = "Enter seed in %s format: " % g.seed_ext
		words = _get_words(infile,"seed data",prompt,opts)
		seed = _get_seed_from_seed_data(words)
	elif source == "wallet":
		seed = get_seed_from_wallet(infile, opts, silent=silent)
	elif source == "incognito wallet":
		h = True if ext == g.incog_hex_ext or 'from_incog_hex' in opts else False
		seed = get_seed_from_incog_wallet(infile, opts, silent=silent, hex_input=h)


	if infile and not seed and (
		source == "seed" or source == "mnemonic" or source == "incognito wallet"):
		msg("Invalid %s file '%s'" % (source,infile))
		sys.exit(2)

	if g.debug: print "Seed: %s" % hexlify(seed)

	return seed

# Repeat if entered data is invalid
def get_seed_retry(infile,opts):
	silent = False
	while True:
		seed = get_seed(infile,opts,silent=silent)
		silent = True
		if seed: return seed


def do_pager(text):

	pagers = ["less","more"]
	shell = False

	from os import environ

# Hack for MS Windows command line (i.e. non CygWin) environment
# When 'shell' is true, Windows aborts the calling program if executable
# not found.
# When 'shell' is false, an exception is raised, invoking the fallback
# 'print' instead of the pager.
# We risk assuming that "more" will always be available on a stock
# Windows installation.
	if sys.platform.startswith("win") and 'HOME' not in environ:
		shell = True
		pagers = ["more"]

	if 'PAGER' in environ and environ['PAGER'] != pagers[0]:
		pagers = [environ['PAGER']] + pagers

	for pager in pagers:
		end = "" if pager == "less" else "\n(end of text)\n"
		try:
			from subprocess import Popen, PIPE, STDOUT
			p = Popen([pager], stdin=PIPE, shell=shell)
		except: pass
		else:
			try:
				p.communicate(text+end+"\n")
			except KeyboardInterrupt:
				# Has no effect.  Why?
				if pager != "less":
					msg("\n(User interrupt)\n")
			finally:
				msg_r("\r")
				break
	else: print text+end


def export_to_hidden_incog(incog_enc,opts):
	fname,offset = opts['export_incog_hidden'].split(",") #Already sanity-checked

	check_data_fits_file_at_offset(fname,int(offset),len(incog_enc),"write")

	if not g.quiet: confirm_or_exit("","alter file '%s'" % fname)
	f = os.open(fname,os.O_RDWR)
	os.lseek(f, int(offset), os.SEEK_SET)
	os.write(f, incog_enc)
	os.close(f)
	qmsg("Data written to file '%s' at offset %s" % (fname,offset),
			"Data written to file")


def pretty_hexdump(data,gw,cols,line_nums=False):
	r = 1 if len(data) % gw else 0
	return "".join(
		[
			("" if (line_nums == False or i % cols) else "%03i: " % (i/cols)) +
			hexlify(data[i*gw:i*gw+gw]) +
			(" " if (i+1) % cols else "\n")
				for i in range(len(data)/gw + r)
		]
	).rstrip()

def decode_pretty_hexdump(data):
	import re
	lines = [re.sub('^\d+:\s+','',l) for l in data.split("\n")]
	return unhexlify("".join(("".join(lines).split())))

def wallet_to_incog_data(infile,opts):

	d = get_data_from_wallet(infile,silent=True)
	seed_id,key_id,preset,salt,enc_seed = \
			d[1][0], d[1][1], d[2].split(":")[0], d[3], d[4]

	passwd = get_mmgen_passphrase("Enter mmgen passphrase: ",opts)
	key = make_key(passwd, salt, preset, "main key")
	# We don't need the seed; just do this to verify password.
	if decrypt_seed(enc_seed, key, seed_id, key_id) == False:
		sys.exit(2)

	from Crypto import Random
	iv = Random.new().read(g.aesctr_iv_len)
	iv_id = make_chksum_8(iv)
	qmsg("IV ID: %s" % iv_id)

	from binascii import hexlify
	from hashlib import sha256
	# IV is used BOTH to initialize counter and to salt password!
	key = make_key(passwd, iv, preset, "wrapper key")
	wrap_enc = encrypt_seed(salt + enc_seed, key, iv=int(hexlify(iv),16))

	return iv+wrap_enc,seed_id,key_id,iv_id,preset


if __name__ == "__main__":
	print "util.py"
