#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.xmr.keygen: Monero public key generation backends for the MMGen suite
"""

from ...key import PubKey
from ...keygen import keygen_base

class backend:

	class base(keygen_base):

		def __init__(self, cfg):
			super().__init__(cfg)
			from ...proto.xmr.params import mainnet
			self.proto_cls = mainnet
			from ...util2 import get_keccak
			self.keccak_256 = get_keccak(cfg)

		def to_viewkey(self, privkey):
			return self.proto_cls.preprocess_key(
				self.proto_cls,
				self.keccak_256(privkey).digest(),
				None)

	class nacl(base):

		def __init__(self, cfg):
			super().__init__(cfg)
			from nacl.bindings import crypto_scalarmult_ed25519_base_noclamp
			self.scalarmultbase = crypto_scalarmult_ed25519_base_noclamp

		def to_pubkey(self, privkey):
			return PubKey(
				self.scalarmultbase(privkey) +
				self.scalarmultbase(self.to_viewkey(privkey)),
				compressed = privkey.compressed)
