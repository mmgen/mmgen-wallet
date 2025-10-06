#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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
addrgen: Address generation initialization code for the MMGen suite
"""

from .keygen import KeyGenerator # convenience import

# decorator for to_addr() and to_viewkey()
def check_data(orig_func):
	def f(self, data):
		assert data.pubkey_type == self.pubkey_type, 'addrgen.py:check_data() pubkey_type mismatch'
		assert data.compressed == self.compressed, (
			f'addrgen.py:check_data() expected compressed={self.compressed} '
			f'but got compressed={data.compressed}')
		return orig_func(self, data)
	return f

class addr_generator:

	class base:

		def __init__(self, cfg, proto, addr_type):
			self.proto = proto
			self.pubkey_type = addr_type.pubkey_type
			self.compressed = addr_type.compressed
			self.desc = f'AddrGenerator {type(self).__name__!r}'

	class keccak(base):

		def __init__(self, cfg, proto, addr_type):
			super().__init__(cfg, proto, addr_type)
			from .util2 import get_keccak
			self.keccak_256 = get_keccak(cfg)

def AddrGenerator(cfg, proto, addr_type):
	"""
	factory function returning an address generator for the specified address type
	"""

	package_map = {
		'legacy':     'btc',
		'compressed': 'btc',
		'segwit':     'btc',
		'bech32':     'btc',
		'bech32x':    'xchain',
		'monero':     'xmr',
		'ethereum':   'eth',
		'zcash_z':    'zec'}

	from .addr import MMGenAddrType

	match addr_type:
		case MMGenAddrType(x):
			assert x in proto.mmtypes, f'{x}: invalid address type for coin {proto.coin}'
		case str(x):
			addr_type = MMGenAddrType(proto=proto, id_str=x)
		case _:
			raise TypeError(f"{type(addr_type)}: incorrect argument type for 'addr_type' arg")

	import importlib
	return getattr(
		importlib.import_module(f'mmgen.proto.{package_map[addr_type.name]}.addrgen'),
		addr_type.name)(cfg, proto, addr_type)
