#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2014 Philemon <mmgen-py@yandex.com>
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
from mmgen.util import *
from mmgen.term import get_char

def encrypt_seed(seed, key):
	return encrypt_data(seed, key, iv=1, what="seed")


def decrypt_seed(enc_seed, key, seed_id, key_id):

	vmsg("Checking key...")
	chk1 = make_chksum_8(key)
	if key_id:
		if not compare_checksums(chk1, "of key", key_id, "in header"):
			msg("Incorrect passphrase")
			return False

	dec_seed = decrypt_data(enc_seed, key, iv=1, what="seed")

	chk2 = make_chksum_8(dec_seed)

	if seed_id:
		if compare_checksums(chk2,"of decrypted seed",seed_id,"in header"):
			qmsg("Passphrase is OK")
		else:
			if not g.debug:
				msg_r("Checking key ID...")
				if compare_checksums(chk1, "of key", key_id, "in header"):
					msg("Key ID is correct but decryption of seed failed")
				else:
					msg("Incorrect passphrase")

			return False
#	else:
#		qmsg("Generated IDs (Seed/Key): %s/%s" % (chk2,chk1))

	if g.debug: print "Decrypted seed: %s" % hexlify(dec_seed)

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

		if dec_data == data: vmsg("done\n")
		else:
			msg("ERROR.\nDecrypted %s doesn't match original %s" % (what,what))
			sys.exit(2)

	return enc_data


def decrypt_data(enc_data, key, iv=1, what="data"):

	vmsg("Decrypting %s with key..." % what)

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


def make_key(passwd, salt, hash_preset, what="key"):

	vmsg_r("Generating %s.  Please wait..." % what)
	key = scrypt_hash_passphrase(passwd, salt, hash_preset)
	vmsg("done")
	if g.debug: print "Key: %s" % hexlify(key)
	return key


def get_random_data_from_user(uchars):

	if g.quiet: msg("Enter %s random symbols" % uchars)
	else:       msg(cmessages['usr_rand_notice'] % uchars)

	prompt = "You may begin typing.  %s symbols left: "
	msg_r(prompt % uchars)

	import time
	# time.clock() always returns zero, so we'll use time.time()
	saved_time = time.time()

	key_data,time_data,pp = "",[],True

	for i in range(uchars):
		key_data += get_char(immed_chars="ALL",prehold_protect=pp)
		if i == 0: pp = False
		msg_r("\r" + prompt % (uchars - i - 1))
		now = time.time()
		time_data.append(now - saved_time)
		saved_time = now

	if g.quiet: msg_r("\r")
	else: msg_r("\rThank you.  That's enough.%s\n\n" % (" "*18))

	fmt_time_data = ["{:.22f}".format(i) for i in time_data]

	if g.debug:
		msg("\nUser input:\n%s\nKeystroke time intervals:\n%s\n" %
				(key_data,"\n".join(fmt_time_data)))

	prompt = "User random data successfully acquired.  Press ENTER to continue"
	prompt_and_get_char(prompt,"",enter_ok=True)

	return key_data+"".join(fmt_time_data)


def get_random(length,opts):
	from Crypto import Random
	os_rand = Random.new().read(length)
	if 'usr_randchars' in opts and opts['usr_randchars'] not in (0,-1):
		kwhat = "a key from OS random data + "
		if not g.user_entropy:
			g.user_entropy = sha256(
				get_random_data_from_user(opts['usr_randchars'])).digest()
			kwhat += "user entropy"
		else:
			kwhat += "saved user entropy"
		key = make_key(g.user_entropy, "", '2', what=kwhat)
		return encrypt_data(os_rand,key,what="random data",verify=False)
	else:
		return os_rand


def get_seed_from_wallet(
		infile,
		opts,
		prompt="Enter {} wallet passphrase: ".format(g.proj_name),
		silent=False
		):

	wdata = get_data_from_wallet(infile,silent=silent)
	label,metadata,hash_preset,salt,enc_seed = wdata

	if g.verbose: display_control_data(*wdata)

	passwd = get_mmgen_passphrase(prompt,opts)

	key = make_key(passwd, salt, hash_preset)

	return decrypt_seed(enc_seed, key, metadata[0], metadata[1])


