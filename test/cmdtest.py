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
test/cmdtest.py: Command test runner for the MMGen wallet system
"""

def check_segwit_opts(proto):
	for k, m in (('segwit', 'S'), ('segwit_random', 'S'), ('bech32', 'B')):
		if getattr(cfg, k) and m not in proto.mmtypes:
			die(1, f'--{k.replace("_", "-")} option incompatible with {proto.cls_name}')

def create_shm_dir(data_dir, trash_dir):
	# Laggy flash media can cause pexpect to fail, so create a temporary directory
	# under '/dev/shm' and put datadir and tmpdirs here.
	import shutil
	from subprocess import run
	if sys.platform in ('win32', 'darwin'):
		for tdir in (data_dir, trash_dir):
			try:
				os.listdir(tdir)
			except:
				pass
			else:
				try:
					shutil.rmtree(tdir)
				except: # we couldn't remove data dir - perhaps regtest daemon is running
					try:
						run(['python3', os.path.join('cmds', 'mmgen-regtest'), 'stop'], check=True)
					except:
						die(4, f'Unable to remove {tdir!r}!')
					else:
						time.sleep(2)
						shutil.rmtree(tdir)
			os.mkdir(tdir, 0o755)
		shm_dir = 'test'
	else:
		tdir, pfx = '/dev/shm', 'mmgen-test-'
		try:
			run(f'rm -rf {tdir}/{pfx}*', shell=True, check=True)
		except Exception as e:
			die(2, f'Unable to delete directory tree {tdir}/{pfx}* ({e.args[0]})')
		try:
			import tempfile
			shm_dir = str(tempfile.mkdtemp('', pfx, tdir))
		except Exception as e:
			die(2, f'Unable to create temporary directory in {tdir} ({e.args[0]})')

		dest = os.path.join(shm_dir, os.path.basename(trash_dir))
		os.mkdir(dest, 0o755)

		run(f'rm -rf {trash_dir}', shell=True, check=True)
		os.symlink(dest, trash_dir)

		dest = os.path.join(shm_dir, os.path.basename(data_dir))
		shutil.move(data_dir, dest) # data_dir was created by Config()
		os.symlink(dest, data_dir)

	return shm_dir

import sys, os, time

# overlay must be set up before importing mmgen mods!
try:
	from include.test_init import repo_root
except ImportError:
	from test.include.test_init import repo_root

from mmgen.cfg import Config
from mmgen.color import red, yellow, green, blue, init_color
from mmgen.util import msg, Msg, rmsg, die

from test.include.common import (
	set_globals,
	cmdtest_py_log_fn,
	cmdtest_py_error_fn,
	mk_tmpdir,
	stop_test_daemons)

try:
	os.unlink(os.path.join(repo_root, cmdtest_py_error_fn))
except:
	pass

os.environ['MMGEN_QUIET'] = '0' # for this script and spawned scripts

opts_data = {
	'sets': [
		('list_current_cmd_groups', True, 'list_cmd_groups', True),
		('demo', True, 'exact_output', True),
		('demo', True, 'buf_keypress', True),
		('demo', True, 'pexpect_spawn', True),
	],
	'text': {
		'desc': 'High-level tests for the MMGen Wallet suite',
		'usage':'[options] [command [..command]] | [command_group[.command_subgroup][:command]]',
		'options': """
-h, --help           Print this help message
--, --longhelp       Print help message for long (global) options
-a, --no-altcoin     Skip altcoin tests (WIP)
-A, --no-daemon-autostart Don't start and stop daemons automatically
-B, --bech32         Generate and use Bech32 addresses
-b, --buf-keypress   Use buffered keypresses as with real human input
                     (often required on slow systems, or under emulation)
-c, --print-cmdline  Print the command line of each spawned command
-C, --coverage       Produce code coverage info using trace module
-x, --debug-pexpect  Produce debugging output for pexpect calls
--, --demo           Add extra delay after each send to make input visible.
                     Implies --exact-output --pexpect-spawn --buf-keypress
