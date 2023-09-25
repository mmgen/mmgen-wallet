#!/usr/bin/env python3

"""
test.unit_tests_d.ut_misc: utility unit tests for the MMGen suite
"""

from ..include.common import vmsg
from mmgen.util import fmt_list,list_gen

class unit_tests:

	def fmt_list(self,name,ut):

		samples = {
			'pids': [18234,18444,19324],
			'vardata': [None,True,1234,'sample string'],
		}
		chks = {
			'vardata': {
				None:        "'None', 'True', '1234', 'sample string'",
				'dfl':       "'None', 'True', '1234', 'sample string'",
				'utf8':      "“None”, “True”, “1234”, “sample string”",
				'bare':      "None True 1234 'sample string'",
				'no_quotes': "None, True, 1234, sample string",
				'no_spc':    "'None','True','1234','sample string'",
				'min':       "None,True,1234,sample string",
				'repr':      "None, True, 1234, 'sample string'",
				'csv':       "None,True,1234,'sample string'",
				'col':       "    + None\n    + True\n    + 1234\n    + sample string",
			}

		}

		col1_w = max(len(str(e)) for e in list(chks.values())[0]) + 1

		for name,sample in samples.items():
			vmsg(cyan(f'Input: {sample}'))
			for fmt,chk in list(chks.values())[0].items():
				spc = '\n' if fmt in ('col','list') else ' '
				indent = '    + ' if fmt == 'col' else ''
				res = fmt_list(sample,fmt=fmt,indent=indent) if fmt else fmt_list(sample,indent=indent)
				vmsg(f'  {str(fmt)+":":{col1_w}}{spc}{res}')
				if name in chks:
					assert res == chks[name][fmt], f'{res} != {chks[name][fmt]}'

		vmsg('')
		return True

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
