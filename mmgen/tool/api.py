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
tool.api: Python interface to selected commands from the 'mmgen-tool' utility
"""

from .common import tool_cmd_base
from .util import tool_cmd as util_cmds
from .coin import tool_cmd as coin_cmds
from .mnemonic import tool_cmd as mnemonic_cmds

class tool_api(
		util_cmds,
		coin_cmds,
		mnemonic_cmds,
		tool_cmd_base):
	"""
	API providing access to a subset of methods from the mmgen.tool module

	Example:
		from mmgen.tool.api import tool_api
		from mmgen.cfg import Config

		# Initialize a tool API instance:
		tool = tool_api(Config())

		# Set the coin and network:
		tool.init_coin('btc', 'mainnet')

		# Print available address types:
		tool.print_addrtypes()

		# Set the address type:
		tool.addrtype = 'segwit'

		# Disable user entropy gathering (optional, reduces security):
		tool.usr_randchars = 0

		# Generate a random BTC segwit keypair:
		wif, addr = tool.randpair()

		# Set coin, network and address type:
		tool.init_coin('ltc', 'testnet')
		tool.addrtype = 'bech32'

		# Generate a random LTC testnet Bech32 keypair:
		wif, addr = tool.randpair()

		print('wif: ', wif)
		print('addr:', addr)
	"""

	need_proto = True
	need_addrtype = True

	def __init__(self, cfg):
		"""
		Initializer - takes no arguments
		"""
		type(cfg)._reset_ok += ('usr_randchars',)
		super().__init__(cfg=cfg)

	def init_coin(self, coinsym, network):
		"""
		Initialize a coin/network pair
		Valid choices for coins: one of the symbols returned by the 'coins' attribute
		Valid choices for network: 'mainnet', 'testnet', 'regtest'
		"""
		from ..protocol import init_proto, warn_trustlevel
		warn_trustlevel(self.cfg)
		self.proto = init_proto(self.cfg, coinsym, network=network, need_amt=True)
		return self.proto

	@property
	def coins(self):
		"""The available coins"""
		from ..protocol import CoinProtocol
		from ..altcoin.params import CoinInfo
		return sorted(set(
			[c.upper() for c in CoinProtocol.coins]
			+ [c.symbol for c in CoinInfo.get_supported_coins(self.proto.network)]
		))

	@property
	def coin(self):
		"""The currently configured coin"""
		return self.proto.coin

	@property
	def network(self):
		"""The currently configured network"""
		return self.proto.network

	@property
	def addrtypes(self):
		"""
		The available address types for current coin/network pair.  The
		first-listed is the default
		"""
		from ..addr import MMGenAddrType
		return [MMGenAddrType(proto=self.proto, id_str=id_str).name for id_str in self.proto.mmtypes]

	def print_addrtypes(self):
		"""
		Print the available address types for current coin/network pair along with
		a description.  The first-listed is the default
		"""
		from ..addr import MMGenAddrType
		for t in [MMGenAddrType(proto=self.proto, id_str=id_str) for id_str in self.proto.mmtypes]:
			print(f'{t.name:<12} - {t.desc}')

	@property
	def addrtype(self):
		"""The currently configured address type (is assignable)"""
		return self.mmtype

	@addrtype.setter
	def addrtype(self, val):
		from ..addr import MMGenAddrType
		self.mmtype = MMGenAddrType(self.proto, val)

	@property
	def usr_randchars(self):
		"""
		The number of keystrokes of entropy to be gathered from the user.
		Setting to zero disables user entropy gathering.
		"""
		return self.cfg.usr_randchars

	@usr_randchars.setter
	def usr_randchars(self, val):
		self.cfg.usr_randchars = val