def get_seed_from_incog_wallet(
		infile,
		opts,
		prompt="Enter {} wallet passphrase: ".format(g.proj_name),
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

	msg("Incog ID: %s (IV ID: %s)" % (make_iv_chksum(iv),make_chksum_8(iv)))
	qmsg("Check the applicable value against your records.")
	vmsg(cmessages['incog_iv_id_hidden' if "from_incog_hidden" in opts
			else 'incog_iv_id'])

	passwd = get_mmgen_passphrase(prompt,opts)

	qmsg("Configured hash presets: %s" % " ".join(sorted(g.hash_presets)))
	while True:
		p = "Enter hash preset for %s wallet (default='%s'): "
		hp = my_raw_input(p % (g.proj_name, g.hash_preset))
		if not hp:
			hp = g.hash_preset; break
		elif hp in g.hash_presets:
			break
		msg("%s: Invalid hash preset" % hp)

	# IV is used BOTH to initialize counter and to salt password!
	key = make_key(passwd, iv, hp, "wrapper key")
	d = decrypt_data(enc_incog_data, key, int(hexlify(iv),16), "incog data")
	if d == False: sys.exit(2)

	salt,enc_seed = d[0:g.salt_len], d[g.salt_len:]

	key = make_key(passwd, salt, hp, "main key")
	vmsg("Key ID: %s" % make_chksum_8(key))

	seed = decrypt_seed(enc_seed, key, "", "")
	qmsg("Seed ID: %s.  Check that this value is correct." % make_chksum_8(seed))
	vmsg(cmessages['incog_key_id_hidden' if "from_incog_hidden" in opts
			else 'incog_key_id'])

	return seed


def wallet_to_incog_data(infile,opts):

	d = get_data_from_wallet(infile,silent=True)
	seed_id,key_id,preset,salt,enc_seed = \
			d[1][0], d[1][1], d[2].split(":")[0], d[3], d[4]

	passwd = get_mmgen_passphrase("Enter mmgen passphrase: ",opts)
	key = make_key(passwd, salt, preset, "main key")
	# We don't need the seed; just do this to verify password.
	if decrypt_seed(enc_seed, key, seed_id, key_id) == False:
		sys.exit(2)

	iv = get_random(g.aesctr_iv_len,opts)
	iv_id = make_iv_chksum(iv)
	msg("Incog ID: %s" % iv_id)

	# IV is used BOTH to initialize counter and to salt password!
	key = make_key(passwd, iv, preset, "wrapper key")
	m = "incog data"
	wrap_enc = encrypt_data(salt + enc_seed, key, int(hexlify(iv),16), m)

	return iv+wrap_enc,seed_id,key_id,iv_id,preset


def get_seed(infile,opts,silent=False):

	ext = get_extension(infile)

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
		words = get_words(infile,"mnemonic data",prompt,opts)
		wl = get_default_wordlist()
		from mmgen.mnemonic import get_seed_from_mnemonic
		seed = get_seed_from_mnemonic(words,wl)
	elif source == "brainwallet":
		if 'from_brain' not in opts:
			msg("'--from-brain' parameters must be specified for brainwallet file")
			sys.exit(2)
		prompt = "Enter brainwallet passphrase: "
		words = get_words(infile,"brainwallet data",prompt,opts)
		seed = _get_seed_from_brain_passphrase(words,opts)
	elif source == "seed":
		prompt = "Enter seed in %s format: " % g.seed_ext
		words = get_words(infile,"seed data",prompt,opts)
		seed = get_seed_from_seed_data(words)
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


def _get_seed_from_brain_passphrase(words,opts):
	bp = " ".join(words)
	if g.debug: print "Sanitized brain passphrase: %s" % bp
	seed_len,hash_preset = get_from_brain_opt_params(opts)
	if g.debug: print "Brainwallet l = %s, p = %s" % (seed_len,hash_preset)
	vmsg_r("Hashing brainwallet data.  Please wait...")
	# Use buflen arg of scrypt.hash() to get seed of desired length
	seed = scrypt_hash_passphrase(bp, "", hash_preset, buflen=seed_len/8)
	vmsg("Done")
	return seed


# Vars for mmgen_*crypt functions only
salt_len,sha256_len,nonce_len = 32,32,32

def mmgen_encrypt(data,what="data",hash_preset='3',opts={}):
	salt,iv,nonce = get_random(salt_len,opts),\
		get_random(g.aesctr_iv_len,opts), get_random(nonce_len,opts)
	hp,m = (hash_preset,"user-requested") if hash_preset else ('3',"default")
	vmsg("Encrypting %s" % what)
	qmsg("Using %s hash preset of '%s'" % (m,hp))
	passwd = get_new_passphrase("passphrase",{})
	key = make_key(passwd, salt, hp)
	enc_d = encrypt_data(sha256(nonce+data).digest() + nonce + data, key,
				int(hexlify(iv),16), what=what)
	return salt+iv+enc_d


def mmgen_decrypt(data,what="data",hash_preset='3',opts={}):
	dstart = salt_len + g.aesctr_iv_len
	salt,iv,enc_d = data[:salt_len],data[salt_len:dstart],data[dstart:]
	hp,m = (hash_preset,"user-requested") if hash_preset else ('3',"default")
	vmsg("Preparing to decrypt %s" % what)
	qmsg("Using %s hash preset of '%s'" % (m,hp))
	passwd = get_mmgen_passphrase("Enter passphrase: ",{})
	key = make_key(passwd, salt, hp)
	dec_d = decrypt_data(enc_d, key, int(hexlify(iv),16), what)
	if dec_d[:sha256_len] == sha256(dec_d[sha256_len:]).digest():
		vmsg("Success. Passphrase and hash preset are correct")
		return dec_d[sha256_len+nonce_len:]
	else:
		msg("Incorrect passphrase or hash preset")
		return False
