#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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

import sys,os,time,importlib,platform

from include.tests_header import repo_root
from include.common import end_msg
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
-N, --node-tools          Select node-tools unit tests
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

opts.UserOpts._reset_ok += ('use_internal_keccak_module',)

cmd_args = opts.init(opts_data)

file_pfx = 'nt_' if opt.node_tools else 'ut_'

all_tests = sorted(
	[fn[3:-3] for fn in os.listdir(os.path.join(repo_root,'test','unit_tests_d')) if fn[:3] == file_pfx])

exclude = opt.exclude.split(',') if opt.exclude else []

for e in exclude:
	if e not in all_tests:
		die(1,f'{e!r}: invalid parameter for --exclude (no such test)')

start_time = int(time.time())

if opt.list:
	Msg(' '.join(all_tests))
	sys.exit(0)

class UnitTestHelpers(object):

	@classmethod
	def process_bad_data(cls,data):
		if os.getenv('PYTHONOPTIMIZE'):
			ymsg('PYTHONOPTIMIZE set, skipping error handling tests')
			return
		import re
		desc_w = max(len(e[0]) for e in data)
		exc_w = max(len(e[1]) for e in data)
		m_exc = '{!r}: incorrect exception type (expected {!r})'
		m_err = '{!r}: incorrect error msg (should match {!r}'
		m_noraise = "\nillegal action 'bad {}' failed to raise exception {!r}"
		for (desc,exc_chk,emsg_chk,func) in data:
			try:
				vmsg_r('  bad {:{w}}'.format( desc+':', w=desc_w+1 ))
				func()
			except Exception as e:
				exc = type(e).__name__
				emsg = e.args[0]
				vmsg(' {:{w}} [{}]'.format( exc, emsg, w=exc_w ))
				assert exc == exc_chk, m_exc.format(exc,exc_chk)
				assert re.search(emsg_chk,emsg), m_err.format(emsg,emsg_chk)
			else:
				die(4,m_noraise.format(desc,exc_chk))

tests_seen = []

def run_test(test,subtest=None):
	modname = f'test.unit_tests_d.{file_pfx}{test}'
	mod = importlib.import_module(modname)

	def run_subtest(subtest):
		msg(f'Running unit subtest {test}.{subtest}')
		t = getattr(mod,'unit_tests')()
		ret = getattr(t,subtest)(test,UnitTestHelpers)
		if type(ret).__name__ == 'coroutine':
			ret = run_session(ret)
		if not ret:
			die(4,f'Unit subtest {subtest!r} failed')
		pass

	if test not in tests_seen:
		gmsg(f'Running unit test {test}')
		tests_seen.append(test)

	if subtest:
		run_subtest(subtest)
	else:
		if hasattr(mod,'unit_tests'): # new class-based API
			t = getattr(mod,'unit_tests')
			altcoin_deps = getattr(t,'altcoin_deps',())
			win_skip = getattr(t,'win_skip',())
			arm_skip = getattr(t,'arm_skip',())
			subtests = [k for k,v in t.__dict__.items() if type(v).__name__ == 'function']
			for subtest in subtests:
				if opt.no_altcoin_deps and subtest in altcoin_deps:
					qmsg(gray(f'Invoked with --no-altcoin-deps, so skipping {subtest!r}'))
					continue
				if g.platform == 'win' and subtest in win_skip:
					qmsg(gray(f'Skipping {subtest!r} for Windows platform'))
					continue
				elif platform.machine() == 'aarch64' and subtest in arm_skip:
					qmsg(gray(f'Skipping {subtest!r} for ARM platform'))
					continue
				run_subtest(subtest)
		else:
			if not mod.unit_test().run_test(test,UnitTestHelpers):
				die(4,'Unit test {test!r} failed')

try:
	for test in (cmd_args or all_tests):
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
