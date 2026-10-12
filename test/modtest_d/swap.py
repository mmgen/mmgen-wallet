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

		for tl_arg, tl_chk, si_arg in (
				(None,      None,             None),
				('1',       UniAmt('1'),      None),
				('33',      UniAmt('33'),     7),
				('2%',      0.98,             14),
				('-2%',     1.02,             1),
				('3.333%',  0.96667,          1),
				('-3.333%', 1.03333,          3),
				('1.2345',  UniAmt('1.2345'), 10)):
			cfg_data = {
				'trade_limit': tl_arg,
				'stream_interval': None if si_arg is None else str(si_arg)}
			sc = SwapCfg(Config(cfg_data))
			vmsg(f'  trade_limit:     {tl_arg} => {sc.trade_limit}')
			vmsg(f'  stream_interval: {si_arg} => {sc.stream_interval}')
			assert sc.trade_limit == tl_chk
			assert sc.stream_interval == sc.si.dfl if si_arg is None else si_arg
			assert sc.stream_quantity == 0

		vmsg('\n  Testing error handling')

		def bad1():
			SwapCfg(Config({'trade_limit': 'x'}))

		def bad2():
			SwapCfg(Config({'trade_limit': '1.23x'}))

		def bad3():
			SwapCfg(Config({'stream_interval': 30}))

		def bad4():
			SwapCfg(Config({'stream_interval': 0}))

		def bad5():
			SwapCfg(Config({'stream_interval': 'x'}))

		ut.process_bad_data((
			('bad1', 'SwapCfgValueError', 'invalid parameter', bad1),
			('bad2', 'SwapCfgValueError', 'invalid parameter', bad2),
			('bad3', 'SwapCfgValueError', 'invalid parameter', bad3),
			('bad4', 'SwapCfgValueError', 'invalid parameter', bad4),
			('bad5', 'SwapCfgValueError', 'invalid parameter', bad5),
		), pfx='')

		return True

	def asset(self, name, ut, desc='SwapAsset class'):
		for asset_name, full_name, memo_name, chain, tokensym, direction in (
			('BTC',      'BTC.BTC',  'b',        'BTC', None,   'recv'),
			('LTC',      'LTC.LTC',  'l',        'LTC', None,   'recv'),
			('BCH',      'BCH.BCH',  'c',        'BCH', None,   'recv'),
			('ETH.USDT', 'ETH.USDT', 'ETH.USDT', 'ETH', 'USDT', 'recv'),
		):
			a = SwapAsset(asset_name, direction)
			vmsg(f'  {a.name}')
			assert a.name == asset_name
			assert a.full_name == full_name
			assert a.direction == direction
			assert a.tokensym == tokensym
			assert a.chain == chain
			assert a.memo_asset_name == memo_name
		return True

	def memo(self, name, ut, desc='Swap transaction memo'):

		def bad(s):
			return lambda: Memo.parse(s)

		def bad10(swap_cfg):
			def inner():
				coin = 'BTC'
				proto = init_proto(cfg, coin, need_amt=True)
				addr = make_burn_addr(proto, 'C')
				asset = SwapAsset(coin, 'send')
				Memo(swap_cfg, proto, asset, addr, trade_limit=None)
			return inner

		def bad11():
			SwapAsset('XYZ', 'send')

		def bad12():
			SwapAsset('DOGE', 'send')

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

			for limit, limit_chk, si, suf in (
				('123.4567',   12340000000, None, '1234e7/3/0'),
				('1.234567',   123400000,   1,    '1234e5/1/0'),
				('0.01234567', 1234000,     10,   '1234e3/10/0'),
				('0.00012345', 12345,       20,   '12345/20/0'),
				(None,         0,           3,    '0/3/0'),
			):
				vmsg('\nTesting memo initialization:')
				swap_cfg = SwapCfg(Config({'trade_limit': limit, 'stream_interval': si}))
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
				assert p.asset.chain == coin.upper()
				assert p.asset.coin == token or coin.upper()
				assert p.address == addr.views[addr.view_pref]
				assert p.trade_limit == limit_chk
				assert p.stream_interval == si or swap_cfg.si.dfl, f'{p.stream_interval} != {swap_cfg.si.dfl}'
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

			ut.process_bad_data((
				('bad1',  'SwapMemoParseError', 'must contain',      bad('x')),
				('bad2',  'SwapMemoParseError', 'must contain',      bad('y:z:x')),
				('bad3',  'SwapMemoParseError', 'function abbrev',   bad('z:l:foobar:0/3/0')),
				('bad4',  'SwapAssetError',     'unrecognized',      bad('=:x:foobar:0/3/0')),
				('bad5',  'SwapMemoParseError', 'failed to parse',   bad('=:l:foobar:n')),
				('bad6',  'SwapMemoParseError', 'invalid specifier', bad('=:l:foobar:x/3/0')),
				('bad7',  'SwapMemoParseError', 'extra',             bad('=:l:foobar:0/3/0:x')),
				('bad10', 'AssertionError',     'recv',              bad10(swap_cfg)),
				('bad11', 'SwapAssetError',     'unrecognized',      bad11),
				('bad12', 'SwapAssetError',     'unsupported',       bad12),
			), pfx='')

		return True

	def memoless(self, name, ut, desc='memoless amounts'):
		from mmgen.swap.proto.thorchain.memoless import THORChainMemolessAmount
		from mmgen.swap.util import get_coin_amt
		vecs = [
			{
				'desc': 'BTC',
				'asset': 'btc',
				'data': (
					('1.00020002', '1.00020002', 100020002, 20002, False),
					('1',          '1.00049999', 100049999, 49999, False),
					('1.00020002', '1.00049999', 100049999, 49999, False),
					('1',          '1.0005',     100050000, 50000, False),
					('1',          '0.99950001',  99950001, 50001, False),
					('1',          '0.99999999',  99999999, 99999, False),
					('1.00049999', '1.00020002', 100020002, 20002, False),
					('1.00050001', '1.00000001', 100000001,     1, False),
					('1.99999999', '2.00000001', 200000001,     1, False))
			}, {
				'desc': 'BTC round down',
				'asset': 'btc',
				'data': (
					('1.00020002', '1.00020002', 100020002, 20002, True),
					('1',          '0.99949999',  99949999, 49999, True),
					('1.00020002', '0.99949999',  99949999, 49999, True),
					('1',          '0.9995',      99950000, 50000, True),
					('1',          '0.99950001',  99950001, 50001, True),
					('1',          '0.99999999',  99999999, 99999, True),
					('1.00049999', '1.00020002', 100020002, 20002, True),
					('1.00050001', '1.00000001', 100000001,     1, True),
					('1.99999999', '1.99900001', 199900001,     1, True))
			}, {
				'desc': 'BTC misc',
				'asset': 'btc',
				'data': (
					('1',          '1.00020002', 100020002, 20002, False),
					('1',          '0.99920002',  99920002, 20002, True),
					('1.234',      '1.23420002', 123420002, 20002, False),
					('1.234',      '1.23320002', 123320002, 20002, True),
					('1.234',      '1.23449999', 123449999, 49999, False),
					('1.234',      '1.2345',     123450000, 50000, False),
					('1.234',      '1.2335',     123350000, 50000, True),
					('1.234',      '1.23350001', 123350001, 50001, False),
					('1.234',      '1.23350001', 123350001, 50001, True),
					('1.234',      '1.23399999', 123399999, 99999, False),
					('1.2345',     '1.23449999', 123449999, 49999, False),
					('1.23456789', '1.23420002', 123420002, 20002, False),
					('1.23456789', '1.23499999', 123499999, 99999, False),
					('1.23456789', '1.23399999', 123399999, 99999, True))
			}, {
				'desc': 'ETH',
				'asset': 'eth',
				'data': (
					('1.234567800000000001', '1.234567800000000001', 1234567800000000001, 1,     False),
					('1.2345678',            '1.234567800000000001', 1234567800000000001, 1,     False),
					('1.234567800000000001', '1.234567800000050001', 1234567800000050001, 50001, False),
					('1.2345678',            '1.234567799999999999', 1234567799999999999, 99999, False),
					('1.234567899999923456', '1.234567899999900001', 1234567899999900001, 1,     True),
					('1.234567899999960001', '1.234567899999910001', 1234567899999910001, 10001, True),
					('1.234567899999960002', '1.234567899999910001', 1234567899999910001, 10001, True),
					('1.23456789',           '1.234567890000020002', 1234567890000020002, 20002, False),
					('1.23456789',           '1.234567889999920002', 1234567889999920002, 20002, True),
					('1.23456789',           '1.234567889999999999', 1234567889999999999, 99999, False),
					('1.23456789',           '1.234567889999999999', 1234567889999999999, 99999, True))
			}, {
				'desc': 'USDT',
				'asset': 'eth.usdt',
				'data': (
					('1.012345',   '1.012345', 1012345, 12345, False),
					('1',          '1.020002', 1020002, 20002, False),
					('1.025',      '1.075',    1075000, 75000, False),
					('1.025',      '0.975001',  975001, 75001, False),
					('1.075',      '1.025001', 1025001, 25001, False),
					('1.075',      '1.025',    1025000, 25000, False),
					('1.076',      '1.125',    1125000, 25000, False),
					('1.012345',   '1.012345', 1012345, 12345, True),
					('1',          '0.920002',  920002, 20002, True),
					('1.025',      '0.975',     975000, 75000, True),
					('1.025',      '0.975001',  975001, 75001, True),
					('1.075',      '1.025001', 1025001, 25001, True),
					('1.075',      '1.025',    1025000, 25000, True),
					('1.076',      '1.025',    1025000, 25000, True),
					('1.234567',   '1.220002', 1220002, 20002, False),
					('1.234567',   '1.25',     1250000, 50000, False),
					('1.234567',   '1.250001', 1250001, 50001, False),
					('1.234567',   '1.199999', 1199999, 99999, False),
					('1.234567',   '1.199999', 1199999, 99999, True),
					('1.567',      '1.520002', 1520002, 20002, False))}]

		def get_type(diff):
			return 'A' if diff == 0 else (
				('B' if diff < halfmod else 'C' if diff == halfmod else 'D') if diff > 0 else
				('E' if diff > -halfmod else 'F' if diff == -halfmod else 'G'))

		mod = THORChainMemolessAmount.mod
		halfmod = mod // 2

		for vec in vecs:
			wid = get_coin_amt(cfg, vec['asset'], '0').max_prec + 3
			fs = '    {:{w}} {:{w}} {:<{w}} {:<6} {:<4} {}'
			vmsg(f'\n  {vec["desc"]}')
			vmsg(fs.format('AMT_IN', 'AMT_OUT', 'INT_AMT', 'REFNUM', 'TYPE', 'ROUND_DOWN', w=wid))
			vmsg(fs.format('------', '-------', '-------', '------', '----', '----------', w=wid))
			for amt_in, amt_out, int_amt, refnum, round_down in vec['data']:
				amt = get_coin_amt(cfg, vec['asset'], amt_in)
				enc = THORChainMemolessAmount(amt, refnum=refnum, round_down=round_down)
				vmsg(fs.format(
					amt_in,
					amt_out,
					int_amt,
					refnum,
					get_type(refnum - amt.to_unit('atomic') % mod),
					round_down,
					w = wid))

				assert enc.refnum == refnum, f'{enc.refnum} != {refnum}'
				assert str(enc.amt) == amt_out, f'{enc.amt!s} != {amt_out}'
				assert enc.int_amt == int_amt, f'{enc.int_amt} != {int_amt}'
				if round_down:
					assert enc.amt <= amt

				dec = THORChainMemolessAmount(enc.amt)
				assert enc.amt == dec.amt, f'{enc.amt} != {dec.amt}'
				assert enc.int_amt == dec.int_amt, f'{enc.int_amt} != {dec.int_amt}'
				assert enc.refnum == dec.refnum, f'{enc.refnum} != {dec.refnum}'

		return True

		vmsg('\nTesting error handling')

		proto = init_proto(cfg, 'btc', need_amt=True)

		def bad1(): THORChainMemolessAmount(proto.coin_amt('1'), 100000)
		def bad2(): THORChainMemolessAmount(proto.coin_amt('1'), 'foo')
		def bad3(): THORChainMemolessAmount(proto.coin_amt('1'), -1)
		def bad4(): THORChainMemolessAmount(1, 1)

		ut.process_bad_data((
			('refnum (100000)',  'AssertionError', 'must be an integer', bad1),
			('refnum ("foo")',   'AssertionError', 'must be an integer', bad2),
			('refnum (-1)',      'AssertionError', 'must be an integer', bad3),
			('amount (integer)', 'AssertionError', 'must be CoinAmt',    bad4),
		))

		return True
