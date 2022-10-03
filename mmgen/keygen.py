#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
keygen.py: Public key generation classes for the MMGen suite
"""

from collections import namedtuple
from .key import PubKey,PrivKey

keygen_public_data = namedtuple(
	'keygen_public_data', [
		'pubkey',
		'viewkey_bytes',
		'pubkey_type',
		'compressed' ])

class keygen_base:

	def gen_data(self,privkey):
		assert isinstance(privkey,PrivKey)
		return keygen_public_data(
			self.to_pubkey(privkey),
			self.to_viewkey(privkey),
			privkey.pubkey_type,
			privkey.compressed )

	def to_viewkey(self,privkey):
		return None

class keygen_backend:

	class std:
		backends = ('libsecp256k1','python-ecdsa')

		class libsecp256k1(keygen_base):

			def __init__(self):
				from .secp256k1 import priv2pub
				self.priv2pub = priv2pub

			def to_pubkey(self,privkey):
				return PubKey(
					s = self.priv2pub( privkey, int(privkey.compressed) ),
					compressed = privkey.compressed )

			@classmethod
			def test_avail(cls,silent=False):
				try:
					from .secp256k1 import priv2pub
					if not priv2pub(bytes.fromhex('deadbeef'*8),1):
						from .util import die
						die( 'ExtensionModuleError',
							'Unable to execute priv2pub() from secp256k1 extension module' )
					return True
				except Exception as e:
					if not silent:
						from .util import ymsg
						ymsg(str(e))
					return False

		class python_ecdsa(keygen_base):

			def __init__(self):
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

	class monero:
		backends = ('nacl','ed25519ll-djbec','ed25519')

		class base(keygen_base):

			def __init__(self):

				from .proto.xmr.params import mainnet
				self.proto_cls = mainnet

				from .util import get_keccak
				self.keccak_256 = get_keccak()

			def to_viewkey(self,privkey):
				return self.proto_cls.preprocess_key(
					self.proto_cls,
					self.keccak_256(privkey).digest(),
					None )

		class nacl(base):

			def __init__(self):
				super().__init__()
				from nacl.bindings import crypto_scalarmult_ed25519_base_noclamp
				self.scalarmultbase = crypto_scalarmult_ed25519_base_noclamp

			def to_pubkey(self,privkey):
				return PubKey(
					self.scalarmultbase( privkey ) +
					self.scalarmultbase( self.to_viewkey(privkey) ),
					compressed = privkey.compressed
				)

		class ed25519(base):

			def __init__(self):
				super().__init__()
				from .contrib.ed25519 import edwards,encodepoint,B,scalarmult
				self.edwards     = edwards
				self.encodepoint = encodepoint
				self.B           = B
				self.scalarmult  = scalarmult

			def scalarmultbase(self,privnum):
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
				return int.from_bytes( in_bytes[::-1], 'big' )

			def to_pubkey(self,privkey):
				return PubKey(
					self.encodepoint( self.scalarmultbase( self.rev_bytes2int(privkey) )) +
					self.encodepoint( self.scalarmultbase( self.rev_bytes2int(self.to_viewkey(privkey)) )),
					compressed = privkey.compressed
				)

		class ed25519ll_djbec(ed25519):

			def __init__(self):
				super().__init__()
				from .contrib.ed25519ll_djbec import scalarmult
				self.scalarmult = scalarmult

	class zcash_z:
		backends = ('nacl',)

		class nacl(keygen_base):

			def __init__(self):
				from nacl.bindings import crypto_scalarmult_base
				self.crypto_scalarmult_base = crypto_scalarmult_base
				from .sha2 import Sha256
				self.Sha256 = Sha256

			def zhash256(self,s,t):
				s = bytearray(s + bytes(32))
				s[0] |= 0xc0
				s[32] = t
				return self.Sha256(s,preprocess=False).digest()

			def to_pubkey(self,privkey):
				return PubKey(
					self.zhash256(privkey,0)
					+ self.crypto_scalarmult_base(self.zhash256(privkey,1)),
					compressed = privkey.compressed
				)

			def to_viewkey(self,privkey):
				vk = bytearray( self.zhash256(privkey,0) + self.zhash256(privkey,1) )
				vk[32] &= 0xf8
				vk[63] &= 0x7f
				vk[63] |= 0x40
				return vk

def get_backends(pubkey_type):
	return getattr(keygen_backend,pubkey_type).backends

def _check_backend(backend,pubkey_type,desc='keygen backend'):

	from .util import is_int,qmsg,die

	assert is_int(backend), f'illegal value for {desc} (must be an integer)'

	backends = get_backends(pubkey_type)

	if not (1 <= int(backend) <= len(backends)):
		die(1,
			f'{backend}: {desc} out of range\n' +
			f'Configured backends: ' +
			' '.join( f'{n}:{k}' for n,k in enumerate(backends,1) )
		)

	qmsg(f'Using backend {backends[int(backend)-1]!r} for public key generation')

	return True

def check_backend(proto,backend,addr_type):

	from .addr import MMGenAddrType
	pubkey_type = MMGenAddrType(proto,addr_type or proto.dfl_mmtype).pubkey_type

	return  _check_backend(
		backend,
		pubkey_type,
		desc = '--keygen-backend parameter' )
