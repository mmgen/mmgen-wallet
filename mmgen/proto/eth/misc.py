#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.eth.misc: miscellaneous utilities for Ethereum base protocol
"""

from ...util2 import get_keccak

def decrypt_geth_keystore(cfg, wallet_fn, passwd, check_addr=True):
	"""
	Decrypt the encrypted private key in a Geth keystore wallet, returning the decrypted key
	"""
	import json

	with open(wallet_fn) as fp:
		wallet_data = json.loads(fp.read())

	from ...altcoin.util import decrypt_keystore
	key = decrypt_keystore(
		wallet_data,
		passwd,
		mac_algo = get_keccak())

	# Optionally check that Ethereum private key produces correct address
	if check_addr:
		from ...tool.coin import tool_cmd
		from ...protocol import init_proto
		t = tool_cmd(cfg=cfg, proto=init_proto(cfg, 'eth'))
		addr = t.wif2addr(key.hex())
		addr_chk = wallet_data['address']
		assert addr == addr_chk, f'incorrect address: ({addr} != {addr_chk})'

	return key

def hash_message(cfg, message, msghash_type):
	return get_keccak(cfg)(
		{
			'raw': message,
			'eth_sign': '\x19Ethereum Signed Message:\n{}{}'.format(len(message), message),
		}[msghash_type].encode()
	).digest()

def ec_sign_message_with_privkey(cfg, message, key, msghash_type):
	"""
	Sign an arbitrary string with an Ethereum private key, returning the signature

	Conforms to the standard defined by the Geth `eth_sign` JSON-RPC call
	"""
	from py_ecc.secp256k1 import ecdsa_raw_sign
	v, r, s = ecdsa_raw_sign(hash_message(cfg, message, msghash_type), key)
	return '{:064x}{:064x}{:02x}'.format(r, s, v)

def ec_recover_pubkey(cfg, message, sig, msghash_type):
	"""
	Given a message and signature, recover the public key associated with the private key
	used to make the signature

	Conforms to the standard defined by the Geth `eth_sign` JSON-RPC call
	"""
	from py_ecc.secp256k1 import ecdsa_raw_recover
	r, s, v = (sig[:64], sig[64:128], sig[128:])
	return '{:064x}{:064x}'.format(
		*ecdsa_raw_recover(
			hash_message(cfg, message, msghash_type), tuple(int(hexstr, 16) for hexstr in (v, r, s)))
	)
