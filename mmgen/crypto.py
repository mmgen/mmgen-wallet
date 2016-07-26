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
crypto.py:  Cryptographic and related routines for the MMGen suite
"""

from binascii import hexlify
from hashlib import sha256

from mmgen.common import *
from mmgen.term import get_char

crmsg = {
	'usr_rand_notice': """
You've chosen to not fully trust your OS's random number generator and provide
some additional entropy of your own.  Please type %s symbols on your keyboard.
Type slowly and choose your symbols carefully for maximum randomness.  Try to
use both upper and lowercase as well as punctuation and numerals.  What you
type will not be displayed on the screen.  Note that the timings between your
keystrokes will also be used as a source of randomness.
""",
# 	'incog_iv_id': """
#    Check that the generated Incog ID above is correct.
#    If it's not, then your incognito data is incorrect or corrupted.
# """,
# 	'incog_iv_id_hidden': """
#    Check that the generated Incog ID above is correct.
#    If it's not, then your incognito data is incorrect or corrupted,
#    or you've supplied an incorrect offset.
# """,
# 	'incorrect_incog_passphrase_try_again': """
# Incorrect passphrase, hash preset, or maybe old-format incog wallet.
# Try again? (Y)es, (n)o, (m)ore information:
# """.strip(),
# 	'confirm_seed_id': """
# If the Seed ID above is correct but you're seeing this message, then you need
# to exit and re-run the program with the '--old-incog-fmt' option.
# """.strip(),
}

def encrypt_seed(seed, key):
	return encrypt_data(seed, key, iv=1, desc='seed')


def decrypt_seed(enc_seed, key, seed_id, key_id):

	vmsg_r('Checking key...')
	chk1 = make_chksum_8(key)
	if key_id:
		if not compare_chksums(key_id,'key ID',chk1,'computed'):
			msg('Incorrect passphrase or hash preset')
			return False

	dec_seed = decrypt_data(enc_seed, key, iv=1, desc='seed')

	chk2 = make_chksum_8(dec_seed)

	if seed_id:
		if compare_chksums(seed_id,'Seed ID',chk2,'decrypted seed'):
			qmsg('Passphrase is OK')
		else:
			if not opt.debug:
				msg_r('Checking key ID...')
				if compare_chksums(key_id,'key ID',chk1,'computed'):
					msg('Key ID is correct but decryption of seed failed')
				else:
					msg('Incorrect passphrase or hash preset')

			vmsg('')
			return False
#	else:
#		qmsg('Generated IDs (Seed/Key): %s/%s' % (chk2,chk1))

	dmsg('Decrypted seed: %s' % hexlify(dec_seed))

	return dec_seed


def encrypt_data(data, key, iv=1, desc='data', verify=True):

	# 192-bit seed is 24 bytes -> not multiple of 16.  Must use MODE_CTR
	from Crypto.Cipher import AES
	from Crypto.Util import Counter

	vmsg('Encrypting %s' % desc)

	c = AES.new(key, AES.MODE_CTR,
			counter=Counter.new(g.aesctr_iv_len*8,initial_value=iv))
	enc_data = c.encrypt(data)

	if verify:
		vmsg_r('Performing a test decryption of the %s...' % desc)

		c = AES.new(key, AES.MODE_CTR,
				counter=Counter.new(g.aesctr_iv_len*8,initial_value=iv))
		dec_data = c.decrypt(enc_data)

		if dec_data == data: vmsg('done')
		else:
			die(2,"ERROR.\nDecrypted %s doesn't match original %s" % (desc,desc))

	return enc_data


def decrypt_data(enc_data, key, iv=1, desc='data'):

	vmsg_r('Decrypting %s with key...' % desc)

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
		desc='encryption key',from_what='passphrase',verbose=False):

	if from_what: desc += ' from '
	if opt.verbose or verbose:
		msg_r('Generating %s%s...' % (desc,from_what))
	key = scrypt_hash_passphrase(passwd, salt, hash_preset)
	if opt.verbose or verbose: msg('done')
	dmsg('Key: %s' % hexlify(key))
	return key


