#!/usr/bin/env python3

"""
test.unit_tests_d.ut_misc: utility unit tests for the MMGen suite
"""

from ..include.common import vmsg
from mmgen.util import list_gen

class unit_tests:

	def list_gen(self,name,ut):
		res = list_gen(
			['a'],
			['b', 1==2],
			['c', 'x'],
			['d', int],
			['e', None, 1, 'f', isinstance(7,int)],
			['g', 'h', 0],
			[None],
			[0],
			[False],
		)
		chk = ['a', 'c', 'd', 'e', None, 1, 'f', None, 0, False]

		vmsg('=> ' + str(res))
		assert res == chk, f'{res} != {chk}'
		vmsg('')
		return True
