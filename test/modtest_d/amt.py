#!/usr/bin/env python3

"""
test.modtest_d.amt: CoinAmt unit tests for the MMGen suite
"""

from decimal import Decimal

from mmgen.protocol import init_proto
from mmgen.tx.new import parse_fee_spec
from mmgen.cfg import Config
from mmgen.amt import TokenAmt

from ..include.common import cfg, vmsg

def get_protos(data):
	return {coin: init_proto(cfg, coin, need_amt=True) for coin in set(d[0] for d in data)}

def test_to_unit(data):
	protos = get_protos(data)
	for proto, amt, unit, chk in data:
		amt = protos[proto].coin_amt(amt)
		res = amt.to_unit(unit)
		vmsg(f'  {proto.upper()} {amt.fmt(4):<24} => {res:<21} {unit}')
		if '.' in chk:
			assert res == Decimal(chk), f'{res} != {Decimal(chk)}'
		else:
			assert res == int(chk), f'{res} != {int(chk)}'
	return True

def test_fee_spec(data):
	protos = get_protos(data)
	for proto, spec, amt, unit in data:
		vmsg(f'  {proto.upper():6} {spec:<5} => {amt:<4} {unit}')
		res = parse_fee_spec(protos[proto], spec)
		assert res.amt == amt, f'  {res.amt} != {amt}'
		assert res.unit == unit, f'  {res.unit} != {unit}'
	return True

def test_fmt(data):
	protos = get_protos(data)
	fs = '  {:5} {:18} {:<6} {:<5} {}'
	vmsg(fs.format('PROTO', 'INPUT', 'IWIDTH', 'PREC', 'FORMATTED'))
	for proto, amt, iwidth, prec, chk in data:
		amt = protos[proto].coin_amt(amt)
		args = (iwidth,) if iwidth else ()
		kwargs = {'prec': prec} if prec else {}
		res = amt.fmt(*args, **kwargs)
		vmsg(fs.format(
			proto.upper(),
			f'[{str(amt)}]',
			'None' if iwidth is None else iwidth,
			'None' if prec is None else prec,
			f'[{res}]'))
		assert res == chk, f'[{res}] != [{chk}]'
	return True

class unit_tests:

	altcoin_deps = ('fee_spec_alt', 'to_unit_alt', 'token_amt')

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

	def fee_spec(self, name, ut, desc='fee spec parsing (BTC)'):
		return test_fee_spec((
			('btc', '32s',  '32', 'satoshi'),
			('btc', '1s',   '1',  'satoshi')))

	def fee_spec_alt(self, name, ut, desc='fee spec parsing (LTC, BCH, ETH, XMR)'):
		return test_fee_spec((
			('ltc', '3.07s', '3.07', 'satoshi'),
			('bch', '3.07s', '3.07', 'satoshi'),
			('eth', '3.07G', '3.07', 'Gwei'),
			('eth', '37M',   '37',   'Mwei'),
			('eth', '3701w', '3701', 'wei'),
			('eth', '3.07M', '3.07', 'Mwei'),
			('xmr', '3.07a', '3.07', 'atomic')))

	def fmt(self, name, ut, desc='column formatting (LTC, BCH, ETH, XMR)'):
		return test_fmt((
			('btc', '1',              None, None, '1         '),
			('btc', '1.2',            None, None, '1.2       '),
			('btc', '1',              1,    None, '1         '),
			('btc', '1.2',            1,    None, '1.2       '),
			('btc', '12',             None, None, '12         '),
			('btc', '12.3',           None, None, '12.3       '),
			('btc', '12',             1,    None, '12         '),
			('btc', '12.3',           1,    None, '12.3       '),
			('btc', '12',             2,    None, '12         '),
			('btc', '12.3',           2,    None, '12.3       '),
			('btc', '12',             3,    None, ' 12         '),
			('btc', '12.3',           3,    None, ' 12.3       '),
			('ltc', '0',              None, None, '0         '),
			('ltc', '0.00000001',     None, None, '0.00000001'),
			('ltc', '0.00000001',     8,    None, '       0.00000001'),
			('xmr', '1.234567890123', None, None, '1.234567890123'),
			('xmr', '1',              None, None, '1             '),
			('xmr', '1',              None, 4,    '1     '),
			('xmr', '123.456',        None, None, '123.456         '),
			('xmr', '123.456',        2,    None, '123.456         '),
			('xmr', '123.456',        None, 4,    '123.456 '),
			('xmr', '123.456',        2,    4,    '123.456 '),
			('xmr', '1.234567890123', None, 4,    '1.2345'),
			('xmr', '1.234567890123', 8,    4,    '       1.2345'),
			('xmr', '1',              8,    4,    '       1     '),
			('xmr', '111',            8,    4,    '     111     ')))

	def token_amt(self, name, ut, desc='TokenAmt (ETH)'):
		for n, dec, unit, chk in (
			(1234567,                    6,  'atomic', '1.234567'),
			('1.234567',                 6,  None,     '1.234567'),
			(1234567,                    22, 'atomic', '0.0000000000000001234567'),
			('0.0000000000000001234567', 22, None,     '0.0000000000000001234567'),
		):
			amt = TokenAmt(n, decimals=dec, from_unit=unit)
			amt_disp = amt.hl(color=False)
			vmsg('  ' + amt_disp)
			if unit == 'atomic':
				assert amt.to_unit('atomic') == n
			assert amt_disp == chk, f'{amt_disp} != {chk}'
		return True
