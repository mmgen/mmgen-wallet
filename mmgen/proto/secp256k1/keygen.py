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
proto.secp256k1.keygen: secp256k1 public key generation backends for the MMGen suite
"""

from ...key import PubKey
from ...keygen import keygen_base

def pubkey_format(vk_bytes, compressed):
	# if compressed, discard Y coord, replace with appropriate version byte
	# even y: <0, odd y: >0 -- https://bitcointalk.org/index.php?topic=129652.0
	return (b'\x02', b'\x03')[vk_bytes[-1] & 1] + vk_bytes[:32] if compressed else b'\x04' + vk_bytes

class backend:

	class libsecp256k1(keygen_base):

		production_safe = True

		def __init__(self, cfg):
			super().__init__(cfg)
			from .secp256k1 import pubkey_gen
			self.pubkey_gen = pubkey_gen

		def to_pubkey(self, privkey):
			return PubKey(
				s = self.pubkey_gen(privkey, int(privkey.compressed)),
				compressed = privkey.compressed)

		@classmethod
		def get_clsname(cls, cfg, *, silent=False):
			from .secp256k1 import pubkey_gen
			if not pubkey_gen(bytes.fromhex('deadbeef'*8), 1):
				from ...util import die
				die('ExtensionModuleError',
					'Unable to execute pubkey_gen() from secp256k1 extension module')
			return cls.__name__
