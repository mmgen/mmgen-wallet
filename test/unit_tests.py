#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>
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

repo_root = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),os.pardir)))
os.chdir(repo_root)
sys.path[0] = repo_root
os.environ['MMGEN_TEST_SUITE'] = '1'

# Import these _after_ prepending repo_root to sys.path
from mmgen.common import *

opts_data = {
	'text': {
		'desc': "Unit tests for the MMGen suite",
		'usage':'[options] [tests]',
		'options': """
-h, --help       Print this help message
-f, --fast       Speed up execution by reducing rounds on some tests
-l, --list       List available tests
-n, --names      Print command names instead of descriptions
-q, --quiet      Produce quieter output
-v, --verbose    Produce more verbose output
""",
	'notes': """
If no test is specified, all available tests are run
	"""
	}
}

sys.argv = [sys.argv[0]] + ['--skip-cfg-file'] + sys.argv[1:]
cmd_args = opts.init(opts_data)

def exit_msg():
	t = int(time.time()) - start_time
	gmsg('All requested tests finished OK, elapsed time: {:02}:{:02}'.format(t//60,t%60))

all_tests = [fn[3:-3] for fn in os.listdir(os.path.join(repo_root,'test','unit_tests_d')) if fn[:3] == 'ut_']

start_time = int(time.time())

if opt.list:
	Die(0,' '.join(all_tests))

try:
	for test in cmd_args:
		if test not in all_tests:
			die(1,"'{}': test not recognized".format(test))

	for test in (cmd_args or all_tests):
		exec('from test.unit_tests_d.ut_{m} import {m}'.format(m=test))
		gmsg('Running unit test {}'.format(test))
		t = globals()[test]()
		if not t.run_test(test):
			rdie(1,'Unit test {!r} failed'.format(test))
		exec('del {}'.format(test))

	exit_msg()
except KeyboardInterrupt:
	die(1,green('\nExiting at user request'))
