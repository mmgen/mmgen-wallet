#!/usr/bin/env python3

"""
test.modtest_d.misc: utility unit tests for the MMGen suite
"""

from mmgen.color import cyan
from mmgen.util import fmt_list, fmt_dict, list_gen

from ..include.common import vmsg

class unit_tests:

	def fmt_list(self, name, ut):

		samples = {
			'pids': [18234, 18444, 19324],
			'vardata': [None, True, 1234, 'sample string'],
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

		for _name, sample in samples.items():
			vmsg(cyan(f'Input: {sample}'))
			for fmt in list(chks.values())[0]:
				spc = '\n' if fmt in ('col', 'list') else ' '
				indent = '    + ' if fmt == 'col' else ''
				res = fmt_list(sample, fmt=fmt, indent=indent) if fmt else fmt_list(sample, indent=indent)
				vmsg(f'  {str(fmt)+":":{col1_w}}{spc}{res}')
				if _name in chks:
					assert res == chks[_name][fmt], f'{res} != {chks[_name][fmt]}'

		vmsg('')
		return True

	def fmt_dict(self, name, ut):
		samples = {
			'url': {
				'name': 'Example',
				'desc': 'Sample URL',
				'rank': 1,
				'error': None,
				'url': 'https://example.com/foobar.html',
			},
			'choice': {
				'c': 'curl',
				'a': 'aiohttp',
				'r': 'requests',
			},
			'cmdline': {
				'cmd': ['ls', '-l'],
				'text': 'foo bar',
				'stdin': None,
				'offset': 123,
				'env': {},
			}
		}
		chks = {
		'cmdline': {
			None:           "'cmd' (['ls', '-l']), 'text' (foo bar), 'stdin' (None), 'offset' (123), 'env' ({})",
			'dfl':          "'cmd' (['ls', '-l']), 'text' (foo bar), 'stdin' (None), 'offset' (123), 'env' ({})",
			'square':       "'cmd' [['ls', '-l']], 'text' [foo bar], 'stdin' [None], 'offset' [123], 'env' [{}]",
			'equal':        "'cmd'=['ls', '-l'], 'text'=foo bar, 'stdin'=None, 'offset'=123, 'env'={}",
			'equal_spaced': "'cmd' = ['ls', '-l'], 'text' = foo bar, 'stdin' = None, 'offset' = 123, 'env' = {}",
			'kwargs':       "cmd=['ls', '-l'], text='foo bar', stdin=None, offset=123, env={}",
			'colon':        "cmd:['ls', '-l'], text:'foo bar', stdin:None, offset:123, env:{}",
		}
		}

		col1_w = max(len(str(e)) for e in list(chks.values())[0]) + 1

		for _name, sample in samples.items():
			vmsg(cyan(f'Input: {sample}'))
			for fmt in list(chks.values())[0]:
				res = fmt_dict(sample, fmt=fmt) if fmt else fmt_dict(sample)
				vmsg(f'  {str(fmt)+":":{col1_w}} {res}')
				if _name in chks:
					assert res == chks[_name][fmt], f'{res} != {chks[_name][fmt]}'

		vmsg('')
		return True

	def list_gen(self, name, ut):
		res = list_gen(
			['a'],
			['b', False],
			['c', 'x'],
			['d', int],
			['e', None, 1, 'f', isinstance(7, int)],
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
