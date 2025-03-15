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
			try:
				from .secp256k1 import pubkey_gen
				if not pubkey_gen(bytes.fromhex('deadbeef'*8), 1):
					from ...util import die
					die('ExtensionModuleError',
						'Unable to execute pubkey_gen() from secp256k1 extension module')
				return cls.__name__
			except ImportError as e:
				if not silent:
					from ...util import ymsg
					ymsg(str(e))
				cfg._util.qmsg('Using (slow) native Python ECDSA library for public key generation')
				return 'python_ecdsa'

	class python_ecdsa(keygen_base):

		production_safe = False

		def __init__(self, cfg):
			super().__init__(cfg)
			import ecdsa
			self.ecdsa = ecdsa

		def to_pubkey(self, privkey):
			"""
			devdoc/guide_wallets.md:
			Uncompressed public keys start with 0x04; compressed public keys begin with 0x03 or
			0x02 depending on whether they're greater or less than the midpoint of the curve.
			"""
			def privnum2pubkey(numpriv, *, compressed=False):
				pk = self.ecdsa.SigningKey.from_secret_exponent(numpriv, curve=self.ecdsa.SECP256k1)
				# vk_bytes = x (32 bytes) + y (32 bytes) (unsigned big-endian)
				return pubkey_format(pk.verifying_key.to_string(), compressed)

			return PubKey(
				s = privnum2pubkey(int.from_bytes(privkey, 'big'), compressed=privkey.compressed),
				compressed = privkey.compressed)