def _get_random_data_from_user(uchars):

	if opt.quiet: msg('Enter %s random symbols' % uchars)
	else:       msg(crmsg['usr_rand_notice'] % uchars)

	prompt = 'You may begin typing.  %s symbols left: '
	msg_r(prompt % uchars)

	import time
	# time.clock() always returns zero, so we'll use time.time()
	saved_time = time.time()

	key_data,time_data,pp = '',[],True

	for i in range(uchars):
		key_data += get_char(immed_chars='ALL',prehold_protect=pp)
		pp = False
		msg_r('\r' + prompt % (uchars - i - 1))
		now = time.time()
		time_data.append(now - saved_time)
		saved_time = now

	if opt.quiet: msg_r('\r')
	else: msg_r("\rThank you.  That's enough.%s\n\n" % (' '*18))

	fmt_time_data = ['{:.22f}'.format(i) for i in time_data]

	dmsg('\nUser input:\n%s\nKeystroke time intervals:\n%s\n' %
				(key_data,'\n'.join(fmt_time_data)))

	prompt = 'User random data successfully acquired.  Press ENTER to continue'
	prompt_and_get_char(prompt,'',enter_ok=True)

	return key_data+''.join(fmt_time_data)


def get_random(length):
	from Crypto import Random
	os_rand = Random.new().read(length)
	if g.use_urandchars and opt.usr_randchars:
		from_what = 'OS random data'
		if not g.user_entropy:
			g.user_entropy = \
				sha256(_get_random_data_from_user(opt.usr_randchars)).digest()
			from_what += ' plus user-supplied entropy'
		else:
			from_what += ' plus saved user-supplied entropy'
		key = make_key(g.user_entropy, '', '2', from_what=from_what, verbose=True)
		return encrypt_data(os_rand,key,desc='random data',verify=False)
	else:
		return os_rand


# Vars for mmgen_*crypt functions only
salt_len,sha256_len,nonce_len = 32,32,32

def mmgen_encrypt(data,desc='data',hash_preset=''):
	salt,iv,nonce = get_random(salt_len),\
					get_random(g.aesctr_iv_len), \
					get_random(nonce_len)
	hp = hash_preset or get_hash_preset_from_user('3',desc)
	m = ('user-requested','default')[hp=='3']
	vmsg('Encrypting %s' % desc)
	qmsg("Using %s hash preset of '%s'" % (m,hp))
	passwd = get_new_passphrase(desc, {})
	key = make_key(passwd, salt, hp)
	enc_d = encrypt_data(sha256(nonce+data).digest() + nonce + data, key,
				int(hexlify(iv),16), desc=desc)
	return salt+iv+enc_d


def mmgen_decrypt(data,desc='data',hash_preset=''):
	dstart = salt_len + g.aesctr_iv_len
	salt,iv,enc_d = data[:salt_len],data[salt_len:dstart],data[dstart:]
	vmsg('Preparing to decrypt %s' % desc)
	hp = hash_preset or get_hash_preset_from_user('3',desc)
	m = ('user-requested','default')[hp=='3']
	qmsg("Using %s hash preset of '%s'" % (m,hp))
	passwd = get_mmgen_passphrase(desc)
	key = make_key(passwd, salt, hp)
	dec_d = decrypt_data(enc_d, key, int(hexlify(iv),16), desc)
	if dec_d[:sha256_len] == sha256(dec_d[sha256_len:]).digest():
		vmsg('OK')
		return dec_d[sha256_len+nonce_len:]
	else:
		msg('Incorrect passphrase or hash preset')
		return False

def mmgen_decrypt_retry(d,desc='data'):
	while True:
		d_dec = mmgen_decrypt(d,desc)
		if d_dec: return d_dec
		msg('Trying again...')
