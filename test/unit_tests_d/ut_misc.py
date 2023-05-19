#!/usr/bin/env python3

"""
test.unit_tests_d.ut_misc: miscellaneous unit tests for the MMGen suite
"""

class unit_tests:

	def pyversion(self,name,ut):
		from ..include.common import vmsg
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
