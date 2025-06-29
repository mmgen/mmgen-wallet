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
proto.secp256k1.util: secp256k1 elliptic curve utility functions
"""

def sign_message(*, sign_doc, sec_bytes):
	from hashlib import sha256
	from .secp256k1 import sign_msghash
	return sign_msghash(
		sha256(bytes(sign_doc)).digest(),
		sec_bytes)[0]
