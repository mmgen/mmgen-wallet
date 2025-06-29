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
proto.eth.util: various utilities for Ethereum base protocol
"""

from ...util2 import get_keccak

v_base = 27

def decrypt_geth_keystore(cfg, wallet_fn, passwd, *, check_addr=True):
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
	from ..secp256k1.secp256k1 import sign_msghash
	sig, recid = sign_msghash(hash_message(cfg, message, msghash_type), key)
	return sig.hex() + '{:02x}'.format(v_base + recid)

def ec_recover_pubkey(cfg, message, sig, msghash_type):
	"""
	Given a message and signature, recover the public key associated with the private key
	used to make the signature

	Conforms to the standard defined by the Geth `eth_sign` JSON-RPC call
	"""
	from ..secp256k1.secp256k1 import pubkey_recover
	sig_bytes = bytes.fromhex(sig)
	return pubkey_recover(
		hash_message(cfg, message, msghash_type),
		sig_bytes[:64],
		sig_bytes[64] - v_base,
		False).hex()

def compute_contract_addr(cfg, deployer_addr, nonce):
	from . import rlp
	encoded = rlp.encode([bytes.fromhex(deployer_addr), nonce])
	return get_keccak(cfg)(encoded).hexdigest()[-40:]