-d, --deps-only      Run a command or command subgroup’s dependencies without
                     running the command or command group itself.
-D, --no-daemon-stop Don't stop auto-started daemons after running tests
-E, --direct-exec    Bypass pexpect and execute a command directly (for
                     debugging only)
-e, --exact-output   Show the exact output of the MMGen script(s) being run
-G, --exclude-groups=G Exclude the specified command groups (comma-separated)
-k, --devnet-block-period=N Block time for Ethereum devnet bump tests
-l, --list-cmds      List the test script’s available commands
-L, --list-cmd-groups List the test script’s command groups and subgroups
-g, --list-current-cmd-groups List command groups for current configuration
-n, --names          Display command names instead of descriptions
-N, --no-timings     Suppress display of timing information
-o, --log            Log commands to file {lf!r}
-O, --pexpect-spawn  Use pexpect.spawn instead of popen_spawn (much slower,
                     kut does real terminal emulation)
-p, --pause          Pause between tests, resuming on keypress
-P, --profile        Record the execution time of each script
-q, --quiet          Produce minimal output.  Suppress dependency info
-r, --resume=c       Resume at command 'c' after interrupted run
-R, --resume-after=c Same, but resume at command following 'c'
-t, --step           After resuming, execute one command and stop
-S, --skip-deps      Skip dependency checking for command
-u, --usr-random     Get random data interactively from user
-T, --pexpect-timeout=T Set the timeout for pexpect
-v, --verbose        Produce more verbose output
-W, --no-dw-delete   Don't remove default wallet from data dir after dw tests
                     are done
-X, --exit-after=C   Exit after command 'C'
-y, --segwit         Generate and use Segwit addresses
-Y, --segwit-random  Generate and use a random mix of Segwit and Legacy addrs
""",
		'notes': """

If no command is given, the whole test suite is run for the currently
specified coin (default BTC).

