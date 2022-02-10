#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
crypto.py: Random number, password hashing and symmetric encryption routines for the MMGen suite
"""

import os
from collections import namedtuple

from .globalvars import g
from .opts import opt
from .util import (
	msg,
	msg_r,
	dmsg,
	vmsg,
	vmsg_r,
	qmsg,
	fmt,
	line_input,
	get_words_from_user,
	make_chksum_8,
	compare_chksums,
	pwfile_reuse_warning,
)

mmenc_ext = 'mmenc'
scramble_hash_rounds = 10

salt_len       = 16
aesctr_iv_len  = 16
aesctr_dfl_iv  = int.to_bytes(1,aesctr_iv_len,'big')
hincog_chk_len = 8

# Scrypt params: 'id_num': [N, r, p] (N is an exponent of two)
# NB: hashlib.scrypt in Python (>=v3.6) supports max N value of 14.  This means that
# for hash presets > 3 the standalone scrypt library must be used!
_hp = namedtuple('scrypt_preset',['N','r','p'])
hash_presets = {
	'1': _hp(12, 8, 1),
	'2': _hp(13, 8, 4),
	'3': _hp(14, 8, 8),
	'4': _hp(15, 8, 12),
	'5': _hp(16, 8, 16),
	'6': _hp(17, 8, 20),
	'7': _hp(18, 8, 24),
}

def get_hash_params(hash_preset):
	if hash_preset in hash_presets:
		return hash_presets[hash_preset] # N,r,p
	else: # Shouldn't be here
		die(3,f"{hash_preset}: invalid 'hash_preset' value")

def sha256_rounds(s,n):
	from hashlib import sha256
	for i in range(n):
		s = sha256(s).digest()
	return s

def scramble_seed(seed,scramble_key):
	import hmac
	step1 = hmac.digest(seed,scramble_key,'sha256')
	if g.debug:
		msg(f'Seed:  {seed.hex()!r}\nScramble key: {scramble_key}\nScrambled seed: {step1.hex()}\n')
	return sha256_rounds( step1, scramble_hash_rounds )

def encrypt_seed(seed,key):
	return encrypt_data(seed,key,desc='seed')

def decrypt_seed(enc_seed,key,seed_id,key_id):
	vmsg_r('Checking key...')
	chk1 = make_chksum_8(key)
	if key_id:
		if not compare_chksums(key_id,'key ID',chk1,'computed'):
			msg('Incorrect passphrase or hash preset')
			return False

	dec_seed = decrypt_data(enc_seed,key,desc='seed')
	chk2     = make_chksum_8(dec_seed)
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
#		qmsg(f'Generated IDs (Seed/Key): {chk2}/{chk1}')

	dmsg(f'Decrypted seed: {dec_seed.hex()}')
	return dec_seed

def encrypt_data(data,key,iv=aesctr_dfl_iv,desc='data',verify=True,silent=False):
	from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
	from cryptography.hazmat.backends import default_backend
	if not silent:
		vmsg(f'Encrypting {desc}')
	c = Cipher(algorithms.AES(key),modes.CTR(iv),backend=default_backend())
	encryptor = c.encryptor()
	enc_data = encryptor.update(data) + encryptor.finalize()

	if verify:
		vmsg_r(f'Performing a test decryption of the {desc}...')
		c = Cipher(algorithms.AES(key),modes.CTR(iv),backend=default_backend())
		encryptor = c.encryptor()
		dec_data = encryptor.update(enc_data) + encryptor.finalize()
		if dec_data != data:
			die(2,f'ERROR.\nDecrypted {desc} doesn’t match original {desc}')
		if not silent:
			vmsg('done')

	return enc_data

def decrypt_data(enc_data,key,iv=aesctr_dfl_iv,desc='data'):
	from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
	from cryptography.hazmat.backends import default_backend
	vmsg_r(f'Decrypting {desc} with key...')
	c = Cipher(algorithms.AES(key),modes.CTR(iv),backend=default_backend())
	encryptor = c.encryptor()
	return encryptor.update(enc_data) + encryptor.finalize()

def scrypt_hash_passphrase(passwd,salt,hash_preset,buflen=32):

	# Buflen arg is for brainwallets only, which use this function to generate
	# the seed directly.
	ps = get_hash_params(hash_preset)

	if isinstance(passwd,str):
		passwd = passwd.encode()

	def do_hashlib_scrypt():
		from hashlib import scrypt
		return scrypt(
			password = passwd,
			salt     = salt,
			n        = 2**ps.N,
			r        = ps.r,
			p        = ps.p,
			maxmem   = 0,
			dklen    = buflen )

	def do_standalone_scrypt():
		import scrypt
		return scrypt.hash(
			password = passwd,
			salt     = salt,
			N        = 2**ps.N,
			r        = ps.r,
			p        = ps.p,
			buflen   = buflen )

	if int(hash_preset) > 3:
		msg_r('Hashing passphrase, please wait...')

	# hashlib.scrypt doesn't support N > 14 (hash preset > 3)
	ret = (
		do_standalone_scrypt() if ps.N > 14 or g.force_standalone_scrypt_module else
		do_hashlib_scrypt() )

	if int(hash_preset) > 3:
		msg_r('\b'*34 + ' '*34 + '\b'*34)

	return ret

def make_key(passwd,salt,hash_preset,desc='encryption key',from_what='passphrase',verbose=False):
	if opt.verbose or verbose:
		msg_r(f"Generating {desc}{' from ' + from_what if from_what else ''}...")
	key = scrypt_hash_passphrase(passwd,salt,hash_preset)
	if opt.verbose or verbose: msg('done')
	dmsg(f'Key: {key.hex()}')
	return key

def _get_random_data_from_user(uchars,desc):
	info1 = f"""
		Now we're going to gather some additional input from the keyboard to further
		randomize the random data {desc}.

		An encryption key will be created from this input, and the random data will
		be encrypted using the key.  The resulting data is guaranteed to be at least
		as random as the original random data, so even if you type very predictably
		no harm will be done.

		However, to gain the maximum benefit, try making your input as random as
		possible.  Type slowly and choose your symbols carefully.  Try to use both
		upper and lowercase letters as well as punctuation and numerals. The timings
		between your keystrokes will also be used as a source of entropy, so be as
		random as possible in your timing as well.
	"""
	info2 = f"""
		Please type {uchars} symbols on your keyboard.  What you type will not be displayed
		on the screen.
	"""

	msg(f'Enter {uchars} random symbols' if opt.quiet else
		'\n' + fmt(info1,indent='  ') +
		'\n' + fmt(info2) )

	import time
	from .term import get_char_raw
	key_data = ''
	time_data = []

	for i in range(uchars):
		key_data += get_char_raw(f'\rYou may begin typing.  {uchars-i} symbols left: ')
		time_data.append(time.time())

	msg_r( '\r' if opt.quiet else f'\rThank you.  That’s enough.{" "*18}\n\n' )

	time_data = [f'{t:.22f}'.rstrip('0') for t in time_data]

	avg_prec = sum(len(t.split('.')[1]) for t in time_data) // len(time_data)

	if avg_prec < g.min_time_precision:
		ymsg(f'WARNING: Avg. time precision of only {avg_prec} decimal points. User entropy quality is degraded!')

	ret = key_data + '\n' + '\n'.join(time_data)

	if g.debug:
		msg(f'USER ENTROPY (user input + keystroke timings):\n{ret}')

	line_input('User random data successfully acquired.  Press ENTER to continue: ')

	return ret.encode()

def get_random(length):

	os_rand = os.urandom(length)
	assert len(os_rand) == length, f'OS random number generator returned {len(os_rand)} (!= {length}) bytes!'

	return add_user_random(
		rand_bytes = os_rand,
		desc       = 'from your operating system' )

def add_user_random(
		rand_bytes,
		desc,
		urand = {'data':b'', 'counter':0} ):

	assert type(rand_bytes) == bytes, 'add_user_random_chk1'

	if opt.usr_randchars:

		if not urand['data']:
			from hashlib import sha256
			urand['data'] = sha256(_get_random_data_from_user(opt.usr_randchars,desc)).digest()

		# counter protects against very evil rng that might repeatedly output the same data
		urand['counter'] += 1

		os_rand = os.urandom(8)
		assert len(os_rand) == 8, f'OS random number generator returned {len(os_rand)} (!= 8) bytes!'

		import hmac
		key = hmac.digest(
			urand['data'],
			os_rand + int.to_bytes(urand['counter'],8,'big'),
			'sha256' )

		msg('Encrypting random data {} with ephemeral key #{}'.format( desc, urand['counter'] ))

		return encrypt_data( data=rand_bytes, key=key, desc=desc, verify=False, silent=True )
	else:
		return rand_bytes

def get_hash_preset_from_user(
		hash_preset = g.dfl_hash_preset,
		data_desc = 'data',
		prompt = None ):

	prompt = prompt or (
		f'Enter hash preset for {data_desc},\n' +
		f'or hit ENTER to accept the default value ({hash_preset!r}): ' )

	while True:
		ret = line_input(prompt)
		if ret:
			if ret in hash_presets:
				return ret
			else:
				msg('Invalid input.  Valid choices are {}'.format(', '.join(hash_presets)))
		else:
			return hash_preset

def get_new_passphrase(data_desc,hash_preset,passwd_file,pw_desc='passphrase'):
	message = f"""
			You must choose a passphrase to encrypt your {data_desc} with.
			A key will be generated from your passphrase using a hash preset of '{hash_preset}'.
			Please note that no strength checking of passphrases is performed.
			For an empty passphrase, just hit ENTER twice.
		"""
	if passwd_file:
		from .fileutil import get_words_from_file
		pw = ' '.join(get_words_from_file(
			infile = passwd_file,
			desc = f'{pw_desc} for {data_desc}',
			quiet = pwfile_reuse_warning(passwd_file).warning_shown ))
	else:
		qmsg('\n'+fmt(message,indent='  '))
		if opt.echo_passphrase:
			pw = ' '.join(get_words_from_user(f'Enter {pw_desc} for {data_desc}: '))
		else:
			for i in range(g.passwd_max_tries):
				pw = ' '.join(get_words_from_user(f'Enter {pw_desc} for {data_desc}: '))
				pw_chk = ' '.join(get_words_from_user(f'Repeat {pw_desc}: '))
				dmsg(f'Passphrases: [{pw}] [{pw_chk}]')
				if pw == pw_chk:
					vmsg('Passphrases match')
					break
				else:
					msg('Passphrases do not match.  Try again.')
			else:
				die(2,f'User failed to duplicate passphrase in {g.passwd_max_tries} attempts')

	if pw == '':
		qmsg('WARNING: Empty passphrase')

	return pw

def get_passphrase(data_desc,passwd_file,pw_desc='passphrase'):
	if passwd_file:
		from .fileutil import get_words_from_file
		return ' '.join(get_words_from_file(
			infile = passwd_file,
			desc = f'{pw_desc} for {data_desc}',
			quiet = pwfile_reuse_warning(passwd_file).warning_shown ))
	else:
		return ' '.join(get_words_from_user(f'Enter {pw_desc} for {data_desc}: '))

mmenc_salt_len = 32
mmenc_nonce_len = 32

def mmgen_encrypt(data,desc='data',hash_preset=None):
	salt  = get_random(mmenc_salt_len)
	iv    = get_random(aesctr_iv_len)
	nonce = get_random(mmenc_nonce_len)
	hp    = hash_preset or opt.hash_preset or get_hash_preset_from_user(data_desc=desc)
	m     = ('user-requested','default')[hp=='3']
	vmsg(f'Encrypting {desc}')
	qmsg(f'Using {m} hash preset of {hp!r}')
	passwd = get_new_passphrase(
		data_desc = desc,
		hash_preset = hp,
		passwd_file = opt.passwd_file )
	key    = make_key(passwd,salt,hp)
	from hashlib import sha256
	enc_d  = encrypt_data( sha256(nonce+data).digest() + nonce + data, key, iv, desc=desc )
	return salt+iv+enc_d

def mmgen_decrypt(data,desc='data',hash_preset=None):
	vmsg(f'Preparing to decrypt {desc}')
	dstart = mmenc_salt_len + aesctr_iv_len
	salt   = data[:mmenc_salt_len]
	iv     = data[mmenc_salt_len:dstart]
	enc_d  = data[dstart:]
	hp     = hash_preset or opt.hash_preset or get_hash_preset_from_user(data_desc=desc)
	m  = ('user-requested','default')[hp=='3']
	qmsg(f'Using {m} hash preset of {hp!r}')
	passwd = get_passphrase(
		data_desc = desc,
		passwd_file = opt.passwd_file )
	key    = make_key(passwd,salt,hp)
	dec_d  = decrypt_data( enc_d, key, iv, desc )
	sha256_len = 32
	from hashlib import sha256
	if dec_d[:sha256_len] == sha256(dec_d[sha256_len:]).digest():
		vmsg('OK')
		return dec_d[sha256_len+mmenc_nonce_len:]
	else:
		msg('Incorrect passphrase or hash preset')
		return False

def mmgen_decrypt_retry(d,desc='data'):
	while True:
		d_dec = mmgen_decrypt(d,desc)
		if d_dec: return d_dec
		msg('Trying again...')
