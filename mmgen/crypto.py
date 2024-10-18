#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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
crypto: Random number, password hashing and symmetric encryption routines for the MMGen suite
"""

import os
from collections import namedtuple

from .cfg import gc
from .util import msg, msg_r, ymsg, fmt, die, make_chksum_8, oneshot_warning

class Crypto:

	mmenc_ext = 'mmenc'
	scramble_hash_rounds = 10

	salt_len       = 16
	aesctr_iv_len  = 16
	aesctr_dfl_iv  = int.to_bytes(1, aesctr_iv_len, 'big')
	hincog_chk_len = 8

	mmenc_salt_len = 32
	mmenc_nonce_len = 32

	# Scrypt params: 'id_num': [N, r, p] (N is an exponent of two)
	# NB: hashlib.scrypt in Python (>=v3.6) supports max N value of 14.  This means that
	# for hash presets > 3 the standalone scrypt library must be used!
	_hp = namedtuple('scrypt_preset', ['N', 'r', 'p'])
	hash_presets = {
		'1': _hp(12, 8, 1),
		'2': _hp(13, 8, 4),
		'3': _hp(14, 8, 8),
		'4': _hp(15, 8, 12),
		'5': _hp(16, 8, 16),
		'6': _hp(17, 8, 20),
		'7': _hp(18, 8, 24),
	}

	class pwfile_reuse_warning(oneshot_warning):
		message = 'Reusing passphrase from file {!r} at user request'
		def __init__(self, fn):
			oneshot_warning.__init__(self, div=fn, fmt_args=[fn], reverse=True)

	def pwfile_used(self, passwd_file):
		if hasattr(self, '_pwfile_used'):
			self.pwfile_reuse_warning(passwd_file)
			return True
		else:
			self._pwfile_used = True
			return False

	def __init__(self, cfg):
		self.cfg = cfg
		self.util = cfg._util

	def get_hash_params(self, hash_preset):
		if hash_preset in self.hash_presets:
			return self.hash_presets[hash_preset] # N, r, p
		else: # Shouldn't be here
			die(3, f"{hash_preset}: invalid 'hash_preset' value")

	def sha256_rounds(self, s):
		from hashlib import sha256
		for _ in range(self.scramble_hash_rounds):
			s = sha256(s).digest()
		return s

	def scramble_seed(self, seed, scramble_key):
		import hmac
		step1 = hmac.digest(seed, scramble_key, 'sha256')
		if self.cfg.debug:
			msg(f'Seed:  {seed.hex()!r}\nScramble key: {scramble_key}\nScrambled seed: {step1.hex()}\n')
		return self.sha256_rounds(step1)

	def encrypt_seed(self, data, key, desc='seed'):
		return self.encrypt_data(data, key, desc=desc)

	def decrypt_seed(self, enc_seed, key, seed_id, key_id):
		self.util.vmsg_r('Checking key...')
		chk1 = make_chksum_8(key)
		if key_id:
			if not self.util.compare_chksums(key_id, 'key ID', chk1, 'computed'):
				msg('Incorrect passphrase or hash preset')
				return False

		dec_seed = self.decrypt_data(enc_seed, key, desc='seed')
		chk2     = make_chksum_8(dec_seed)
		if seed_id:
			if self.util.compare_chksums(seed_id, 'Seed ID', chk2, 'decrypted seed'):
				self.util.qmsg('Passphrase is OK')
			else:
				if not self.cfg.debug:
					msg_r('Checking key ID...')
					if self.util.compare_chksums(key_id, 'key ID', chk1, 'computed'):
						msg('Key ID is correct but decryption of seed failed')
					else:
						msg('Incorrect passphrase or hash preset')
				self.util.vmsg('')
				return False

		self.util.dmsg(f'Decrypted seed: {dec_seed.hex()}')
		return dec_seed

	def encrypt_data(
			self,
			data,
			key,
			iv     = aesctr_dfl_iv,
			desc   = 'data',
			verify = True,
			silent = False):

		from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
		from cryptography.hazmat.backends import default_backend
		if not silent:
			self.util.vmsg(f'Encrypting {desc}')
		c = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
		encryptor = c.encryptor()
		enc_data = encryptor.update(data) + encryptor.finalize()

		if verify:
			self.util.vmsg_r(f'Performing a test decryption of the {desc}...')
			c = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
			encryptor = c.encryptor()
			dec_data = encryptor.update(enc_data) + encryptor.finalize()
			if dec_data != data:
				die(2, f'ERROR.\nDecrypted {desc} doesn’t match original {desc}')
			if not silent:
				self.util.vmsg('done')

		return enc_data

	def decrypt_data(
			self,
			enc_data,
			key,
			iv   = aesctr_dfl_iv,
			desc = 'data'):

		from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
		from cryptography.hazmat.backends import default_backend
		self.util.vmsg_r(f'Decrypting {desc} with key...')
		c = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
		encryptor = c.encryptor()
		return encryptor.update(enc_data) + encryptor.finalize()

	def scrypt_hash_passphrase(
			self,
			passwd,
			salt,
			hash_preset,
			buflen = 32):

		# Buflen arg is for brainwallets only, which use this function to generate
		# the seed directly.
		ps = self.get_hash_params(hash_preset)

		if isinstance(passwd, str):
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
				dklen    = buflen)

		def do_standalone_scrypt():
			import scrypt
			return scrypt.hash(
				password = passwd,
				salt     = salt,
				N        = 2**ps.N,
				r        = ps.r,
				p        = ps.p,
				buflen   = buflen)

		if int(hash_preset) > 3:
			msg_r('Hashing passphrase, please wait...')

		# hashlib.scrypt doesn't support N > 14 (hash preset > 3)
		ret = (
			do_standalone_scrypt() if ps.N > 14 or self.cfg.force_standalone_scrypt_module else
			do_hashlib_scrypt())

		if int(hash_preset) > 3:
			msg_r('\b'*34 + ' '*34 + '\b'*34)

		return ret

	def make_key(
			self,
			passwd,
			salt,
			hash_preset,
			desc      = 'encryption key',
			from_what = 'passphrase',
			verbose   = False):

		if self.cfg.verbose or verbose:
			msg_r(f"Generating {desc}{' from ' + from_what if from_what else ''}...")
		key = self.scrypt_hash_passphrase(passwd, salt, hash_preset)
		if self.cfg.verbose or verbose:
			msg('done')
		self.util.dmsg(f'Key: {key.hex()}')
		return key

	def _get_random_data_from_user(self, uchars=None, desc='data'):

		if uchars is None:
			uchars = self.cfg.usr_randchars

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

		msg(f'Enter {uchars} random symbols' if self.cfg.quiet else
			'\n' + fmt(info1, indent='  ') +
			'\n' + fmt(info2))

		import time
		from .term import get_char_raw
		key_data = ''
		time_data = []

		for i in range(uchars):
			key_data += get_char_raw(f'\rYou may begin typing.  {uchars-i} symbols left: ')
			time_data.append(time.time())

		msg_r('\r' if self.cfg.quiet else f'\rThank you.  That’s enough.{" "*18}\n\n')

		time_data = [f'{t:.22f}'.rstrip('0') for t in time_data]

		avg_prec = sum(len(t.split('.')[1]) for t in time_data) // len(time_data)

		if avg_prec < gc.min_time_precision:
			ymsg(f'WARNING: Avg. time precision of only {avg_prec} decimal points. User entropy quality is degraded!')

		ret = key_data + '\n' + '\n'.join(time_data)

		if self.cfg.debug:
			msg(f'USER ENTROPY (user input + keystroke timings):\n{ret}')

		from .ui import line_input
		line_input(self.cfg, 'User random data successfully acquired.  Press ENTER to continue: ')

		return ret.encode()

	def get_random(self, length):

		os_rand = os.urandom(length)
		assert len(os_rand) == length, f'OS random number generator returned {len(os_rand)} (!= {length}) bytes!'

		return self.add_user_random(
			rand_bytes = os_rand,
			desc       = 'from your operating system')

	def add_user_random(
			self,
			rand_bytes,
			desc,
			urand = {'data':b'', 'counter':0}):

		assert type(rand_bytes) is bytes, 'add_user_random_chk1'

		if self.cfg.usr_randchars:

			if not urand['data']:
				from hashlib import sha256
				urand['data'] = sha256(self._get_random_data_from_user(desc=desc)).digest()

			# counter protects against very evil rng that might repeatedly output the same data
			urand['counter'] += 1

			os_rand = os.urandom(8)
			assert len(os_rand) == 8, f'OS random number generator returned {len(os_rand)} (!= 8) bytes!'

			import hmac
			key = hmac.digest(
				urand['data'],
				os_rand + int.to_bytes(urand['counter'], 8, 'big'),
				'sha256')

			msg(f'Encrypting random data {desc} with ephemeral key #{urand["counter"]}')

			return self.encrypt_data(data=rand_bytes, key=key, desc=desc, verify=False, silent=True)
		else:
			return rand_bytes

	def get_hash_preset_from_user(
			self,
			old_preset = gc.dfl_hash_preset,
			data_desc  = 'data',
			prompt     = None):

		prompt = prompt or (
			f'Enter hash preset for {data_desc}, \n' +
			f'or hit ENTER to accept the default value ({old_preset!r}): ')

		from .ui import line_input
		while True:
			ret = line_input(self.cfg, prompt)
			if ret:
				if ret in self.hash_presets:
					return ret
				else:
					msg('Invalid input.  Valid choices are {}'.format(', '.join(self.hash_presets)))
			else:
				return old_preset

	def get_new_passphrase(self, data_desc, hash_preset, passwd_file, pw_desc='passphrase'):
		message = f"""
				You must choose a passphrase to encrypt your {data_desc} with.
				A key will be generated from your passphrase using a hash preset of '{hash_preset}'.
				Please note that no strength checking of passphrases is performed.
				For an empty passphrase, just hit ENTER twice.
			"""
		if passwd_file:
			from .fileutil import get_words_from_file
			pw = ' '.join(get_words_from_file(
				cfg    = self.cfg,
				infile = passwd_file,
				desc   = f'{pw_desc} for {data_desc}',
				quiet  = self.pwfile_used(passwd_file)))
		else:
			self.util.qmsg('\n'+fmt(message, indent='  '))
			from .ui import get_words_from_user
			if self.cfg.echo_passphrase:
				pw = ' '.join(get_words_from_user(self.cfg, f'Enter {pw_desc} for {data_desc}: '))
			else:
				for _ in range(gc.passwd_max_tries):
					pw = ' '.join(get_words_from_user(self.cfg, f'Enter {pw_desc} for {data_desc}: '))
					pw_chk = ' '.join(get_words_from_user(self.cfg, f'Repeat {pw_desc}: '))
					self.util.dmsg(f'Passphrases: [{pw}] [{pw_chk}]')
					if pw == pw_chk:
						self.util.vmsg('Passphrases match')
						break
					msg('Passphrases do not match.  Try again.')
				else:
					die(2, f'User failed to duplicate passphrase in {gc.passwd_max_tries} attempts')

		if pw == '':
			self.util.qmsg('WARNING: Empty passphrase')

		return pw

	def get_passphrase(self, data_desc, passwd_file, pw_desc='passphrase'):
		if passwd_file:
			from .fileutil import get_words_from_file
			return ' '.join(get_words_from_file(
				cfg    = self.cfg,
				infile = passwd_file,
				desc   = f'{pw_desc} for {data_desc}',
				quiet  = self.pwfile_used(passwd_file)))
		else:
			from .ui import get_words_from_user
			return ' '.join(get_words_from_user(self.cfg, f'Enter {pw_desc} for {data_desc}: '))

	def mmgen_encrypt(self, data, desc='data', hash_preset=None):
		salt  = self.get_random(self.mmenc_salt_len)
		iv    = self.get_random(self.aesctr_iv_len)
		nonce = self.get_random(self.mmenc_nonce_len)
		hp    = hash_preset or self.cfg.hash_preset or self.get_hash_preset_from_user(data_desc=desc)
		m     = ('user-requested', 'default')[hp=='3']
		self.util.vmsg(f'Encrypting {desc}')
		self.util.qmsg(f'Using {m} hash preset of {hp!r}')
		passwd = self.get_new_passphrase(
			data_desc = desc,
			hash_preset = hp,
			passwd_file = self.cfg.passwd_file)
		key    = self.make_key(passwd, salt, hp)
		from hashlib import sha256
		enc_d  = self.encrypt_data(sha256(nonce+data).digest() + nonce + data, key, iv, desc=desc)
		return salt+iv+enc_d

	def mmgen_decrypt(self, data, desc='data', hash_preset=None):
		self.util.vmsg(f'Preparing to decrypt {desc}')
		dstart = self.mmenc_salt_len + self.aesctr_iv_len
		salt   = data[:self.mmenc_salt_len]
		iv     = data[self.mmenc_salt_len:dstart]
		enc_d  = data[dstart:]
		hp     = hash_preset or self.cfg.hash_preset or self.get_hash_preset_from_user(data_desc=desc)
		m  = ('user-requested', 'default')[hp=='3']
		self.util.qmsg(f'Using {m} hash preset of {hp!r}')
		passwd = self.get_passphrase(
			data_desc = desc,
			passwd_file = self.cfg.passwd_file)
		key    = self.make_key(passwd, salt, hp)
		dec_d  = self.decrypt_data(enc_d, key, iv, desc)
		sha256_len = 32
		from hashlib import sha256
		if dec_d[:sha256_len] == sha256(dec_d[sha256_len:]).digest():
			self.util.vmsg('OK')
			return dec_d[sha256_len+self.mmenc_nonce_len:]
		else:
			msg('Incorrect passphrase or hash preset')
			return False

	def mmgen_decrypt_retry(self, d, desc='data'):
		while True:
			d_dec = self.mmgen_decrypt(d, desc)
			if d_dec:
				return d_dec
			msg('Trying again...')
