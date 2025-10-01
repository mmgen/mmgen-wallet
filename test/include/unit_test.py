#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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
test.include.unit_test: Unit test framework for the MMGen suite
"""

import sys, os, time, importlib, platform, asyncio

from .test_init import repo_root

# for the unit tests, violate MMGen Project best practices and allow use of the dev tools
# in production code:
if not os.getenv('MMGEN_DEVTOOLS'):
	from mmgen.devinit import init_dev
	init_dev()

from mmgen.cfg import Config, gc, gv
from mmgen.color import gray, brown, orange, yellow, red
from mmgen.util import msg, msg_r, gmsg, ymsg, Msg, isAsync

from test.include.common import set_globals, end_msg

def die(ev, s):
	msg((red if ev > 1 else yellow)(s))
	sys.exit(ev)

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

if os.path.islink(Config.test_datadir):
	os.unlink(Config.test_datadir)

sys.argv.insert(1, '--skip-cfg-file')

cfg = Config(opts_data=opts_data)

type(cfg)._reset_ok += ('use_internal_keccak_module', 'debug_addrlist')

set_globals(cfg)

test_type = {
	'modtest.py':    'unit',
	'daemontest.py': 'daemon',
}[gc.prog_name]

test_subdir = gc.prog_name.removesuffix('.py') + '_d'

test_dir = os.path.join(repo_root, 'test', test_subdir)

all_tests = sorted(fn.removesuffix('.py') for fn in os.listdir(test_dir) if not fn.startswith('_'))

exclude = cfg.exclude.split(',') if cfg.exclude else []

if cfg.no_altcoin_deps:
	ymsg(f'{gc.prog_name}: skipping altcoin tests by user request')
	altcoin_tests = importlib.import_module(f'test.{test_subdir}').altcoin_tests

for e in exclude:
	if e not in all_tests:
		die(1, f'{e!r}: invalid parameter for --exclude (no such test)')

start_time = int(time.time())

if cfg.list:
	Msg(' '.join(all_tests))
	sys.exit(0)

if cfg.list_subtests:
	def gen():
		for test in all_tests:
			mod = importlib.import_module(f'test.{test_subdir}.{test}')
			if hasattr(mod, 'unit_tests'):
				t = getattr(mod, 'unit_tests')
				subtests = [k for k, v in t.__dict__.items() if type(v).__name__ == 'function' and k[0] != '_']
				yield fs.format(test, ' '.join(f'{subtest}' for subtest in subtests))
			else:
				yield test
	fs = '{:%s} {}' % max(len(t) for t in all_tests)
	Msg(fs.format('TEST', 'SUBTESTS') + '\n' + '\n'.join(gen()))
	sys.exit(0)

def silence():
	if not cfg.verbose:
		global stdout_save, stderr_save
		stdout_save = sys.stdout
		stderr_save = sys.stderr
		sys.stdout = sys.stderr = gv.stdout = gv.stderr = open(os.devnull, 'w')

def end_silence():
	if not cfg.verbose:
		global stdout_save, stderr_save
		sys.stdout = gv.stdout = stdout_save
		sys.stderr = gv.stderr = stderr_save

class UnitTestHelpers:

	def __init__(self, subtest_name):
		self.subtest_name = subtest_name

	def skip_msg(self, desc):
		cfg._util.qmsg(gray(
			f'Skipping {test_type} subtest {self.subtest_name.replace("_", "-")!r} for {desc}'
		))

	def process_bad_data(self, data, pfx='bad '):
		if os.getenv('PYTHONOPTIMIZE'):
			ymsg('PYTHONOPTIMIZE set, skipping error handling tests')
			return
		import re
		desc_w = max(len(e[0]) for e in data)
		exc_w = max(len(e[1]) for e in data)
		m_exc = '{!r}: incorrect exception type (expected {!r})'
		m_err = '{!r}: incorrect error msg (should match {!r}'
		m_noraise = "\nillegal action '{}{}' failed to raise an exception (expected {!r})"
		for (desc, exc_chk, emsg_chk, func) in data:
			try:
				cfg._util.vmsg_r('  {}{:{w}}'.format(pfx, desc+':', w=desc_w+1))
				asyncio.run(func()) if isAsync(func) else func()
			except Exception as e:
				exc = type(e).__name__
				emsg = e.args[0] if e.args else '(unspecified error)'
				cfg._util.vmsg(f' {exc:{exc_w}} [{emsg}]')
				assert exc == exc_chk, m_exc.format(exc, exc_chk)
				assert re.search(emsg_chk, emsg), m_err.format(emsg, emsg_chk)
			else:
				die(4, m_noraise.format(pfx, desc, exc_chk))

tests_seen = []

def run_test(test, subtest=None):

	def run_subtest(t, subtest):
		subtest_disp = subtest.replace('_', '-')
		msg(brown(f'Running {test_type} subtest ') + orange(f'{test}.{subtest_disp}'))

		if getattr(t, 'silence_output', False):
			silence()

		if hasattr(t, '_pre_subtest'):
			getattr(t, '_pre_subtest')(test, subtest, UnitTestHelpers(subtest))

		try:
			func = getattr(t, subtest.replace('-', '_'))
			c = func.__code__
			do_desc = c.co_varnames[c.co_argcount-1] == 'desc'
			if do_desc:
				if cfg.verbose:
					msg(f'Testing {func.__defaults__[0]}')
				elif not cfg.quiet:
					msg_r(f'Testing {func.__defaults__[0]}...')

			if isAsync(func):
				ret = asyncio.run(func(test, UnitTestHelpers(subtest)))
			else:
				ret = func(test, UnitTestHelpers(subtest))

			if do_desc and not cfg.quiet:
				msg('OK\n' if cfg.verbose else 'OK')
		except:
			if getattr(t, 'silence_output', False):
				end_silence()
			raise

		if hasattr(t, '_post_subtest'):
			getattr(t, '_post_subtest')(test, subtest, UnitTestHelpers(subtest))

		if getattr(t, 'silence_output', False):
			end_silence()

		if not ret:
			die(4, f'Unit subtest {subtest_disp!r} failed')

	if test not in tests_seen:
		gmsg(f'Running {test_type} test {test}')
		tests_seen.append(test)

	if cfg.no_altcoin_deps and test in altcoin_tests:
		msg(gray(f'Skipping {test_type} test {test!r} [--no-altcoin-deps]'))
		return

	mod = importlib.import_module(f'test.{test_subdir}.{test}')

	if hasattr(mod, 'unit_tests'): # new class-based API
		t = getattr(mod, 'unit_tests')()
		altcoin_deps = getattr(t, 'altcoin_deps', ())
		win_skip = getattr(t, 'win_skip', ())
		mac_skip = getattr(t, 'mac_skip', ())
		arm_skip = getattr(t, 'arm_skip', ())
		riscv_skip = getattr(t, 'riscv_skip', ())
		fast_skip = getattr(t, 'fast_skip', ())
		subtests = (
			[subtest] if subtest else
			[k for k, v in type(t).__dict__.items() if type(v).__name__ == 'function' and k[0] != '_']
		)
		if hasattr(t, '_pre'):
			t._pre()

		def subtest_skip_msg(name, add_msg):
			cfg._util.qmsg(gray(
				'Skipping {} subtest {!r} {}'.format(test_type, name.replace('_', '-'), add_msg)
			))

		for _subtest in subtests:
			if cfg.no_altcoin_deps and _subtest in altcoin_deps:
				subtest_skip_msg(_subtest, '[--no-altcoin-deps]')
				continue
			if cfg.fast and _subtest in fast_skip:
				subtest_skip_msg(_subtest, '[--fast]')
				continue
			if sys.platform == 'win32' and _subtest in win_skip:
				subtest_skip_msg(_subtest, 'for Windows platform')
				continue
			if sys.platform == 'darwin' and _subtest in mac_skip:
				subtest_skip_msg(_subtest, 'for macOS platform')
				continue
			if platform.machine() == 'aarch64' and _subtest in arm_skip:
				subtest_skip_msg(_subtest, 'for ARM platform')
				continue
			if platform.machine() == 'riscv64' and _subtest in riscv_skip:
				subtest_skip_msg(_subtest, 'for RISC-V platform')
				continue
			run_subtest(t, _subtest)
		if hasattr(t, '_post'):
			t._post()
	else:
		assert not subtest, f'{subtest!r}: subtests not supported for this {test_type} test'
		if not mod.unit_test().run_test(test, UnitTestHelpers(test)):
			die(4, 'Unit test {test!r} failed')

def main():
	for test in (cfg._args or all_tests):
		if '.' in test:
			test, subtest = test.split('.')
		else:
			subtest = None
		if test not in all_tests:
			die(1, f'{test!r}: test not recognized')
		if test not in exclude:
			run_test(test, subtest=subtest)
	end_msg(int(time.time()) - start_time)

from mmgen.main import launch
launch(func=main)
