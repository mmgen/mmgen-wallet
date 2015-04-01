#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2015 Philemon <mmgen-py@yandex.com>
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
crypto.py:  Cryptographic and related routines for the 'mmgen-tool' utility
"""

import sys
from binascii import hexlify
from hashlib import sha256

import mmgen.config as g
import mmgen.opt as opt
from mmgen.util import *
from mmgen.term import get_char

crmsg = {
	'incog_iv_id': """
   Check that the generated Incog ID above is correct.
   If it's not, then your incognito data is incorrect or corrupted.
""",
	'incog_iv_id_hidden': """
   Check that the generated Incog ID above is correct.
   If it's not, then your incognito data is incorrect or corrupted,
   or you've supplied an incorrect offset.
""",
	'usr_rand_notice': """
You've chosen to not fully trust your OS's random number generator and provide
some additional entropy of your own.  Please type %s symbols on your keyboard.
Type slowly and choose your symbols carefully for maximum randomness.  Try to
use both upper and lowercase as well as punctuation and numerals.  What you
type will not be displayed on the screen.  Note that the timings between your
keystrokes will also be used as a source of randomness.
""",
	'incorrect_incog_passphrase_try_again': """
Incorrect passphrase, hash preset, or maybe old-format incog wallet.
Try again? (Y)es, (n)o, (m)ore information:
""".strip(),
	'confirm_seed_id': """
