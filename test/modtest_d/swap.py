#!/usr/bin/env python3

"""
test.modtest_d.swap: swap unit tests for the MMGen suite
"""

from mmgen.color import cyan

from ..include.common import cfg, vmsg, make_burn_addr

class unit_tests:

	def memo(self, name, ut, desc='Swap transaction memo'):
		from mmgen.protocol import init_proto
		from mmgen.amt import UniAmt
		from mmgen.swap.proto.thorchain import data as Memo
		for coin, addrtype in (
			('ltc', 'bech32'),
			('bch', 'compressed'),
			('eth', None),
		):
			proto = init_proto(cfg, coin, need_amt=True)
			addr = make_burn_addr(proto, addrtype)

			vmsg(f'\nTesting coin {cyan(coin.upper())}:')

			for limit, limit_chk in (
				('123.4567',   12340000000),
				('1.234567',   123400000),
				('0.01234567', 1234000),
				('0.00012345', 12345),
				(None, 0),
			):
				vmsg('\nTesting memo initialization:')
				m = Memo(proto, addr, trade_limit=UniAmt(limit) if limit else None)
				vmsg(f'str(memo):  {m}')
				vmsg(f'repr(memo): {m!r}')
				vmsg(f'limit:      {limit}')

				p = Memo.parse(m)
				limit_dec = UniAmt(p.trade_limit, from_unit='satoshi')
				vmsg(f'limit_dec:  {limit_dec.hl()}')

				vmsg('\nTesting memo parsing:')
				from pprint import pformat
				vmsg(pformat(p._asdict()))
				assert p.proto == 'THORChain'
				assert p.function == 'SWAP'
				assert p.chain == coin.upper()
				assert p.asset == coin.upper()
				assert p.address == addr.views[addr.view_pref]
				assert p.trade_limit == limit_chk
				assert p.stream_interval == 1
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

			ut.process_bad_data((
				('bad1',  'SwapMemoParseError', 'must contain',      bad('x')),
				('bad2',  'SwapMemoParseError', 'must contain',      bad('y:z:x')),
				('bad3',  'SwapMemoParseError', 'function abbrev',   bad('z:l:foobar:0/1/0')),
				('bad4',  'SwapMemoParseError', 'asset abbrev',      bad('=:x:foobar:0/1/0')),
				('bad5',  'SwapMemoParseError', 'failed to parse',   bad('=:l:foobar:n')),
				('bad6',  'SwapMemoParseError', 'invalid specifier', bad('=:l:foobar:x/1/0')),
				('bad7',  'SwapMemoParseError', 'extra',             bad('=:l:foobar:0/1/0:x')),
			), pfx='')

		return True