For traceback output and error file support, set the EXEC_WRAPPER_TRACEBACK
environment var
"""
	},
	'code': {
		'options': lambda proto, help_notes, s: s.format(
				lf = cmdtest_py_log_fn
			)
	}
}

# we need some opt values before running opts.init, so parse without initializing:
po = Config(opts_data=opts_data, parse_only=True)._parsed_opts

data_dir = Config.test_datadir

# step 1: delete data_dir symlink in ./test;
if not po.user_opts.get('skip_deps'):
	try:
		os.unlink(data_dir)
	except:
		pass

# step 2: opts.init will create new data_dir in ./test (if not po.user_opts['skip_deps'])
cfg = Config(opts_data=opts_data)

if cfg.no_altcoin and cfg.coin != 'BTC':
	die(1, f'--no-altcoin incompatible with --coin={cfg.coin}')

set_globals(cfg)

type(cfg)._reset_ok += (
	'no_daemon_autostart',
	'names',
	'no_timings',
	'exit_after',
	'resuming',
	'skipping_deps')

cfg.resuming = any(k in po.user_opts for k in ('resume', 'resume_after'))
cfg.skipping_deps = cfg.resuming or 'skip_deps' in po.user_opts

cmd_args = cfg._args

if cfg.pexpect_spawn and sys.platform == 'win32':
	die(1, '--pexpect-spawn option not supported on Windows platform, exiting')

if cfg.daemon_id and cfg.daemon_id in cfg.blacklisted_daemons.split():
	die(1, f'cmdtest.py: daemon {cfg.daemon_id!r} blacklisted, exiting')

# step 3: move data_dir to /dev/shm and symlink it back to ./test:
trash_dir = os.path.join('test', 'trash')
trash_dir2 = os.path.join('test', 'trash2')

if not cfg.skipping_deps:
	shm_dir = create_shm_dir(data_dir, trash_dir)

check_segwit_opts(cfg._proto)

testing_segwit = cfg.segwit or cfg.segwit_random or cfg.bech32

if cfg.test_suite_deterministic:
	cfg.no_timings = True
	init_color(num_colors=0)
	os.environ['MMGEN_DISABLE_COLOR'] = '1' # for this script and spawned scripts

if cfg.profile:
	cfg.names = True

if cfg.exact_output:
	qmsg = qmsg_r = lambda s: None
else:
	qmsg = cfg._util.qmsg
	qmsg_r = cfg._util.qmsg_r

if cfg.skipping_deps:
	cfg.no_daemon_autostart = True

from test.cmdtest_d.include.cfg import cfgs

def create_tmp_dirs(shm_dir):
	if sys.platform in ('win32', 'darwin'):
		for cfg in sorted(cfgs):
			mk_tmpdir(cfgs[cfg]['tmpdir'])
	else:
		os.makedirs(os.path.join('test', 'tmp'), mode=0o755, exist_ok=True)
		for cfg in sorted(cfgs):
			src = os.path.join(shm_dir, cfgs[cfg]['tmpdir'].split('/')[-1])
			mk_tmpdir(src)
			try:
				os.unlink(cfgs[cfg]['tmpdir'])
			except OSError as e:
				if e.errno != 2:
					raise
			finally:
				os.symlink(src, cfgs[cfg]['tmpdir'])

def set_restore_term_at_exit():
	import termios, atexit
	fd = sys.stdin.fileno()
	old = termios.tcgetattr(fd)
	def at_exit():
		termios.tcsetattr(fd, termios.TCSADRAIN, old)
	atexit.register(at_exit)

if __name__ == '__main__':

	if not cfg.skipping_deps: # do this before list cmds exit, so we stay in sync with shm_dir
		create_tmp_dirs(shm_dir)

	if cfg.list_cmds:
		from test.cmdtest_d.include.group_mgr import CmdGroupMgr
		CmdGroupMgr(cfg).list_cmds()
		sys.exit(0)

	if cfg.list_cmd_groups:
		from test.cmdtest_d.include.group_mgr import CmdGroupMgr
		CmdGroupMgr(cfg).list_cmd_groups()
		sys.exit(0)

	if cfg.pause:
		set_restore_term_at_exit()

	from mmgen.exception import TestSuiteSpawnedScriptException
	from test.cmdtest_d.include.runner import CmdTestRunner

	try:
		tr = CmdTestRunner(cfg, repo_root, data_dir, trash_dir, trash_dir2)
		tr.run_tests(cmd_args)
		tr.print_warnings()
		if tr.daemon_started and not cfg.no_daemon_stop:
			stop_test_daemons(tr.network_id, remove_datadir=True)
		if hasattr(tr, 'tg'):
			del tr.tg
		del tr
	except KeyboardInterrupt:
		if tr.daemon_started and not cfg.no_daemon_stop:
			stop_test_daemons(tr.network_id, remove_datadir=True)
		tr.print_warnings()
		if hasattr(tr, 'tg'):
			del tr.tg
		del tr
		die(1, yellow('\ntest.py exiting at user request'))
	except TestSuiteSpawnedScriptException as e:
		# if spawned script is not running under exec_wrapper, output brief error msg:
		if os.getenv('MMGEN_EXEC_WRAPPER'):
			Msg(red(str(e)))
			Msg(blue('cmdtest.py: spawned script exited with error'))
		if hasattr(tr, 'tg'):
			del tr.tg
		del tr
		raise
	except Exception as e:
		if type(e).__name__ == 'TestSuiteException':
			rmsg('TEST ERROR: ' + str(e))
		if hasattr(tr, 'tg'):
			del tr.tg
		del tr
		# if cmdtest.py itself is running under exec_wrapper, re-raise so wrapper can handle exception:
		if os.getenv('MMGEN_EXEC_WRAPPER') or not os.getenv('MMGEN_IGNORE_TEST_PY_EXCEPTION'):
			raise
		die(1, red('Test script exited with error'))
