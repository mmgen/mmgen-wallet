# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.overlay.fakemods.mmgen.proto.xmr.keygen:
	testing Monero public key generation backends for the MMGen suite
"""

from .keygen_orig import *

class overlay_fake_backend:

	class ed25519(backend.base):

		def __init__(self, cfg):
			super().__init__(cfg)
			from ...contrib.ed25519 import edwards, encodepoint, B, scalarmult
			self.edwards     = edwards
			self.encodepoint = encodepoint
			self.B           = B
			self.scalarmult  = scalarmult

		def scalarmultbase(self, privnum):
			"""
			Source and license for scalarmultbase function:
			  https://github.com/bigreddmachine/MoneroPy/blob/master/moneropy/crypto/ed25519.py
			Copyright (c) 2014-2016, The Monero Project
			All rights reserved.
			"""
			if privnum == 0:
				return [0, 1]
			Q = self.scalarmult(self.B, privnum//2)
			Q = self.edwards(Q, Q)
			if privnum & 1:
				Q = self.edwards(Q, self.B)
			return Q

		@staticmethod
		def rev_bytes2int(in_bytes):
			return int.from_bytes(in_bytes[::-1], 'big')

		def to_pubkey(self, privkey):
			return PubKey(
				self.encodepoint(self.scalarmultbase(self.rev_bytes2int(privkey))) +
				self.encodepoint(self.scalarmultbase(self.rev_bytes2int(self.to_viewkey(privkey)))),
				compressed = privkey.compressed)

	class ed25519ll_djbec(ed25519):

		def __init__(self, cfg):
			super().__init__(cfg)
			from ...contrib.ed25519ll_djbec import scalarmult
			self.scalarmult = scalarmult

backend.ed25519 = overlay_fake_backend.ed25519
backend.ed25519ll_djbec = overlay_fake_backend.ed25519ll_djbec
