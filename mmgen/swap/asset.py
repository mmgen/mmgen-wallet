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
swap.asset: swap asset class the MMGen Wallet suite
"""

from collections import namedtuple

from ..util import die

class SwapAsset:

	_ad = namedtuple('swap_asset_data', ['desc', 'name', 'full_name', 'abbr'])
	assets_data = {}
	send = ()
	recv = ()
	evm_chains = ()

	@classmethod
	def get_full_name(self, s):
		for d in self.assets_data.values():
			if s in (d.abbr, d.full_name):
				return d.full_name or f'{d.name}.{d.name}'
		die('SwapAssetError', f'{s!r}: unrecognized asset name or abbreviation')

	@property
	def chain(self):
		return self.data.full_name.split('.', 1)[0] if self.data.full_name else self.name

	@property
	def asset(self):
		return self.data.full_name.split('.', 1)[1] if self.data.full_name else None

	@property
	def full_name(self):
		return self.data.full_name or f'{self.data.name}.{self.data.name}'

	@property
	def memo_asset_name(self):
		return self.data.abbr or self.data.full_name

	def __init__(self, name, direction):

		if name not in self.assets_data:
			die('SwapAssetError', f'{name!r}: unrecognized asset')

		assert direction in ('send', 'recv'), 'direction must be ‘send’ or ‘recv’'

		if direction == 'send' and name not in self.send:
			die('SwapAssetError', f'{name!r} unsupported send asset')

		if direction == 'recv' and name not in self.recv:
			die('SwapAssetError', f'{name!r} unsupported receive asset')

		self.direction = direction
		self.name = name
		self.data = self.assets_data[name]
		self.desc = self.data.desc
