#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
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
test/unit_tests.py: Unit tests for the MMGen suite
"""

import sys,os,time,importlib,platform

import include.test_init

from mmgen.devinit import init_dev
init_dev()

from mmgen.common import *
from test.include.common import set_globals,end_msg

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
-L, --list-subtests       List available tests and subtests
-n, --names               Print command names instead of descriptions
-q, --quiet               Produce quieter output
-x, --exclude=T           Exclude tests 'T' (comma-separated)
-v, --verbose             Produce more verbose output
""",
	'notes': """
If no test is specified, all available tests are run
	"""
	}
}

sys.argv.insert(1,'--skip-cfg-file')

cfg = Config(opts_data=opts_data)

type(cfg)._reset_ok += ('use_internal_keccak_module','debug_addrlist')

set_globals(cfg)

file_pfx = 'ut_'

tests_d = os.path.join(include.test_init.repo_root,'test','unit_tests_d')

all_tests = sorted(fn[len(file_pfx):-len('.py')] for fn in os.listdir(tests_d) if fn.startswith(file_pfx))

exclude = cfg.exclude.split(',') if cfg.exclude else []

for e in exclude:
	if e not in all_tests:
		die(1,f'{e!r}: invalid parameter for --exclude (no such test)')

start_time = int(time.time())

if cfg.list:
	Msg(' '.join(all_tests))
	sys.exit(0)

if cfg.list_subtests:
	def gen():
		for test in all_tests:
			mod = importlib.import_module(f'test.unit_tests_d.{file_pfx}{test}')
			if hasattr(mod,'unit_tests'):
				t = getattr(mod,'unit_tests')
				subtests = [k for k,v in t.__dict__.items() if type(v).__name__ == 'function' and k[0] != '_']
				yield fs.format( test, ' '.join(f'{subtest}' for subtest in subtests) )
			else:
				yield test
	fs = '{:%s} {}' % max(len(t) for t in all_tests)
	Msg( fs.format('TEST','SUBTESTS') + '\n' + '\n'.join(gen()) )
	sys.exit(0)

class UnitTestHelpers:

	def __init__(self,subtest_name):
		self.subtest_name = subtest_name

	def skip_msg(self,desc):
		cfg._util.qmsg(gray(f'Skipping subtest {self.subtest_name.replace("_","-")!r} for {desc}'))

	def process_bad_data(self,data):
		if os.getenv('PYTHONOPTIMIZE'):
			ymsg('PYTHONOPTIMIZE set, skipping error handling tests')
			return
		import re
		desc_w = max(len(e[0]) for e in data)
		exc_w = max(len(e[1]) for e in data)
		m_exc = '{!r}: incorrect exception type (expected {!r})'
		m_err = '{!r}: incorrect error msg (should match {!r}'
		m_noraise = "\nillegal action 'bad {}' failed to raise an exception (expected {!r})"
		for (desc,exc_chk,emsg_chk,func) in data:
			try:
				cfg._util.vmsg_r('  bad {:{w}}'.format( desc+':', w=desc_w+1 ))
				func()
			except Exception as e:
				exc = type(e).__name__
				emsg = e.args[0]
				cfg._util.vmsg(' {:{w}} [{}]'.format( exc, emsg, w=exc_w ))
				assert exc == exc_chk, m_exc.format(exc,exc_chk)
				assert re.search(emsg_chk,emsg), m_err.format(emsg,emsg_chk)
			else:
				die(4,m_noraise.format(desc,exc_chk))

tests_seen = []

def run_test(test,subtest=None):
	mod = importlib.import_module(f'test.unit_tests_d.{file_pfx}{test}')

	def run_subtest(subtest):
		subtest_disp = subtest.replace('_','-')
		msg(f'Running unit subtest {test}.{subtest_disp}')

		t = getattr(mod,'unit_tests')()
		if hasattr(t,'_pre_subtest'):
			getattr(t,'_pre_subtest')(test,subtest,UnitTestHelpers(subtest))

		try:
			ret = getattr(t,subtest.replace('-','_'))(test,UnitTestHelpers(subtest))
			if type(ret).__name__ == 'coroutine':
				ret = async_run(ret)
		except:
			raise

		if hasattr(t,'_post_subtest'):
			getattr(t,'_post_subtest')(test,subtest,UnitTestHelpers(subtest))

		if not ret:
			die(4,f'Unit subtest {subtest_disp!r} failed')

	if test not in tests_seen:
		gmsg(f'Running unit test {test}')
		tests_seen.append(test)

	if hasattr(mod,'unit_tests'): # new class-based API
		t = getattr(mod,'unit_tests')()
		altcoin_deps = getattr(t,'altcoin_deps',())
		win_skip = getattr(t,'win_skip',())
		arm_skip = getattr(t,'arm_skip',())
		subtests = (
			[subtest] if subtest else
			[k for k,v in type(t).__dict__.items() if type(v).__name__ == 'function' and k[0] != '_']
		)
		if hasattr(t,'_pre'):
			t._pre()
		for subtest in subtests:
			subtest_disp = subtest.replace('_','-')
			if cfg.no_altcoin_deps and subtest in altcoin_deps:
				cfg._util.qmsg(gray(f'Invoked with --no-altcoin-deps, so skipping subtest {subtest_disp!r}'))
				continue
			if gc.platform == 'win' and subtest in win_skip:
				cfg._util.qmsg(gray(f'Skipping subtest {subtest_disp!r} for Windows platform'))
				continue
			elif platform.machine() == 'aarch64' and subtest in arm_skip:
				cfg._util.qmsg(gray(f'Skipping subtest {subtest_disp!r} for ARM platform'))
				continue
			run_subtest(subtest)
		if hasattr(t,'_post'):
			t._post()
	else:
		assert not subtest, f'{subtest!r}: subtests not supported for this unit test'
		if not mod.unit_test().run_test(test,UnitTestHelpers(test)):
			die(4,'Unit test {test!r} failed')

try:
	for test in (cfg._args or all_tests):
		if '.' in test:
			test,subtest = test.split('.')
		else:
			subtest = None
		if test not in all_tests:
			die(1,f'{test!r}: test not recognized')
		if test not in exclude:
			run_test(test,subtest=subtest)
	end_msg(int(time.time()) - start_time)
except KeyboardInterrupt:
	die(1,green('\nExiting at user request'))
