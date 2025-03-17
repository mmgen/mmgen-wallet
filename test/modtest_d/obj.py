#!/usr/bin/env python3

"""
test.modtest_d.obj: data object unit tests for the MMGen suite
"""

from decimal import Decimal, getcontext

from ..include.common import vmsg, cfg, parity_dev_amt
from mmgen.protocol import init_proto

def test_equal(res, chk):
	vmsg(f'  checking {res}')
	if type(res) is type:
		assert res is chk, f'{res} != {chk}'
	else:
		assert res == chk, f'{res} != {chk}'

def coinamt_test(cls, aa, bb, ut):

	def do(desc, res, chk):
		vmsg(f'{desc:10} = {res:<{cls.max_prec+10}} [{type(res).__name__}]')
		if chk is not None:
			assert res == chk, f'{res} != {chk}'
			assert type(res) is cls, f'{type(res).__name__} != {cls.__name__}'

	vmsg(f'\nTesting {cls.__name__} arithmetic operations...')

	A, B = (Decimal(aa), Decimal(bb))
	a, b = (cls(aa), cls(bb))

	do('A', A, None)
	do('B', B, None)
	do('a', a, A)
	do('b', b, B)
	do('b + a', b + a, B + A)
	do('sum([b,a])', sum([b, a]), B + A)
	do('b - a', b - a, B - A)
	do('b * a', b * a, B * A)
	do('b * A', b * A, B * A)
	do('B * a', B * a, B * A)
	do('b / a', b / a, cls(B / A, from_decimal=True))
	do('b / A', b / A, cls(B / A, from_decimal=True))
	do('a / b', a / b, cls(A / B, from_decimal=True))

	do('a * a / a', a * a / a, A * A / A)
	do('a * b / a', a * b / a, A * B / A)
	do('a * b / b', a * b / b, A * B / B)

	vmsg(f'\nChecking {cls.__name__} error handling...')

	bad_data = (
		('negation',          'NotImplementedError', 'not implemented',    lambda: -a),
		('modulus',           'NotImplementedError', 'not implemented',    lambda: b % a),
		('floor division',    'NotImplementedError', 'not implemented',    lambda: b // a),
		('negative result',   'ObjectInitError',     'cannot be negative', lambda: a - b),
		('operand type',      'TypeError',           'incorrect type',     lambda: a + B),
		('operand type',      'TypeError',           'incorrect type',     lambda: b - A),
	)

	if cls.max_amt is not None:
		bad_data += (
			('result', 'ObjectInitError', 'too large', lambda: b + b),
			('result', 'ObjectInitError', 'too large', lambda: b * b),
		)

	ut.process_bad_data(bad_data)

	vmsg('OK')

class unit_tests:

	altcoin_deps = ('coinamt_alt', 'coinamt_alt2')

	def coinamt(self, name, ut, desc='BTCAmt class'):
		from mmgen.amt import BTCAmt
		for cls, aa, bb in (
				(BTCAmt, '1.2345', '11234567.897'),
			):
			coinamt_test(cls, aa, bb, ut)
		return True

	def coinamt_alt(self, name, ut, desc='LTCAmt, XMRAmt and ETHAmt classes'):
		from mmgen.amt import LTCAmt, XMRAmt, ETHAmt
		for cls, aa, bb in (
				(LTCAmt, '1.2345', '44938271.588'),
				(XMRAmt, '1.2345', '11234567.98765432'),
				(ETHAmt, '1.2345', '11234567.98765432123456'),
			):
			coinamt_test(cls, aa, bb, ut)
		return True

	def coinamt2(self, name, ut, desc='CoinAmt class'):
		from decimal import Decimal
		proto = init_proto(cfg, 'btc', network='testnet', need_amt=True)

		test_equal(getcontext().prec, proto.decimal_prec)

		coin_amt = proto.coin_amt
		test_equal(coin_amt.__name__, 'BTCAmt')
		a = coin_amt('1.234')
		a2 = coin_amt('2.468')

		# addition with integer zero:
		b = a + 0 # __add__
		b = 0 + a # __radd__
		test_equal(sum([a, a]), a2) # __radd__ (sum() starts with integer 0)

		# __add__
		b = coin_amt('333.2456')
		test_equal(a + b, coin_amt('334.4796'))

		# __sub__
		test_equal(a - coin_amt('1'), coin_amt('0.234'))
		test_equal(coin_amt('2') - a, coin_amt('0.766'))

		# __mul__
		b = a * 2
		test_equal(type(b), coin_amt)
		test_equal(b, a2)

		# __rmul__
		b = 2 * a
		test_equal(type(b), coin_amt)
		test_equal(b, a2)

		# __truediv__
		b = a / 2
		test_equal(type(b), coin_amt)
		test_equal(b, coin_amt('0.617'))

		# __rtruediv__
		b = 2 / a
		test_equal(type(b), coin_amt)
		test_equal(b, coin_amt('1.62074554'))

		def bad1(): b = a + 1
		def bad2(): b = a - 1
		def bad3(): a + Decimal(1)
		def bad4(): b = a + 0.0
		def bad5(): b = a - 0.0

		def bad1r(): b = 1 + a
		def bad2r(): b = 3 - a
		def bad3r(): Decimal(1) + a
		def bad4r(): b = 0.0 + a
		def bad5r(): b = 0.0 - a

		def bad10(): b = coin_amt('1') - a
		def bad11(): b = a * -2
		def bad12(): b = a / -2
		def bad13(): b = a - coin_amt('2')
		def bad14(): b = -2 * a
		def bad15(): b = -2 / a

		def bad16(): b = coin_amt(a)

		vmsg('Testing error handling:')

		ut.process_bad_data(
			(
				('addition with int',      'TypeError',       'incorrect type',     bad1),
				('subtraction with int',   'TypeError',       'incorrect type',     bad2),
				('addition with Decimal',  'TypeError',       'incorrect type',     bad3),
				('addition with float',    'TypeError',       'incorrect type',     bad4),
				('subtraction with float', 'TypeError',       'incorrect type',     bad5),

				('addition with int',      'TypeError',       'incorrect type',     bad1r),
				('subtraction with int',   'TypeError',       'incorrect type',     bad2r),
				('addition with Decimal',  'TypeError',       'incorrect type',     bad3r),
				('addition with float',    'TypeError',       'incorrect type',     bad4r),
				('subtraction with float', 'TypeError',       'incorrect type',     bad5r),

				('negative result',        'ObjectInitError', 'cannot be negative', bad10),
				('negative result',        'ObjectInitError', 'cannot be negative', bad11),
				('negative result',        'ObjectInitError', 'cannot be negative', bad12),
				('negative result',        'ObjectInitError', 'cannot be negative', bad13),
				('negative result',        'ObjectInitError', 'cannot be negative', bad14),
				('negative result',        'ObjectInitError', 'cannot be negative', bad15),

				('double initialization',  'TypeError',        'is instance',       bad16),
			),
			pfx = '')


		return True

	def coinamt_alt2(self, name, ut, desc='CoinAmt class (altcoins)'):
		proto = init_proto(cfg, 'etc', network='regtest', need_amt=True)
		test_equal(getcontext().prec, proto.decimal_prec)
		coin_amt = proto.coin_amt
		dev_amt = coin_amt(parity_dev_amt, from_unit='wei')
		dev_amt_s   = '1606938044258990275541962092341162602522202.993782792835301376'
		dev_amt_a1  = '1606938044258990275541962092341162602522203.993782792835301377'
		dev_amt_s1  = '1606938044258990275541962092341162602522201.993782792835301375'
		dev_amt_d2  = '803469022129495137770981046170581301261101.496891396417650688'
		dev_amt_d10 = '160693804425899027554196209234116260252220.299378279283530138'
		test_equal(str(dev_amt), dev_amt_s)
		addend = coin_amt('1.000000000000000001')
		test_equal(dev_amt + addend, coin_amt(dev_amt_a1))
		test_equal(dev_amt - addend, coin_amt(dev_amt_s1))
		test_equal(dev_amt / coin_amt('2'), coin_amt(dev_amt_d2))
		test_equal(dev_amt / coin_amt('10'), coin_amt(dev_amt_d10))
		test_equal(2 / coin_amt('0.3456'), coin_amt('5.787037037037037037'))
		test_equal(2.345 * coin_amt('2.3456'), coin_amt('5.500432000000000458'))
		return True
