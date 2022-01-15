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
crypto.py:  Cryptographic and related routines for the MMGen suite
"""

from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
from cryptography.hazmat.backends import default_backend
from hashlib import sha256
from .common import *

mmenc_ext = 'mmenc'

def sha256_rounds(s,n):
	for i in range(n):
		s = sha256(s).digest()
	return s

def scramble_seed(seed,scramble_key):
	import hmac
	step1 = hmac.digest(seed,scramble_key,'sha256')
	if g.debug:
		msg(f'Seed:  {seed.hex()!r}\nScramble key: {scramble_key}\nScrambled seed: {step1.hex()}\n')
	return sha256_rounds(step1,g.scramble_hash_rounds)

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

def encrypt_data(data,key,iv=g.aesctr_dfl_iv,desc='data',verify=True):
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
		vmsg('done')

	return enc_data

def decrypt_data(enc_data,key,iv=g.aesctr_dfl_iv,desc='data'):
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
	return add_user_random(
		rand_bytes = os.urandom(length),
		desc       = 'generated by your operating system' )

def add_user_random(rand_bytes,desc):
	assert type(rand_bytes) == bytes, 'add_user_random_chk1'
	if opt.usr_randchars:
		if not g.user_entropy:
			g.user_entropy = sha256(_get_random_data_from_user(opt.usr_randchars,desc)).digest()
			urand_desc = 'user-supplied entropy'
		else:
			urand_desc = 'saved user-supplied entropy'
		key = make_key(g.user_entropy,b'','2',from_what=urand_desc,verbose=True)
		msg(f'Encrypting random data {desc} with key')
		return encrypt_data(rand_bytes,key,desc=desc,verify=False)
	else:
		return rand_bytes

def get_hash_preset_from_user(hp=g.dfl_hash_preset,desc='data'):
	while True:
		ret = line_input(
			f'Enter hash preset for {desc},\n' +
			f'or hit ENTER to accept the default value ({hp!r}): ' )
		if ret:
			if ret in g.hash_presets:
				return ret
			else:
				msg(f'Invalid input.  Valid choices are {", ".join(g.hash_presets)}')
				continue
		else:
			return hp

def get_new_passphrase(desc,passchg=False):
	pw_desc = f"{'new ' if passchg else ''}passphrase for {desc}"
	if opt.passwd_file:
		pw = ' '.join(get_words_from_file(opt.passwd_file,pw_desc))
	elif opt.echo_passphrase:
		pw = ' '.join(get_words_from_user(f'Enter {pw_desc}: '))
	else:
		for i in range(g.passwd_max_tries):
			pw = ' '.join(get_words_from_user(f'Enter {pw_desc}: '))
			pw_chk = ' '.join(get_words_from_user('Repeat passphrase: '))
			dmsg(f'Passphrases: [{pw}] [{pw_chk}]')
			if pw == pw_chk:
				vmsg('Passphrases match'); break
			else: msg('Passphrases do not match.  Try again.')
		else:
			die(2,f'User failed to duplicate passphrase in {g.passwd_max_tries} attempts')

	if pw == '':
		qmsg('WARNING: Empty passphrase')

	return pw

def get_passphrase(desc,passchg=False):
	pw_desc = f"{'old ' if passchg else ''}passphrase for {desc}"
	if opt.passwd_file:
		pwfile_reuse_warning(opt.passwd_file)
		return ' '.join(get_words_from_file(opt.passwd_file,pw_desc))
	else:
		return ' '.join(get_words_from_user(f'Enter {pw_desc}: '))

_salt_len,_sha256_len,_nonce_len = (32,32,32)

def mmgen_encrypt(data,desc='data',hash_preset=''):
	salt  = get_random(_salt_len)
	iv    = get_random(g.aesctr_iv_len)
	nonce = get_random(_nonce_len)
	hp    = hash_preset or opt.hash_preset or get_hash_preset_from_user('3',desc)
	m     = ('user-requested','default')[hp=='3']
	vmsg(f'Encrypting {desc}')
	qmsg(f'Using {m} hash preset of {hp!r}')
	passwd = get_new_passphrase(desc)
	key    = make_key(passwd,salt,hp)
	enc_d  = encrypt_data(sha256(nonce+data).digest() + nonce + data, key, iv, desc=desc)
	return salt+iv+enc_d

def mmgen_decrypt(data,desc='data',hash_preset=''):
	vmsg(f'Preparing to decrypt {desc}')
	dstart = _salt_len + g.aesctr_iv_len
	salt   = data[:_salt_len]
	iv     = data[_salt_len:dstart]
	enc_d  = data[dstart:]
	hp     = hash_preset or opt.hash_preset or get_hash_preset_from_user('3',desc)
	m  = ('user-requested','default')[hp=='3']
	qmsg(f'Using {m} hash preset of {hp!r}')
	passwd = get_passphrase(desc)
	key    = make_key(passwd,salt,hp)
	dec_d  = decrypt_data(enc_d,key,iv,desc)
	if dec_d[:_sha256_len] == sha256(dec_d[_sha256_len:]).digest():
		vmsg('OK')
		return dec_d[_sha256_len+_nonce_len:]
	else:
		msg('Incorrect passphrase or hash preset')
		return False

def mmgen_decrypt_retry(d,desc='data'):
	while True:
		d_dec = mmgen_decrypt(d,desc)
		if d_dec: return d_dec
		msg('Trying again...')
