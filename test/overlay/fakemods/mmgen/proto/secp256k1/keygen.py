# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.overlay.fakemods.mmgen.proto.secp256k1.keygen:
	testing secp256k1 public key generation backends for the MMGen suite
"""

from .keygen_orig import *

def overlay_fake_pubkey_format(vk_bytes, compressed):
	# if compressed, discard Y coord, replace with appropriate version byte
	# even y: <0, odd y: >0 -- https://bitcointalk.org/index.php?topic=129652.0
	return (b'\x02', b'\x03')[vk_bytes[-1] & 1] + vk_bytes[:32] if compressed else b'\x04' + vk_bytes

class overlay_fake_backend:

	class python_ecdsa(keygen_base):

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
				return overlay_fake_pubkey_format(pk.verifying_key.to_string(), compressed)

			return PubKey(
				s = privnum2pubkey(int.from_bytes(privkey, 'big'), compressed=privkey.compressed),
				compressed = privkey.compressed)

backend.python_ecdsa = overlay_fake_backend.python_ecdsa
