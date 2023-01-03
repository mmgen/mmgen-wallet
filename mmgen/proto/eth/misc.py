#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
proto.eth.misc: miscellaneous utilities for Ethereum base protocol
"""

from ...util import die
from ...util2 import get_keccak

def extract_key_from_geth_keystore_wallet(wallet_fn,passwd,check_addr=True):
	"""
	Decrypt the encrypted private key in a Geth keystore wallet, returning the decrypted key
	"""
	import json

	with open(wallet_fn) as fp:
		wallet_data = json.loads(fp.read())

	cdata = wallet_data['crypto']

	assert cdata['cipher'] == 'aes-128-ctr', f'incorrect cipher: "{cdata["cipher"]}" != "aes-128-ctr"'
	assert cdata['kdf'] == 'scrypt', f'incorrect KDF: "{cdata["kdf"]}" != "scrypt"'

	# Derive encryption key from password
	from hashlib import scrypt
	sp = cdata['kdfparams']
	hashed_pw = scrypt(
		password = passwd,
		salt     = bytes.fromhex( sp['salt'] ),
		n        = sp['n'],
		r        = sp['r'],
		p        = sp['p'],
		maxmem   = 0,
		dklen    = sp['dklen'] )

	# Check password by comparing generated MAC to stored MAC
	mac_chk = get_keccak()(hashed_pw[16:32] + bytes.fromhex( cdata['ciphertext'] )).digest().hex()
	if mac_chk != cdata['mac']:
		die(1,'Incorrect passphrase')

	# Decrypt Ethereum private key
	from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
	from cryptography.hazmat.backends import default_backend
	c = Cipher(
		algorithms.AES(hashed_pw[:16]),
		modes.CTR(bytes.fromhex( cdata['cipherparams']['iv'] )),
		backend = default_backend() )
	encryptor = c.encryptor()
	key = encryptor.update( bytes.fromhex(cdata['ciphertext']) ) + encryptor.finalize()

	# Optionally check that Ethereum private key produces correct address
	if check_addr:
		from ...tool.coin import tool_cmd
		from ...protocol import init_proto
		t = tool_cmd( proto=init_proto('eth') )
		addr = t.wif2addr(key.hex())
		addr_chk = wallet_data['address']
		assert addr == addr_chk, f'incorrect address: ({addr} != {addr_chk})'

	return key

def hash_message(message,msghash_type):
	return get_keccak()(
		{
			'raw': message,
			'eth_sign': '\x19Ethereum Signed Message:\n{}{}'.format( len(message), message ),
		}[msghash_type].encode()
	).digest()

def ec_sign_message_with_privkey(message,key,msghash_type):
	"""
	Sign an arbitrary string with an Ethereum private key, returning the signature

	Conforms to the standard defined by the Geth `eth_sign` JSON-RPC call
	"""
	from py_ecc.secp256k1 import ecdsa_raw_sign
	v,r,s = ecdsa_raw_sign( hash_message(message,msghash_type), key )
	return '{:064x}{:064x}{:02x}'.format(r,s,v)

def ec_recover_pubkey(message,sig,msghash_type):
	"""
	Given a message and signature, recover the public key associated with the private key
	used to make the signature

	Conforms to the standard defined by the Geth `eth_sign` JSON-RPC call
	"""
	from py_ecc.secp256k1 import ecdsa_raw_recover
	r,s,v = ( sig[:64], sig[64:128], sig[128:] )
	return '{:064x}{:064x}'.format(
		*ecdsa_raw_recover( hash_message(message,msghash_type), tuple(int(hexstr,16) for hexstr in (v,r,s)) )
	)
