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

from ....util import die

from . import name as proto_name

class Memo:

	# The trade limit, i.e., set 100000000 to get a minimum of 1 full asset, else a refund
	# Optional. 1e8 or scientific notation
	trade_limit = None

	# Swap interval in blocks. Optional. If 0, do not stream
	stream_interval = 1

	# Swap quantity. The interval value determines the frequency of swaps in blocks
	# Optional. If 0, network will determine the number of swaps
	stream_quantity = 0

	max_len = 250
	function = 'SWAP'

	asset_abbrevs = {
		'BTC.BTC':   'b',
		'LTC.LTC':   'l',
		'BCH.BCH':   'c',
		'ETH.ETH':   'e',
		'DOGE.DOGE': 'd',
		'THOR.RUNE': 'r',
	}

	function_abbrevs = {
		'SWAP': '=',
	}

	@classmethod
	def is_partial_memo(cls, s):
		import re
		ops = {
			'swap':     ('SWAP',     's',  '='),
			'add':      ('ADD',      'a',  r'\+'),
			'withdraw': ('WITHDRAW', 'wd', '-'),
			'loan':     (r'LOAN(\+|-)', r'\$(\+|-)'), # open/repay
			'pool':     (r'POOL(\+|-)',),
			'trade':    (r'TRADE(\+|-)',),
			'secure':   (r'SECURE(\+|-)',),
			'misc':     ('BOND', 'UNBOND', 'LEAVE', 'MIGRATE', 'NOOP', 'DONATE', 'RESERVE'),
		}
		pat = r'^(' + '|'.join('|'.join(pats) for pats in ops.values()) + r'):\S\S+'
		return bool(re.search(pat, str(s)))

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
			rev_data = {v:k for k,v in data.items()}
			if item in rev_data:
				return rev_data[item]
			die('SwapMemoParseError', f'{item!r}: unrecognized {proto_name} {desc} abbreviation')

		fields = str(s).split(':')

		if len(fields) < 4:
			die('SwapMemoParseError', 'memo must contain at least 4 comma-separated fields')

		function = get_id(cls.function_abbrevs, get_item('function'), 'function')

		chain, asset = get_id(cls.asset_abbrevs, get_item('asset'), 'asset').split('.')

		address = get_item('address')

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
			['proto', 'function', 'chain', 'asset', 'address', 'trade_limit', 'stream_interval', 'stream_quantity'])

		return ret(proto_name, function, chain, asset, address, limit_int, int(interval), int(quantity))

	def __init__(self, proto, addr, chain=None, trade_limit=None):
		self.proto = proto
		self.chain = chain or proto.coin
		if trade_limit is None:
			self.trade_limit = self.proto.coin_amt('0')
		else:
			assert type(trade_limit) is self.proto.coin_amt, f'{type(trade_limit)} != {self.proto.coin_amt}'
			self.trade_limit = trade_limit
		from ....addr import is_coin_addr
		assert is_coin_addr(proto, addr)
		self.addr = addr.views[addr.view_pref]
		assert not ':' in self.addr # colon is record separator, so address mustn’t contain one

	def __str__(self):
		from . import ExpInt4
		try:
			tl_enc = ExpInt4(self.trade_limit.to_unit('satoshi')).enc
		except Exception as e:
			die('SwapMemoParseError', str(e))
		suf = '/'.join(str(n) for n in (tl_enc, self.stream_interval, self.stream_quantity))
		asset = f'{self.chain}.{self.proto.coin}'
		ret = ':'.join([
			self.function_abbrevs[self.function],
			self.asset_abbrevs[asset],
			self.addr,
			suf])
		assert len(ret) <= self.max_len, f'{proto_name} memo exceeds maximum length of {self.max_len}'
		return ret
