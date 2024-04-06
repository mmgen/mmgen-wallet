#!/usr/bin/env python3

"""
test.unit_tests_d.ut_misc: miscellaneous unit tests for the MMGen suite
"""

import re
from collections import namedtuple

from mmgen.color import yellow, blue
from ..include.common import vmsg

class unit_tests:

	def xmrwallet_uarg_info(self,name,ut): # WIP
		from mmgen.xmrwallet import xmrwallet_uarg_info as uarg_info
		vs = namedtuple('vector_data', ['text', 'groups'])
		fs = '{:16} {}'

		vmsg(blue('  ' + fs.format('ID','ANNOT')))
		for k,v in uarg_info.items():
			vmsg('  ' + fs.format(k, v[0]))

		vectors = {
			'sweep_spec': (
				vs('1:2',     "('1', '2', None, None)"),
				vs('1:2,3',   "('1', '2', '3', None)"),
				vs('1:2,3:4', "('1', '2', '3', '4')"),
			),
		}
		
		vmsg('')
		for k,v in uarg_info.items():
			vmsg(f'  {k}')
			if k in vectors:
				vmsg(f'    pat: {v.pat}')
				vmsg(f'    vectors:')
				for vec in vectors[k]:
					m = re.match(v.pat, vec.text)
					vmsg(f'      {vec.text:10} ==> {m.groups()}')
					assert str(m.groups()) == vec.groups
			else:
				vmsg(yellow('    TBD'))

		return True

	def pyversion(self,name,ut):
		from mmgen.pyversion import PythonVersion,python_version

		ver = {}
		fs = '{:<7} {:<9} {:<5} {}'
		vmsg('\n' + fs.format('Version','PyVersion','Major','Minor'))

		for k in ('current','3.3','3.12','4.3','7.0'):
			obj = python_version if k == 'current' else PythonVersion(k)
			major,minor = [int(s) for s in obj.split('.')]
			assert obj.major == major and obj.minor == minor
			vmsg(fs.format(k.upper(),obj,major,minor))
			ver[k] = obj

		vmsg('\nPerforming comparison tests:')

		assert ver['3.3'] == '3.3'

		assert ver['current'] < ver['7.0']
		assert ver['3.3']     < ver['4.3']
		assert ver['3.12']    < ver['7.0']
		assert ver['3.3']     < ver['3.12']

		assert ver['current'] < '7.0'
		assert ver['3.3']     < '4.3'
		assert ver['3.12']    < '7.0'
		assert ver['3.3']     < '3.12' # ensure we’re comparing numerically, not stringwise

		assert ver['current'] <= ver['current']
		assert ver['3.3']     <= '4.3'
		assert ver['3.12']    <= '7.0'
		assert ver['3.3']     <= '3.12'

		assert ver['current'] == ver['current']
		assert ver['3.3']     == ver['3.3']
		assert ver['3.3']     != ver['3.12']
		assert ver['3.3']     != ver['4.3']
		assert ver['3.3']     == '3.3'
		assert ver['3.3']     != '3.12'
		assert ver['3.3']     != '4.3'

		assert ver['current'] > '3.6'
		assert ver['7.0']     > ver['current']
		assert ver['4.3']     > '3.3'
		assert ver['3.12']    > '3.3'

		assert ver['current'] >= ver['current']
		assert ver['7.0']     >= ver['current']
		assert ver['4.3']     >= '3.3'
		assert ver['3.12']    >= '3.12'
		assert ver['3.12']    >= '3.3'

		assert '3.0' < ver['3.12'] < '3.13'
		assert '3.9' < ver['3.12'] # ensure we’re reverse comparing numerically, not stringwise
		assert '3.3' < ver['4.3']  <= '4.3'
		assert '4.3' <= ver['4.3'] <= '4.3'
		assert '4.3' == ver['4.3'] == '4.3'

		return True