If the seed ID above is correct but you're seeing this message, then you need
to exit and re-run the program with the '--old-incog-fmt' option.
""".strip(),
}

def encrypt_seed(seed, key):
	return encrypt_data(seed, key, iv=1, what="seed")


def decrypt_seed(enc_seed, key, seed_id, key_id):

	vmsg_r("Checking key...")
	chk1 = make_chksum_8(key)
	if key_id:
		if not compare_chksums(key_id,"key id",chk1,"computed",die=False):
			msg("Incorrect passphrase")
			return False

	dec_seed = decrypt_data(enc_seed, key, iv=1, what="seed")

	chk2 = make_chksum_8(dec_seed)

	if seed_id:
		if compare_chksums(seed_id,"seed id",chk2,"decrypted seed",die=False):
			qmsg("Passphrase is OK")
		else:
			if not opt.debug:
				msg_r("Checking key ID...")
				if compare_chksums(key_id,"key id",chk1,"computed",die=False):
					msg("Key ID is correct but decryption of seed failed")
				else:
					msg("Incorrect passphrase")

			vmsg("")
			return False
#	else:
#		qmsg("Generated IDs (Seed/Key): %s/%s" % (chk2,chk1))

	if opt.debug: Msg("Decrypted seed: %s" % hexlify(dec_seed))

	vmsg("OK")
	return dec_seed


def encrypt_data(data, key, iv=1, what="data", verify=True):
	"""
	Encrypt arbitrary data using AES256 in counter mode
	"""

	# 192-bit seed is 24 bytes -> not multiple of 16.  Must use MODE_CTR
	from Crypto.Cipher import AES
	from Crypto.Util import Counter

	vmsg("Encrypting %s" % what)

	c = AES.new(key, AES.MODE_CTR,
			counter=Counter.new(g.aesctr_iv_len*8,initial_value=iv))
	enc_data = c.encrypt(data)

	if verify:
		vmsg_r("Performing a test decryption of the %s..." % what)

		c = AES.new(key, AES.MODE_CTR,
				counter=Counter.new(g.aesctr_iv_len*8,initial_value=iv))
		dec_data = c.decrypt(enc_data)

		if dec_data == data: vmsg("done")
		else:
			msg("ERROR.\nDecrypted %s doesn't match original %s" % (what,what))
			sys.exit(2)

	return enc_data


def decrypt_data(enc_data, key, iv=1, what="data"):

	vmsg_r("Decrypting %s with key..." % what)

	from Crypto.Cipher import AES
	from Crypto.Util import Counter

	c = AES.new(key, AES.MODE_CTR,
			counter=Counter.new(g.aesctr_iv_len*8,initial_value=iv))

	return c.decrypt(enc_data)


def scrypt_hash_passphrase(passwd, salt, hash_preset, buflen=32):

	# Buflen arg is for brainwallets only, which use this function to generate
	# the seed directly.

	N,r,p = get_hash_params(hash_preset)

	import scrypt
	return scrypt.hash(passwd, salt, 2**N, r, p, buflen=buflen)


def make_key(passwd,salt,hash_preset,
		what="encryption key",from_what="passphrase",verbose=False):

	if from_what: what += " from "
	if opt.verbose or verbose:
		msg_r("Generating %s%s..." % (what,from_what))
	key = scrypt_hash_passphrase(passwd, salt, hash_preset)
	if opt.verbose or verbose: msg("done")
	if opt.debug: Msg("Key: %s" % hexlify(key))
	return key


def get_random_data_from_user(uchars):

	if opt.quiet: msg("Enter %s random symbols" % uchars)
	else:       msg(crmsg['usr_rand_notice'] % uchars)

	prompt = "You may begin typing.  %s symbols left: "
	msg_r(prompt % uchars)

	import time
	# time.clock() always returns zero, so we'll use time.time()
	saved_time = time.time()

	key_data,time_data,pp = "",[],True

	for i in range(uchars):
		key_data += get_char(immed_chars="ALL",prehold_protect=pp)
		pp = False
		msg_r("\r" + prompt % (uchars - i - 1))
		now = time.time()
		time_data.append(now - saved_time)
		saved_time = now

	if opt.quiet: msg_r("\r")
	else: msg_r("\rThank you.  That's enough.%s\n\n" % (" "*18))

	fmt_time_data = ["{:.22f}".format(i) for i in time_data]

	if opt.debug:
		msg("\nUser input:\n%s\nKeystroke time intervals:\n%s\n" %
				(key_data,"\n".join(fmt_time_data)))

	prompt = "User random data successfully acquired.  Press ENTER to continue"
	prompt_and_get_char(prompt,"",enter_ok=True)

	return key_data+"".join(fmt_time_data)


def get_random(length):
	from Crypto import Random
	os_rand = Random.new().read(length)
	if g.use_urandchars:
		from_what = "OS random data"
		if not g.user_entropy:
			g.user_entropy = \
				sha256(get_random_data_from_user(opt.usr_randchars)).digest()
			from_what += " plus user-supplied entropy"
		else:
			from_what += " plus saved user-supplied entropy"
		key = make_key(g.user_entropy, "", '2', from_what=from_what, verbose=True)
		return encrypt_data(os_rand,key,what="random data",verify=False)
	else:
		return os_rand


def get_seed_from_wallet(
		infile,
		prompt_info="{} wallet".format(g.proj_name),
		silent=False
		):

	wdata = get_data_from_wallet(infile,silent=silent)
	label,metadata,hash_preset,salt,enc_seed = wdata

	if opt.debug: display_control_data(*wdata)

	padd = " "+infile if opt.quiet else ""
	passwd = get_mmgen_passphrase(prompt_info+padd)

	key = make_key(passwd, salt, hash_preset)

	return decrypt_seed(enc_seed, key, metadata[0], metadata[1])


def get_hidden_incog_data():
		# Already sanity-checked:
		fname,offset,seed_len = opt.from_incog_hidden.split(",")
		qmsg("Getting hidden incog data from file '%s'" % fname)

		z = 0 if opt.old_incog_fmt else 8
		dlen = g.aesctr_iv_len + g.salt_len + (int(seed_len)/8) + z

		fsize = check_data_fits_file_at_offset(fname,int(offset),dlen,"read")

		import os
		f = os.open(fname,os.O_RDONLY)
		os.lseek(f, int(offset), os.SEEK_SET)
		data = os.read(f, dlen)
		os.close(f)
		qmsg("Data read from file '%s' at offset %s" % (fname,offset),
				"Data read from file")
		return data

def confirm_old_format():

	while True:
		reply = get_char(
			crmsg['incorrect_incog_passphrase_try_again']+" ").strip("\n\r")
		if not reply:       msg(""); return False
		elif reply in 'yY': msg(""); return False
		elif reply in 'nN': msg("\nExiting at user request"); sys.exit(1)
		elif reply in 'mM': msg(""); return True
		else:
			if opt.verbose: msg("\nInvalid reply")
			else: msg_r("\r")


def get_seed_from_incog_wallet(
		infile,
		prompt_info="{} incognito wallet".format(g.proj_name),
		silent=False,
		hex_input=False
	):

	what = "incognito wallet data"

	if opt.from_incog_hidden:
		d = get_hidden_incog_data()
	else:
		d = get_data_from_file(infile,what)
		if hex_input:
			try:
				d = unhexlify("".join(d.split()).strip())
			except:
				msg("Data in file '%s' is not in hexadecimal format" % infile)
				sys.exit(2)
		# File could be of invalid length, so check:
		z = 0 if opt.old_incog_fmt else 8
		valid_dlens = [i/8 + g.aesctr_iv_len + g.salt_len + z for i in g.seed_lens]
		# New fmt: [56, 64, 72]. Old fmt: [48, 56, 64].
		if len(d) not in valid_dlens:
			vn = [i/8 + g.aesctr_iv_len + g.salt_len + 8 for i in g.seed_lens]
			if len(d) in vn:
				msg("Re-run the program without the '--old-incog-fmt' option")
				sys.exit()
			else: qmsg(
			"Invalid incognito file size: %s.  Valid sizes (in bytes): %s" %
						(len(d), " ".join([str(i) for i in valid_dlens])))
			return False

	iv, enc_incog_data = d[0:g.aesctr_iv_len], d[g.aesctr_iv_len:]

	incog_id = make_iv_chksum(iv)
	msg("Incog ID: %s (IV ID: %s)" % (incog_id,make_chksum_8(iv)))
	qmsg("Check the applicable value against your records.")
	vmsg(crmsg['incog_iv_id_hidden' if opt.from_incog_hidden
			else 'incog_iv_id'])

	while True:
		passwd = get_mmgen_passphrase(prompt_info+" "+incog_id)

		qmsg("Configured hash presets: %s" % " ".join(sorted(g.hash_presets)))
		hp = get_hash_preset_from_user(what="incog wallet")

		# IV is used BOTH to initialize counter and to salt password!
		key = make_key(passwd, iv, hp, "wrapper key")
		d = decrypt_data(enc_incog_data, key, int(hexlify(iv),16), "incog data")

		salt,enc_seed = d[0:g.salt_len], d[g.salt_len:]

		key = make_key(passwd, salt, hp, "main key")
		vmsg("Key ID: %s" % make_chksum_8(key))

		seed = decrypt_seed(enc_seed, key, "", "")
		old_fmt_sid = make_chksum_8(seed)

		def confirm_correct_seed_id(sid):
			m = "Seed ID: %s.  Is the Seed ID correct?" % sid
			return keypress_confirm(m, True)

		if opt.old_incog_fmt:
			if confirm_correct_seed_id(old_fmt_sid):
				break
		else:
			chk,seed_maybe = seed[:8],seed[8:]
			if sha256(seed_maybe).digest()[:8] == chk:
				msg("Passphrase and hash preset are correct")
				seed = seed_maybe
				break
			elif confirm_old_format():
				if confirm_correct_seed_id(old_fmt_sid):
					break

	return seed


def _get_seed(infile,silent=False,seed_id=""):

	ext = get_extension(infile)

	if   ext == g.mn_ext:           source = "mnemonic"
	elif ext == g.brain_ext:        source = "brainwallet"
	elif ext == g.seed_ext:         source = "seed"
	elif ext == g.wallet_ext:       source = "wallet"
	elif ext == g.incog_ext:        source = "incognito wallet"
	elif ext == g.incog_hex_ext:    source = "incognito wallet"
	elif opt.from_mnemonic : source = "mnemonic"
	elif opt.from_brain    : source = "brainwallet"
	elif opt.from_seed     : source = "seed"
	elif opt.from_incog    : source = "incognito wallet"
	else:
		if infile: msg(
			"Invalid file extension for file: %s\nValid extensions: '.%s'" %
			(infile, "', '.".join(g.seedfile_exts)))
		else: msg("No seed source type specified and no file supplied")
		sys.exit(2)

	seed_id_str = " for seed ID "+seed_id if seed_id else ""
	if source == "mnemonic":
		prompt = "Enter mnemonic%s: " % seed_id_str
		words = get_words(infile,"mnemonic data",prompt)
		wl = get_default_wordlist()
		from mmgen.mnemonic import get_seed_from_mnemonic
		seed = get_seed_from_mnemonic(words,wl)
	elif source == "brainwallet":
		if not opt.from_brain:
			msg("'--from-brain' parameters must be specified for brainwallet file")
			sys.exit(2)
		prompt = "Enter brainwallet passphrase%s: " % seed_id_str
		words = get_words(infile,"brainwallet data",prompt)
		seed = _get_seed_from_brain_passphrase(words)
	elif source == "seed":
		prompt = "Enter seed%s in %s format: " % (seed_id_str,g.seed_ext)
		words = get_words(infile,"seed data",prompt)
		seed = get_seed_from_seed_data(words)
	elif source == "wallet":
		seed = get_seed_from_wallet(infile, silent=silent)
	elif source == "incognito wallet":
		h = (ext == g.incog_hex_ext) or opt.from_incog_hex
		seed = get_seed_from_incog_wallet(infile, silent=silent, hex_input=h)


	if infile and not seed and (
		source == "seed" or source == "mnemonic" or source == "incognito wallet"):
		msg("Invalid %s file '%s'" % (source,infile))
		sys.exit(2)

	if opt.debug: Msg("Seed: %s" % hexlify(seed))

	return seed


# Repeat if entered data is invalid
def get_seed_retry(infile,seed_id=""):
	silent = False
	while True:
		seed = _get_seed(infile,silent=silent,seed_id=seed_id)
		silent = True
		if seed: return seed


def _get_seed_from_brain_passphrase(words):
	bp = " ".join(words)
	if opt.debug: Msg("Sanitized brain passphrase: %s" % bp)
	seed_len,hash_preset = get_from_brain_opt_params()
	if opt.debug: Msg("Brainwallet l = %s, p = %s" % (seed_len,hash_preset))
	vmsg_r("Hashing brainwallet data.  Please wait...")
	# Use buflen arg of scrypt.hash() to get seed of desired length
	seed = scrypt_hash_passphrase(bp, "", hash_preset, buflen=seed_len/8)
	vmsg("Done")
	return seed


# Vars for mmgen_*crypt functions only
salt_len,sha256_len,nonce_len = 32,32,32

def mmgen_encrypt(data,what="data",hash_preset=''):
	salt,iv,nonce = get_random(salt_len),\
					get_random(g.aesctr_iv_len), \
					get_random(nonce_len)
	hp = hash_preset or get_hash_preset_from_user('3',what)
	m = "default" if hp == '3' else "user-requested"
	vmsg("Encrypting %s" % what)
	qmsg("Using %s hash preset of '%s'" % (m,hp))
	passwd = get_new_passphrase(what, {})
	key = make_key(passwd, salt, hp)
	enc_d = encrypt_data(sha256(nonce+data).digest() + nonce + data, key,
				int(hexlify(iv),16), what=what)
	return salt+iv+enc_d


def mmgen_decrypt(data,what="data",hash_preset=""):
	dstart = salt_len + g.aesctr_iv_len
	salt,iv,enc_d = data[:salt_len],data[salt_len:dstart],data[dstart:]
	vmsg("Preparing to decrypt %s" % what)
	hp = hash_preset or get_hash_preset_from_user('3',what)
	m = "default" if hp == '3' else "user-requested"
	qmsg("Using %s hash preset of '%s'" % (m,hp))
	passwd = get_mmgen_passphrase(what)
	key = make_key(passwd, salt, hp)
	dec_d = decrypt_data(enc_d, key, int(hexlify(iv),16), what)
	if dec_d[:sha256_len] == sha256(dec_d[sha256_len:]).digest():
		vmsg("OK")
		return dec_d[sha256_len+nonce_len:]
	else:
		msg("Incorrect passphrase or hash preset")
		return False

def mmgen_decrypt_retry(d,what="data"):
	while True:
		d_dec = mmgen_decrypt(d,what)
		if d_dec: return d_dec
		msg("Trying again...")
