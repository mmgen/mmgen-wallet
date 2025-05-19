#!/usr/bin/env python3

"""
test.modtest_d.swap: swap unit tests for the MMGen suite
"""

from mmgen.color import cyan
from mmgen.cfg import Config
from mmgen.amt import UniAmt
from mmgen.swap.proto.thorchain import SwapCfg, SwapAsset, Memo
from mmgen.protocol import init_proto

from ..include.common import cfg, vmsg, make_burn_addr

class unit_tests:

	def cfg(self, name, ut, desc='Swap configuration'):

		for tl_arg, tl_chk in (
				(None,      None),
				('1',       UniAmt('1')),
				('33',      UniAmt('33')),
				('2%',      0.98),
				('-2%',     1.02),
				('3.333%',  0.96667),
				('-3.333%', 1.03333),
				('1.2345',  UniAmt('1.2345'))):
			cfg_data = {'trade_limit': tl_arg}
			sc = SwapCfg(Config(cfg_data))
			vmsg(f'  trade_limit:     {tl_arg} => {sc.trade_limit}')
			assert sc.trade_limit == tl_chk
			assert sc.stream_interval == 3
			assert sc.stream_quantity == 0

		vmsg('\n  Testing error handling')

		def bad1():
			SwapCfg(Config({'trade_limit': 'x'}))

		def bad2():
			SwapCfg(Config({'trade_limit': '1.23x'}))

		ut.process_bad_data((
			('bad1', 'SwapCfgValueError', 'invalid parameter', bad1),
			('bad2', 'SwapCfgValueError', 'invalid parameter', bad2),
		), pfx='')

		return True

	def asset(self, name, ut, desc='SwapAsset class'):
		for name, full_name, memo_name, chain, asset, direction in (
			('BTC',      'BTC.BTC',  'b',        'BTC', None,   'recv'),
			('LTC',      'LTC.LTC',  'l',        'LTC', None,   'recv'),
			('BCH',      'BCH.BCH',  'c',        'BCH', None,   'recv'),
			('ETH.USDT', 'ETH.USDT', 'ETH.USDT', 'ETH', 'USDT', 'recv'),
		):
			a = SwapAsset(name, direction)
			vmsg(f'  {a.name}')
			assert a.name == name
			assert a.full_name == full_name
			assert a.direction == direction
			assert a.asset == asset
			assert a.chain == chain
			assert a.memo_asset_name == memo_name
		return True

	def memo(self, name, ut, desc='Swap transaction memo'):

		for coin, addrtype, asset_name, token in (
			('ltc', 'bech32',     'LTC',      None),
			('bch', 'compressed', 'BCH',      None),
			('eth', None,         'ETH',      None),
			('eth', None,         'ETH.USDT', 'USDT'),
		):
			proto = init_proto(cfg, coin, tokensym=token, need_amt=True)
			addr = make_burn_addr(proto, addrtype)
			asset = SwapAsset(asset_name, 'recv')

			vmsg(f'\nTesting asset {cyan(asset_name)}:')

			for limit, limit_chk, suf in (
				('123.4567',   12340000000, '1234e7/3/0'),
				('1.234567',   123400000,   '1234e5/3/0'),
				('0.01234567', 1234000,     '1234e3/3/0'),
				('0.00012345', 12345,       '12345/3/0'),
				(None,         0,           '0/3/0'),
			):
				vmsg('\nTesting memo initialization:')
				swap_cfg = SwapCfg(Config({'trade_limit': limit}))
				m = Memo(
					swap_cfg,
					proto,
					asset,
					addr,
					trade_limit = None if limit is None else UniAmt(limit))
				vmsg(f'str(memo):  {m}')
				vmsg(f'repr(memo): {m!r}')
				vmsg(f'limit:      {limit}')

				assert str(m).endswith(':' + suf), f'{m} doesn’t end with {suf}'

				p = Memo.parse(m)
				limit_dec = UniAmt(p.trade_limit, from_unit='satoshi')
				vmsg(f'limit_dec:  {limit_dec.hl()}')

				vmsg('\nTesting memo parsing:')
				from pprint import pformat
				vmsg(pformat(p._asdict()))
				assert p.proto == 'THORChain'
				assert p.function == 'SWAP'
				assert p.chain == coin.upper()
				assert p.asset == token or coin.upper()
				assert p.address == addr.views[addr.view_pref]
				assert p.trade_limit == limit_chk
				assert p.stream_interval == 3
				assert p.stream_quantity == 0 # auto

			vmsg('\nTesting is_partial_memo():')
			for vec in (
				str(m),
				'SWAP:xyz',
				'=:xyz',
				's:xyz',
				'a:xz',
				'+:xz',
				'WITHDRAW:xz',
				'LOAN+:xz:x:x',
				'TRADE-:xz:x:x',
				'BOND:xz',
			):
				vmsg(f'  pass: {vec}')
				assert Memo.is_partial_memo(vec.encode('ascii')), vec

			for vec in (
				'=',
				'swap',
				'swap:',
				'swap:abc',
				'SWAP:a',
			):
				vmsg(f'  fail: {vec}')
				assert not Memo.is_partial_memo(vec.encode('ascii')), vec

			vmsg('\nTesting error handling:')

			def bad(s):
				return lambda: Memo.parse(s)

			def bad10():
				coin = 'BTC'
				proto = init_proto(cfg, coin, need_amt=True)
				addr = make_burn_addr(proto, 'C')
				asset = SwapAsset(coin, 'send')
				Memo(swap_cfg, proto, asset, addr, trade_limit=None)

			def bad11():
				SwapAsset('XYZ', 'send')

			def bad12():
				SwapAsset('DOGE', 'send')

			ut.process_bad_data((
				('bad1',  'SwapMemoParseError', 'must contain',      bad('x')),
				('bad2',  'SwapMemoParseError', 'must contain',      bad('y:z:x')),
				('bad3',  'SwapMemoParseError', 'function abbrev',   bad('z:l:foobar:0/3/0')),
				('bad4',  'SwapAssetError',     'unrecognized',      bad('=:x:foobar:0/3/0')),
				('bad5',  'SwapMemoParseError', 'failed to parse',   bad('=:l:foobar:n')),
				('bad6',  'SwapMemoParseError', 'invalid specifier', bad('=:l:foobar:x/3/0')),
				('bad7',  'SwapMemoParseError', 'extra',             bad('=:l:foobar:0/3/0:x')),
				('bad10', 'AssertionError',     'recv',              bad10),
				('bad11', 'SwapAssetError',     'unrecognized',      bad11),
				('bad12', 'SwapAssetError',     'unsupported',       bad12),
			), pfx='')

		return True
