#!/usr/bin/env python3

"""
test.modtest_d.ut_amt: CoinAmt unit tests for the MMGen suite
"""

from decimal import Decimal

from mmgen.protocol import init_proto
from mmgen.cfg import Config

from ..include.common import cfg, vmsg

def get_protos(data):
	return {coin: init_proto(cfg, coin, need_amt=True) for coin in set(d[0] for d in data)}

def test_to_unit(data):
	protos = get_protos(data)
	for proto, amt, unit, chk in data:
		amt = protos[proto].coin_amt(amt)
		res = amt.to_unit(unit)
		vmsg(f'  {proto.upper()} {amt.fmt(8)} => {res:<14} {unit}')
		if '.' in chk:
			assert res == Decimal(chk), f'{res} != {Decimal(chk)}'
		else:
			assert res == int(chk), f'{res} != {int(chk)}'
	return True

class unit_tests:

	altcoin_deps = ('to_unit_alt',)

	def to_unit(self, name, ut, desc='CoinAmt.to_unit() (BTC)'):
		return test_to_unit((
			('btc', '0.00000001', 'satoshi', '1'),
			('btc', '1.23456789', 'satoshi', '123456789')))

	def to_unit_alt(self, name, ut, desc='CoinAmt.to_unit() (LTC, BCH, ETH, XMR)'):
		return test_to_unit((
			('ltc', '0.00000001',           'satoshi', '1'),
			('ltc', '1.23456789',           'satoshi', '123456789'),
			('bch', '0.00000001',           'satoshi', '1'),
			('bch', '1.23456789',           'satoshi', '123456789'),
			('eth', '1.234567890123456789', 'wei',     '1234567890123456789'),
			('eth', '1.234567890123456789', 'Kwei',    '1234567890123456.789'),
			('eth', '1.234567890123456789', 'Mwei',    '1234567890123.456789'),
			('eth', '1.234567890123456789', 'finney',  '1234.567890123456789'),
			('eth', '0.000000012345678901', 'Mwei',    '12345.678901'),
			('eth', '0.000000000000000001', 'Kwei',    '0.001'),
			('eth', '0.000000000000000001', 'Gwei',    '0.000000001'),
			('eth', '0.00000001',           'Gwei',    '10'),
			('eth', '1',                    'Gwei',    '1000000000'),
			('eth', '1',                    'finney',  '1000'),
			('xmr', '1',                    'atomic',  '1000000000000'),
			('xmr', '0.000000000001',       'atomic',  '1'),
			('xmr', '1.234567890123',       'atomic',  '1234567890123')))
