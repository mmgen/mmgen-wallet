#!/usr/bin/env python3

"""
test.unit_tests_d.ut_obj: data object unit tests for the MMGen suite
"""

from decimal import Decimal

from ..include.common import vmsg

class unit_tests:

	def coinamt(self, name, ut, desc='BTCAmt, LTCAmt, XMRAmt and ETHAmt classes'):

		from mmgen.amt import BTCAmt,LTCAmt,XMRAmt,ETHAmt

		for cls,aa,bb in (
				( BTCAmt, '1.2345', '11234567.897' ),
				( LTCAmt, '1.2345', '44938271.588' ),
				( XMRAmt, '1.2345', '11234567.98765432' ),
				( ETHAmt, '1.2345', '11234567.98765432123456' ),
			):

			def do(desc,res,chk):
				vmsg(f'{desc:10} = {res:<{cls.max_prec+10}} [{type(res).__name__}]')
				if chk is not None:
					assert res == chk, f'{res} != {chk}'
					assert type(res) is cls, f'{type(res).__name__} != {cls.__name__}'

			vmsg(f'\nTesting {cls.__name__} arithmetic operations...')

			A,B   = ( Decimal(aa), Decimal(bb) )
			a,b   = ( cls(aa),  cls(bb) )

			do('A', A, None)
			do('B', B, None)
			do('a', a, A)
			do('b', b, B)
			do('b + a', b + a, B + A)
			do('sum([b,a])', sum([b,a]), B + A)
			do('b - a', b - a, B - A)
			do('b * a', b * a, B * A)
			do('b * A', b * A, B * A)
			do('B * a', B * a, B * A)
			do('b / a', b / a, cls( B / A, from_decimal=True ))
			do('b / A', b / A, cls( B / A, from_decimal=True ))
			do('a / b', a / b, cls( A / B, from_decimal=True ))

			do('a * a / a', a * a / a, A * A / A)
			do('a * b / a', a * b / a, A * B / A)
			do('a * b / b', a * b / b, A * B / B)

			vmsg(f'\nChecking {cls.__name__} error handling...')

			bad_data = (
				('negation',          'NotImplementedError', 'not implemented',    lambda: -a ),
				('modulus',           'NotImplementedError', 'not implemented',    lambda: b % a ),
				('floor division',    'NotImplementedError', 'not implemented',    lambda: b // a ),
				('negative result',   'ObjectInitError',     'cannot be negative', lambda: a - b ),
				('operand type',      'ValueError',          'incorrect type',     lambda: a + B ),
				('operand type',      'ValueError',          'incorrect type',     lambda: b - A ),
			)

			if cls.max_amt is not None:
				bad_data += (
					('result', 'ObjectInitError', 'too large', lambda: b + b ),
					('result', 'ObjectInitError', 'too large', lambda: b * b ),
				)

			ut.process_bad_data(bad_data)

			vmsg('OK')

		return True
