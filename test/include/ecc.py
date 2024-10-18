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
test.include.ecc: elliptic curve utilities for the MMGen test suite
"""

import ecdsa
from mmgen.proto.secp256k1.keygen import pubkey_format

def _pubkey_to_pub_point(vk_bytes):
	try:
		return ecdsa.VerifyingKey.from_string(vk_bytes, curve=ecdsa.curves.SECP256k1).pubkey.point
	except Exception as e:
		raise ValueError(f'invalid pubkey {vk_bytes.hex()}\n    {type(e).__name__}: {e}')

def _check_pub_point(pub_point, vk_bytes, addend_bytes=None):
	if pub_point is ecdsa.ellipticcurve.INFINITY:
		raise ValueError(
			'pubkey {}{} produced key with point at infinity!'.format(
				vk_bytes.hex(),
				'' if addend_bytes is None else f' + {addend_bytes.hex()}'))

def pubkey_check_pyecdsa(vk_bytes):
	_check_pub_point(_pubkey_to_pub_point(vk_bytes), vk_bytes)

def pubkey_tweak_add_pyecdsa(vk_bytes, pk_addend_bytes):
	pk_addend = int.from_bytes(pk_addend_bytes, byteorder='big')
	point_sum = (
		_pubkey_to_pub_point(vk_bytes) +
		ecdsa.SigningKey.from_secret_exponent(pk_addend, curve=ecdsa.SECP256k1).verifying_key.pubkey.point
	)
	_check_pub_point(point_sum, vk_bytes, pk_addend_bytes)
	return pubkey_format(
		ecdsa.VerifyingKey.from_public_point(point_sum, curve=ecdsa.curves.SECP256k1).to_string(),
		compressed = len(vk_bytes) == 33)
