#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
test/unit_tests.py:  Unit tests for the MMGen suite
"""

import sys,os,time

from include.tests_header import repo_root
from mmgen.common import *

opts_data = {
	'text': {
		'desc': "Unit tests for the MMGen suite",
		'usage':'[options] [test | test.subtest]...',
		'options': """
-h, --help                Print this help message
-a, --no-altcoin-deps     Skip tests requiring altcoin daemons, libs or utils
-A, --no-daemon-autostart Don't start and stop daemons automatically
-D, --no-daemon-stop      Don't stop auto-started daemons after running tests
-f, --fast                Speed up execution by reducing rounds on some tests
-l, --list                List available tests
-n, --names               Print command names instead of descriptions
-q, --quiet               Produce quieter output
-v, --verbose             Produce more verbose output
""",
	'notes': """
If no test is specified, all available tests are run
	"""
	}
}

sys.argv.insert(1,'--skip-cfg-file')
cmd_args = opts.init(opts_data)

def exit_msg():
	t = int(time.time()) - start_time
	gmsg('All requested tests finished OK, elapsed time: {:02}:{:02}'.format(t//60,t%60))

all_tests = sorted(
	[fn[3:-3] for fn in os.listdir(os.path.join(repo_root,'test','unit_tests_d')) if fn[:3] == 'ut_'])

start_time = int(time.time())

if opt.list:
	Die(0,' '.join(all_tests))

class UnitTestHelpers(object):

	@classmethod
	def process_bad_data(cls,data):
		import re
		desc_w = max(len(e[0]) for e in data)
		exc_w = max(len(e[1]) for e in data)
		m_exc = '{!r}: incorrect exception type (expected {!r})'
		m_err = '{!r}: incorrect error msg (should match {!r}'
		m_noraise = "\nillegal action 'bad {}' failed to raise exception {!r}"
		for (desc,exc_chk,emsg_chk,func) in data:
			try:
				vmsg_r('  bad {:{w}}'.format(desc+':',w=desc_w+1))
				func()
			except Exception as e:
				exc = type(e).__name__
				emsg = e.args[0]
				vmsg(' {:{w}} [{}]'.format(exc,emsg,w=exc_w))
				assert exc == exc_chk, m_exc.format(exc,exc_chk)
				assert re.search(emsg_chk,emsg), m_err.format(emsg,emsg_chk)
			else:
				rdie(3,m_noraise.format(desc,exc_chk))

def run_test(test,subtest=None):
	modname = 'test.unit_tests_d.ut_{}'.format(test)
	mod = importlib.import_module(modname)

	def run_subtest(subtest):
		gmsg(f'Running unit subtest {test}.{subtest}')
		t = getattr(mod,'unit_tests')()
		if not getattr(t,subtest)(test,UnitTestHelpers):
			rdie(1,f'Unit subtest {subtest!r} failed')
		pass

	if subtest:
		run_subtest(subtest)
	else:
		gmsg(f'Running unit test {test}')
		if hasattr(mod,'unit_tests'): # new class-based API
			t = getattr(mod,'unit_tests')
			altcoin_deps = getattr(t,'altcoin_deps',())
			subtests = [k for k,v in t.__dict__.items() if type(v).__name__ == 'function']
			for subtest in subtests:
				if opt.no_altcoin_deps and subtest in altcoin_deps:
					qmsg(gray(f'Invoked with --no-altcoin-deps, so skipping {subtest!r}'))
					continue
				run_subtest(subtest)
		else:
			if not mod.unit_test().run_test(test,UnitTestHelpers):
				rdie(1,'Unit test {test!r} failed')

try:
	import importlib
	for test in (cmd_args or all_tests):
		if '.' in test:
			test,subtest = test.split('.')
		else:
			subtest = None
		if test not in all_tests:
			die(1,f'{test!r}: test not recognized')
		run_test(test,subtest=subtest)
	exit_msg()
except KeyboardInterrupt:
	die(1,green('\nExiting at user request'))
