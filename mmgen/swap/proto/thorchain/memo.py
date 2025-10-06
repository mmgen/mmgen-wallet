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
swap.proto.thorchain.memo: THORChain swap protocol memo class
"""

from ....util import die, is_hex_str

from . import name as proto_name

from . import SwapAsset

class THORChainMemo:

	max_len = 250
	function = 'SWAP'

	function_abbrevs = {
		'SWAP': '='}

	@classmethod
	def is_partial_memo(cls, bytes_data):
		import re
		ops = {
			'swap':     ('SWAP',     's',  '='),
			'add':      ('ADD',      'a',  r'\+'),
			'withdraw': ('WITHDRAW', 'wd', '-'),
			'loan':     (r'LOAN(\+|-)', r'\$(\+|-)'), # open/repay
			'pool':     (r'POOL(\+|-)',),
			'trade':    (r'TRADE(\+|-)',),
			'secure':   (r'SECURE(\+|-)',),
			'misc':     ('BOND', 'UNBOND', 'LEAVE', 'MIGRATE', 'NOOP', 'DONATE', 'RESERVE')}
		pat = r'^(' + '|'.join('|'.join(pats) for pats in ops.values()) + r'):\S\S+'
		return bool(re.search(pat.encode(), bytes_data))

	@classmethod
	def parse(cls, s):
		"""
		All fields are validated, excluding address (cannot validate, since network is unknown)
		"""
		from collections import namedtuple
		from ....util import is_int

		def get_item(desc):
			try:
				return fields.pop(0)
			except IndexError:
				die('SwapMemoParseError', f'malformed {proto_name} memo (missing {desc} field)')

		def get_id(data, item, desc):
			if item in data:
				return item
			rev_data = {v: k for k,v in data.items()}
			if item in rev_data:
				return rev_data[item]
			die('SwapMemoParseError', f'{item!r}: unrecognized {proto_name} {desc} abbreviation')

		fields = str(s).split(':')

		if len(fields) < 4:
			die('SwapMemoParseError', 'memo must contain at least 4 comma-separated fields')

		function = get_id(cls.function_abbrevs, get_item('function'), 'function')

		asset = SwapAsset.init_from_memo(get_item('asset'))

		address = get_item('address')

		if asset.chain in SwapAsset.evm_chains:
			assert address.startswith('0x'), f'{address}: address does not start with ‘0x’'
			assert len(address) == 42, f'{address}: address has incorrect length ({len(address)} != 42)'
			address = address.removeprefix('0x')

		desc = 'trade_limit/stream_interval/stream_quantity'
		lsq = get_item(desc)

		try:
			limit, interval, quantity = lsq.split('/')
		except ValueError:
			die('SwapMemoParseError', f'malformed memo (failed to parse {desc} field) [{lsq}]')

		from . import ExpInt4
		try:
			limit_int = ExpInt4(limit)
		except Exception as e:
			die('SwapMemoParseError', str(e))

		for n in (interval, quantity):
			if not is_int(n):
				die('SwapMemoParseError', f'malformed memo (non-integer in {desc} field [{lsq}])')

		if fields:
			die('SwapMemoParseError', 'malformed memo (unrecognized extra data)')

		ret = namedtuple(
			'parsed_memo',
			['proto', 'function', 'asset', 'address', 'trade_limit', 'stream_interval', 'stream_quantity'])

		return ret(proto_name, function, asset, address, limit_int, int(interval), int(quantity))

	def __init__(self, swap_cfg, proto, asset, addr, *, trade_limit):

		from ....amt import UniAmt
		from ....addr import is_coin_addr

		assert trade_limit is None or isinstance(trade_limit, UniAmt), f'{type(trade_limit)} != {UniAmt}'
		assert is_coin_addr(proto, addr)

		assert asset.coin == proto.coin, f'{asset.coin} != {proto.coin}'
		assert asset.tokensym == getattr(proto, 'tokensym', None), (
			f'{asset.tokensym} != {getattr(proto, "tokensym", None)}')
		assert asset.direction == 'recv', f'{asset.direction} != ‘recv’'

		self.addr = addr.views[addr.view_pref]
		assert not ':' in self.addr # colon is record separator, so address mustn’t contain one

		if asset.chain in SwapAsset.evm_chains:
			assert len(self.addr) == 40, f'{self.addr}: address has incorrect length ({len(self.addr)} != 40)'
			assert is_hex_str(self.addr), f'{self.addr}: address is not a hexadecimal string'
			self.addr = '0x' + self.addr

		self.proto = proto
		self.asset = asset
		self.swap_cfg = swap_cfg
		self.trade_limit = trade_limit

	def __str__(self):
		from . import ExpInt4
		try:
			tl_enc = (
				0 if self.trade_limit is None else
				ExpInt4(self.trade_limit.to_unit('satoshi')).enc)
		except Exception as e:
			die('SwapMemoParseError', str(e))
		suf = '/'.join(str(n) for n in (
			tl_enc,
			self.swap_cfg.stream_interval,
			self.swap_cfg.stream_quantity))
		ret = ':'.join([
			self.function_abbrevs[self.function],
			self.asset.memo_asset_name,
			self.addr,
			suf])
		assert len(ret) <= self.max_len, f'{proto_name} memo exceeds maximum length of {self.max_len}'
		return ret
