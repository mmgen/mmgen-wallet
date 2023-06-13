#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
proto.secp256k1.keygen: secp256k1 public key generation backends for the MMGen suite
"""

from ...key import PubKey
from ...keygen import keygen_base

class backend:

	class libsecp256k1(keygen_base):

		def __init__(self,cfg):
			from .secp256k1 import priv2pub
			self.priv2pub = priv2pub

		def to_pubkey(self,privkey):
			return PubKey(
				s = self.priv2pub( privkey, int(privkey.compressed) ),
				compressed = privkey.compressed )

		@classmethod
		def test_avail(cls,cfg,silent=False):
			try:
				from .secp256k1 import priv2pub
				if not priv2pub(bytes.fromhex('deadbeef'*8),1):
					from ...util import die
					die( 'ExtensionModuleError',
						'Unable to execute priv2pub() from secp256k1 extension module' )
				return cls.__name__
			except Exception as e:
				if not silent:
					from ...util import ymsg
					ymsg(str(e))
				cfg._util.qmsg('Using (slow) native Python ECDSA library for public key generation')
				return 'python_ecdsa'

	class python_ecdsa(keygen_base):

		def __init__(self,cfg):
			import ecdsa
			self.ecdsa = ecdsa

		def to_pubkey(self,privkey):
			"""
			devdoc/guide_wallets.md:
			Uncompressed public keys start with 0x04; compressed public keys begin with 0x03 or
			0x02 depending on whether they're greater or less than the midpoint of the curve.
			"""
			def privnum2pubkey(numpriv,compressed=False):
				pko = self.ecdsa.SigningKey.from_secret_exponent(numpriv,curve=self.ecdsa.SECP256k1)
				# pubkey = x (32 bytes) + y (32 bytes) (unsigned big-endian)
				pubkey = pko.get_verifying_key().to_string()
				if compressed: # discard Y coord, replace with appropriate version byte
					# even y: <0, odd y: >0 -- https://bitcointalk.org/index.php?topic=129652.0
					return (b'\x02',b'\x03')[pubkey[-1] & 1] + pubkey[:32]
				else:
					return b'\x04' + pubkey

			return PubKey(
				s = privnum2pubkey( int.from_bytes(privkey,'big'), compressed=privkey.compressed ),
				compressed = privkey.compressed )
