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
proto.zec.keygen: Zcash-Z public key generation backend for the MMGen suite
"""

from ...key import PubKey
from ...keygen import keygen_base

class backend:

	class nacl(keygen_base):

		production_safe = True

		def __init__(self, cfg):
			super().__init__(cfg)
			from nacl.bindings import crypto_scalarmult_base
			self.crypto_scalarmult_base = crypto_scalarmult_base
			from ...sha2 import Sha256
			self.Sha256 = Sha256

		def zhash256(self, s, t):
			s = bytearray(s + bytes(32))
			s[0] |= 0xc0
			s[32] = t
			return self.Sha256(s, preprocess=False).digest()

		def to_pubkey(self, privkey):
			return PubKey(
				self.zhash256(privkey, 0)
				+ self.crypto_scalarmult_base(self.zhash256(privkey, 1)),
				compressed = privkey.compressed
			)

		def to_viewkey(self, privkey):
			vk = bytearray(self.zhash256(privkey, 0) + self.zhash256(privkey, 1))
			vk[32] &= 0xf8
			vk[63] &= 0x7f
			vk[63] |= 0x40
			return vk
