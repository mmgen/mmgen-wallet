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
addrgen.py: Address and view key generation classes for the MMGen suite
"""

from .proto.common import hash160,b58chk_encode
from .addr import CoinAddr,MMGenAddrType,MoneroViewKey,ZcashViewKey

# decorator for to_addr() and to_viewkey()
def check_data(orig_func):
	def f(self,data):
		assert data.pubkey_type == self.pubkey_type, 'addrgen.py:check_data() pubkey_type mismatch'
		assert data.compressed == self.compressed,(
	f'addrgen.py:check_data() expected compressed={self.compressed} but got compressed={data.compressed}'
		)
		return orig_func(self,data)
	return f

class addr_generator:
	"""
	provide a generator for each supported address format
	"""
	class base:

		def __init__(self,proto,addr_type):
			self.proto = proto
			self.pubkey_type = addr_type.pubkey_type
			self.compressed = addr_type.compressed
			desc = f'AddrGenerator {type(self).__name__!r}'

		def to_segwit_redeem_script(self,data):
			raise NotImplementedError('Segwit redeem script not supported by this address type')

	class p2pkh(base):

		@check_data
		def to_addr(self,data):
			return CoinAddr(
				self.proto,
				self.proto.pubhash2addr( hash160(data.pubkey), p2sh=False ))

	class legacy(p2pkh): pass
	class compressed(p2pkh): pass

	class segwit(base):

		@check_data
		def to_addr(self,data):
			return CoinAddr(
				self.proto,
				self.proto.pubkey2segwitaddr(data.pubkey) )

		def to_segwit_redeem_script(self,data): # NB: returns hex
			return self.proto.pubkey2redeem_script(data.pubkey).hex()

	class bech32(base):

		@check_data
		def to_addr(self,data):
			return CoinAddr(
				self.proto,
				self.proto.pubhash2bech32addr( hash160(data.pubkey) ))

	class keccak(base):

		def __init__(self,proto,addr_type):
			super().__init__(proto,addr_type)
			from .util import get_keccak
			self.keccak_256 = get_keccak()

	class ethereum(keccak):

		@check_data
		def to_addr(self,data):
			return CoinAddr(
				self.proto,
				self.keccak_256(data.pubkey[1:]).hexdigest()[24:] )

	class monero(keccak):

		def b58enc(self,addr_bytes):
			from .baseconv import baseconv
			enc = baseconv('b58').frombytes
			l = len(addr_bytes)
			a = ''.join([enc( addr_bytes[i*8:i*8+8], pad=11, tostr=True ) for i in range(l//8)])
			b = enc( addr_bytes[l-l%8:], pad=7, tostr=True )
			return a + b

		@check_data
		def to_addr(self,data):
			step1 = self.proto.addr_fmt_to_ver_bytes('monero') + data.pubkey
			return CoinAddr(
				proto = self.proto,
				addr = self.b58enc( step1 + self.keccak_256(step1).digest()[:4]) )

		@check_data
		def to_viewkey(self,data):
			return MoneroViewKey( data.viewkey_bytes.hex() )

	class zcash_z(base):

		@check_data
		def to_addr(self,data):
			ret = b58chk_encode(
				self.proto.addr_fmt_to_ver_bytes('zcash_z')
				+ data.pubkey )
			return CoinAddr( self.proto, ret )

		@check_data
		def to_viewkey(self,data):
			ret = b58chk_encode(
				self.proto.addr_fmt_to_ver_bytes('viewkey')
				+ data.viewkey_bytes )
			return ZcashViewKey( self.proto, ret )
