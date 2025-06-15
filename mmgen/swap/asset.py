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
swap.asset: swap asset class for the MMGen Wallet suite
"""

from collections import namedtuple

from ..util import die

class SwapAsset:

	_ad = namedtuple('swap_asset_data', ['desc', 'name', 'full_name', 'abbr', 'tested'])
	assets_data = {}
	evm_contracts = {}
	unsupported = ()
	blacklisted = {}
	evm_chains = ()

	def fmt_assets_data(self, indent=''):

		def gen_good():
			fs = '%s{:10} {:23} {:9} {}' % indent
			yield fs.format('ASSET', 'DESCRIPTION', 'STATUS', 'CONTRACT ADDRESS')
			for k, v in self.assets_data.items():
				if not k in self.blacklisted:
					if k in self.send or k in self.recv:
						yield fs.format(
							k,
							v.desc,
							'tested' if v.tested else 'untested',
							self.evm_contracts.get(k,'-'))

		def gen_bad():
			if self.blacklisted:
				fs = '%s{:10} {:23} {}' % indent
				yield '\n\nBlacklisted assets:'
				yield fs.format('ASSET', 'DESCRIPTION', 'REASON')
				for k, v in self.blacklisted.items():
					yield fs.format(k, self.assets_data[k].desc, v)

		return '\n'.join(gen_good()) + '\n'.join(gen_bad())

	@classmethod
	def init_from_memo(cls, s):
		for d in cls.assets_data.values():
			if s in (d.abbr, d.full_name):
				return cls(d.name or d.full_name, 'recv')
		die('SwapAssetError', f'{s!r}: unrecognized asset name or abbreviation')

	@property
	def tested(self):
		return [k for k, v in self.assets_data.items() if v.tested]

	@property
	def send(self):
		return set(self.assets_data) - set(self.unsupported) - set(self.blacklisted)

	@property
	def recv(self):
		return set(self.assets_data) - set(self.unsupported) - set(self.blacklisted)

	@property
	def chain(self):
		return self.data.full_name.split('.', 1)[0] if self.data.full_name else self.name

	@property
	def coin(self):
		return self.data.name or self.data.full_name.split('.', 1)[0]

	@property
	def full_name(self):
		return self.data.full_name or f'{self.data.name}.{self.data.name}'

	@property
	def short_name(self):
		return self.data.name or self.data.full_name.split('.', 1)[1]

	@property
	def tokensym(self):
		return None if self.data.name else self.data.full_name.split('.', 1)[1]

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
