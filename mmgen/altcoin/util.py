#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
altcoin.util: various altcoin-related utilities
"""

from ..util import die

def decrypt_keystore(data, passwd, *, mac_algo=None, mac_params={}):
	"""
	Decrypt the encrypted data in a cross-chain keystore
	Returns the decrypted data as a bytestring
	"""

	cdata = data['crypto']
	parms = cdata['kdfparams']

	valid_kdfs = ['scrypt', 'pbkdf2']
	valid_ciphers = ['aes-128-ctr', 'aes-256-ctr']

	if (kdf := cdata['kdf']) not in valid_kdfs:
		die(1, f'unsupported key derivation function {kdf!r} (must be one of {valid_kdfs})')

	if (cipher := cdata['cipher']) not in valid_ciphers:
		die(1, f'unsupported cipher {cipher!r} (must be one of {valid_ciphers})')

	# Derive encryption key from password:
	if kdf == 'scrypt':
		if not mac_algo:
			die(1, 'the ‘mac_algo’ parameter is required for scrypt kdf')
		from hashlib import scrypt
		hashed_pw = scrypt(
			password = passwd,
			salt     = bytes.fromhex(parms['salt']),
			n        = parms['n'],
			r        = parms['r'],
			p        = parms['p'],
			maxmem   = 0,
			dklen    = parms['dklen'])
	elif kdf == 'pbkdf2':
		if (prf := parms.get('prf')) != 'hmac-sha256':
			die(1, f"unsupported hash function {prf!r} (must be 'hmac-sha256')")
		from hashlib import pbkdf2_hmac, blake2b
		hashed_pw = pbkdf2_hmac(
			hash_name  = 'sha256',
			password   = passwd,
			salt       = bytes.fromhex(parms['salt']),
			iterations = parms['c'],
			dklen      = parms['dklen'])
		# see:
		#   https://github.com/xchainjs/xchainjs-lib.git
		#   https://github.com/xchainjs/foundry-primitives-js.git
		mac_algo = mac_algo or blake2b
		mac_params = mac_params or {'digest_size': 32}

	mac = mac_algo(
		hashed_pw[16:32] + bytes.fromhex(cdata['ciphertext']),
		**mac_params
	).digest().hex()

	if mac != cdata['mac']:
		die(1, 'incorrect password')

	# Decrypt data:
	from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
	from cryptography.hazmat.backends import default_backend
	cipher_len = int(cipher.split('-')[1]) // 8
	c = Cipher(
		algorithms.AES(hashed_pw[:cipher_len]),
		modes.CTR(bytes.fromhex(cdata['cipherparams']['iv'])),
		backend = default_backend())
	encryptor = c.encryptor()
	return encryptor.update(bytes.fromhex(cdata['ciphertext'])) + encryptor.finalize()
