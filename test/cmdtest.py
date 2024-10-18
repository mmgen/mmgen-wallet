#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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

def check_segwit_opts():
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

import sys, os, time, asyncio

# overlay must be set up before importing mmgen mods!
try:
	from include.test_init import repo_root
except ImportError:
	from test.include.test_init import repo_root

from mmgen.cfg import Config, gc
from mmgen.color import red, yellow, green, blue, cyan, gray, nocolor, init_color
from mmgen.util import msg, Msg, rmsg, bmsg, die, suf, make_timestr

from test.include.common import (
	set_globals,
	cmdtest_py_log_fn,
	cmdtest_py_error_fn,
	mk_tmpdir,
	iqmsg,
	omsg,
	omsg_r,
	ok,
	start_test_daemons,
	stop_test_daemons,
	init_coverage,
	clean,
)

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

from test.cmdtest_d.common import ( # this must be loaded after set_globals()
	get_file_with_ext,
	confirm_continue
)

type(cfg)._reset_ok += (
	'no_daemon_autostart',
	'names',
	'no_timings',
	'exit_after',
	'resuming',
	'skipping_deps')

logging = cfg.log or os.getenv('MMGEN_EXEC_WRAPPER')

cfg.resuming = any(k in po.user_opts for k in ('resume', 'resume_after'))
cfg.skipping_deps = cfg.resuming or 'skip_deps' in po.user_opts

cmd_args = cfg._args

if cfg.pexpect_spawn and sys.platform == 'win32':
	die(1, '--pexpect-spawn option not supported on Windows platform, exiting')

if cfg.daemon_id and cfg.daemon_id in cfg.blacklisted_daemons.split():
	die(1, f'cmdtest.py: daemon {cfg.daemon_id!r} blacklisted, exiting')

network_id = cfg.coin.lower() + ('_tn' if cfg.testnet else '')

proto = cfg._proto

# step 3: move data_dir to /dev/shm and symlink it back to ./test:
trash_dir = os.path.join('test', 'trash')
trash_dir2 = os.path.join('test', 'trash2')

if not cfg.skipping_deps:
	shm_dir = create_shm_dir(data_dir, trash_dir)

check_segwit_opts()

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

from test.cmdtest_d.cfg import cfgs

def list_cmds():

	def gen_output():

		gm = CmdGroupMgr()
		cw, d = 0, []

		yield green('AVAILABLE COMMANDS:')

		for gname in gm.cmd_groups:
			tg = gm.gm_init_group(None, gname, None, None)
			desc = tg.__doc__.strip() if tg.__doc__ else type(tg).__name__
			d.append((gname, desc, gm.cmd_list, gm.dpy_data))
			cw = max(max(len(k) for k in gm.dpy_data), cw)

		for gname, gdesc, clist, dpdata in d:
			yield '\n'+green(f'{gname!r} - {gdesc}:')
			for cmd in clist:
				data = dpdata[cmd]
				yield '    {:{w}} - {}'.format(
					cmd,
					(data if isinstance(data, str) else data[1]),
					w = cw)

	from mmgen.ui import do_pager
	do_pager('\n'.join(gen_output()))

	sys.exit(0)

def do_between():
	if cfg.pause:
		confirm_continue()
	elif (cfg.verbose or cfg.exact_output) and not cfg.skipping_deps:
		sys.stderr.write('\n')

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

class CmdGroupMgr:

	dpy_data = None

	from test.cmdtest_d.cfg import cmd_groups_dfl, cmd_groups_extra

	cmd_groups = cmd_groups_dfl.copy()
	cmd_groups.update(cmd_groups_extra)

	@staticmethod
	def create_cmd_group(cls, sg_name=None):

		cmd_group_in = dict(cls.cmd_group_in)

		if sg_name and 'subgroup.' + sg_name not in cmd_group_in:
			die(1, f'{sg_name!r}: no such subgroup in test group {cls.__name__}')

		def add_entries(key, add_deps=True, added_subgroups=[]):

			if add_deps:
				for dep in cmd_group_in['subgroup.'+key]:
					yield from add_entries(dep)

			assert isinstance(cls.cmd_subgroups[key][0], str), f'header for subgroup {key!r} missing!'

			if not key in added_subgroups:
				yield from cls.cmd_subgroups[key][1:]
				added_subgroups.append(key)

		def gen():
			for name, data in cls.cmd_group_in:
				if name.startswith('subgroup.'):
					sg_key = name.removeprefix('subgroup.')
					if sg_name in (None, sg_key):
						yield from add_entries(
								sg_key,
								add_deps = sg_name and not cfg.skipping_deps,
								added_subgroups = [sg_name] if cfg.deps_only else [])
					if cfg.deps_only and sg_key == sg_name:
						return
				elif not cfg.skipping_deps:
					yield (name, data)

		return tuple(gen())

	def load_mod(self, gname, modname=None):
		clsname, kwargs = self.cmd_groups[gname]
		if modname is None and 'modname' in kwargs:
			modname = kwargs['modname']
		import importlib
		modpath = f'test.cmdtest_d.ct_{modname or gname}'
		return getattr(importlib.import_module(modpath), clsname)

	def create_group(self, gname, sg_name, full_data=False, modname=None, is3seed=False, add_dpy=False):
		"""
		Initializes the list 'cmd_list' and dict 'dpy_data' from module's cmd_group data.
		Alternatively, if called with 'add_dpy=True', updates 'dpy_data' from module data
		without touching 'cmd_list'
		"""

		cls = self.load_mod(gname, modname)
		cdata = []

		def get_shared_deps(cmdname, tmpdir_idx):
			"""
			shared_deps are "implied" dependencies for all cmds in cmd_group that don't appear in
			the cmd_group data or cmds' argument lists.  Supported only for 3seed tests at present.
			"""
			if not hasattr(cls, 'shared_deps'):
				return []

			return [k for k, v in cfgs[str(tmpdir_idx)]['dep_generators'].items()
						if k in cls.shared_deps and v != cmdname]

		if not hasattr(cls, 'cmd_group'):
			cls.cmd_group = self.create_cmd_group(cls, sg_name)

		for a, b in cls.cmd_group:
			if is3seed:
				for n, (i, j) in enumerate(zip(cls.tmpdir_nums, (128, 192, 256))):
					k = f'{a}_{n+1}'
					if hasattr(cls, 'skip_cmds') and k in cls.skip_cmds:
						continue
					sdeps = get_shared_deps(k, i)
					if isinstance(b, str):
						cdata.append((k, (i, f'{b} ({j}-bit)', [[[]+sdeps, i]])))
					else:
						cdata.append((k, (i, f'{b[1]} ({j}-bit)', [[b[0]+sdeps, i]])))
			else:
				cdata.append((a, b if full_data else (cls.tmpdir_nums[0], b, [[[], cls.tmpdir_nums[0]]])))

		if add_dpy:
			self.dpy_data.update(dict(cdata))
		else:
			self.cmd_list = tuple(e[0] for e in cdata)
			self.dpy_data = dict(cdata)

		return cls

	def gm_init_group(self, trunner, gname, sg_name, spawn_prog):
		kwargs = self.cmd_groups[gname][1]
		cls = self.create_group(gname, sg_name, **kwargs)
		cls.group_name = gname
		return cls(trunner, cfgs, spawn_prog)

	def get_cls_by_gname(self, gname):
		return self.load_mod(gname, self.cmd_groups[gname][1].get('modname'))

	def list_cmd_groups(self):
		ginfo = []
		for gname in self.cmd_groups:
			ginfo.append((gname, self.get_cls_by_gname(gname)))

		if cfg.list_current_cmd_groups:
			exclude = (cfg.exclude_groups or '').split(',')
			ginfo = [g for g in ginfo
						if network_id in g[1].networks
							and not g[0] in exclude
							and g[0] in tuple(self.cmd_groups_dfl) + tuple(cmd_args)]
			desc = 'CONFIGURED'
		else:
			desc = 'AVAILABLE'

		def gen_output():
			yield green(f'{desc} COMMAND GROUPS AND SUBGROUPS:')
			yield ''
			for name, cls in ginfo:
				yield '  {} - {}'.format(
					yellow(name.ljust(13)),
					(cls.__doc__.strip() if cls.__doc__ else cls.__name__))
				if hasattr(cls, 'cmd_subgroups'):
					subgroups = {k:v for k, v in cls.cmd_subgroups.items() if not k.startswith('_')}
					max_w = max(len(k) for k in subgroups)
					for k, v in subgroups.items():
						yield '    + {} · {}'.format(cyan(k.ljust(max_w+1)), v[0])

		from mmgen.ui import do_pager
		do_pager('\n'.join(gen_output()))

		Msg('\n' + ' '.join(e[0] for e in ginfo))
		sys.exit(0)

	def find_cmd_in_groups(self, cmd, group=None):
		"""
		Search for a test command in specified group or all configured command groups
		and return it as a string.  Loads modules but alters no global variables.
		"""
		if group:
			if not group in [e[0] for e in self.cmd_groups]:
				die(1, f'{group!r}: unrecognized group')
			groups = [self.cmd_groups[group]]
		else:
			groups = self.cmd_groups

		for gname in groups:
			cls = self.get_cls_by_gname(gname)

			if not hasattr(cls, 'cmd_group'):
				cls.cmd_group = self.create_cmd_group(cls)

			if cmd in cls.cmd_group:             # first search the class
				return gname

			if cmd in dir(cls(None, None, None)):  # then a throwaway instance
				return gname # cmd might exist in more than one group - we'll go with the first

		return None

class CmdTestRunner:
	'cmdtest.py test runner'

	def __del__(self):
		if logging:
			self.log_fd.close()

	def __init__(self, data_dir, trash_dir):

		self.data_dir = data_dir
		self.trash_dir = trash_dir
		self.cmd_total = 0
		self.rebuild_list = {}
		self.gm = CmdGroupMgr()
		self.repo_root = repo_root
		self.skipped_warnings = []
		self.resume_cmd = None
		self.deps_only = None

		if logging:
			self.log_fd = open(cmdtest_py_log_fn, 'a')
			self.log_fd.write(f'\nLog started: {make_timestr()} UTC\n')
			omsg(f'INFO → Logging to file {cmdtest_py_log_fn!r}')
		else:
			self.log_fd = None

		if cfg.coverage:
			coverdir, accfile = init_coverage()
			omsg(f'INFO → Writing coverage files to {coverdir!r}')
			self.pre_args = ['python3', '-m', 'trace', '--count', '--coverdir='+coverdir, '--file='+accfile]
		else:
			self.pre_args = ['python3'] if sys.platform == 'win32' else []

		if cfg.pexpect_spawn:
			omsg('INFO → Using pexpect.spawn() for real terminal emulation')

		self.set_spawn_env()

	def set_spawn_env(self):

		self.spawn_env = dict(os.environ)
		self.spawn_env.update({
			'MMGEN_NO_LICENSE': '1',
			'MMGEN_BOGUS_SEND': '1',
			'MMGEN_TEST_SUITE_PEXPECT': '1',
			'EXEC_WRAPPER_DO_RUNTIME_MSG':'1',
			# if cmdtest.py itself is running under exec_wrapper, disable writing of traceback file for spawned script
			'EXEC_WRAPPER_TRACEBACK': '' if os.getenv('MMGEN_EXEC_WRAPPER') else '1',
		})

		if cfg.exact_output:
			from mmgen.term import get_terminal_size
			self.spawn_env['MMGEN_COLUMNS'] = str(get_terminal_size().width)
		else:
			self.spawn_env['MMGEN_COLUMNS'] = '120'

	def spawn_wrapper(
			self,
			cmd,
			args            = [],
			extra_desc      = '',
			no_output       = False,
			msg_only        = False,
			no_msg          = False,
			cmd_dir         = 'cmds',
			no_exec_wrapper = False,
			timeout         = None,
			pexpect_spawn   = None,
			direct_exec     = False,
			no_passthru_opts = False,
			spawn_env_override = None,
			exit_val        = None,
			env             = {}):

		self.exit_val = exit_val

		desc = self.tg.test_name if cfg.names else self.gm.dpy_data[self.tg.test_name][1]
		if extra_desc:
			desc += ' ' + extra_desc

		cmd_path = (
			cmd if cfg.system # cfg.system is broken for main test group with overlay tree
			else os.path.relpath(os.path.join(repo_root, cmd_dir, cmd)))

		args = (
			self.pre_args +
			([] if no_exec_wrapper else ['scripts/exec_wrapper.py']) +
			[cmd_path] +
			([] if no_passthru_opts else self.passthru_opts) +
			args)

		try:
			qargs = ['{q}{}{q}'.format(a, q = "'" if ' ' in a else '') for a in args]
		except:
			msg(f'args: {args}')
			raise

		cmd_disp = ' '.join(qargs).replace('\\', '/') # for mingw

		if logging:
			self.log_fd.write('[{}][{}:{}] {}\n'.format(
				proto.coin.lower(),
				self.tg.group_name,
				self.tg.test_name,
				cmd_disp))

		for i in args: # die only after writing log entry
			if not isinstance(i, str):
				die(2, 'Error: missing input files in cmd line?:\nName: {}\nCmdline: {!r}'.format(
					self.tg.test_name,
					args))

		if not no_msg:
			t_pfx = '' if cfg.no_timings else f'[{time.time() - self.start_time:08.2f}] '
			if cfg.verbose or cfg.print_cmdline or cfg.exact_output:
				omsg(green(f'{t_pfx}Testing: {desc}'))
				if not msg_only:
					clr1, clr2 = (nocolor, nocolor) if cfg.print_cmdline else (green, cyan)
					omsg(
						clr1('Executing: ') +
						clr2(repr(cmd_disp) if sys.platform == 'win32' else cmd_disp)
					)
			else:
				omsg_r('{a}Testing {b}: {c}'.format(
					a = t_pfx,
					b = desc,
					c = 'OK\n' if direct_exec or cfg.direct_exec else ''))

		if msg_only:
			return

		# NB: the `pexpect_spawn` arg enables hold_protect and send_delay while the corresponding cmdline
		# option does not.  For performance reasons, this is the desired behavior.  For full emulation of
		# the user experience with hold protect enabled, specify --buf-keypress or --demo.
		send_delay = 0.4 if pexpect_spawn is True or cfg.buf_keypress else None
		pexpect_spawn = pexpect_spawn if pexpect_spawn is not None else bool(cfg.pexpect_spawn)

		spawn_env = dict(spawn_env_override or self.tg.spawn_env)
		spawn_env.update({
			'MMGEN_HOLD_PROTECT_DISABLE': '' if send_delay else '1',
			'MMGEN_TEST_SUITE_POPEN_SPAWN': '' if pexpect_spawn else '1',
			'EXEC_WRAPPER_EXIT_VAL': '' if exit_val is None else str(exit_val),
		})
		spawn_env.update(env)

		from test.include.pexpect import MMGenPexpect
		return MMGenPexpect(
			args          = args,
			no_output     = no_output,
			spawn_env     = spawn_env,
			pexpect_spawn = pexpect_spawn,
			timeout       = timeout,
			send_delay    = send_delay,
			direct_exec   = direct_exec)

	def end_msg(self):
		t = int(time.time() - self.start_time)
		sys.stderr.write(green(
			f'{self.cmd_total} test{suf(self.cmd_total)} performed' +
			('\n' if cfg.no_timings else f'.  Elapsed time: {t//60:02d}:{t%60:02d}\n')
		))

	def init_group(self, gname, sg_name=None, cmd=None, quiet=False, do_clean=True):

		from test.cmdtest_d.cfg import cmd_groups_altcoin
		if cfg.no_altcoin and gname in cmd_groups_altcoin:
			omsg(gray(f'INFO → skipping test group {gname!r} (--no-altcoin)'))
			return None

		ct_cls = CmdGroupMgr().load_mod(gname)

		if sys.platform in ct_cls.platform_skip:
			omsg(gray(f'INFO → skipping test {gname!r} for platform {sys.platform!r}'))
			return None

		for k in ('segwit', 'segwit_random', 'bech32'):
			if getattr(cfg, k):
				segwit_opt = k
				break
		else:
			segwit_opt = None

		def gen_msg():
			yield ('{g}:{c}' if cmd else 'test group {g!r}').format(g=gname, c=cmd)
			if len(ct_cls.networks) != 1:
				yield f' for {proto.coin} {proto.network}'
			if segwit_opt:
				yield ' (--{})'.format(segwit_opt.replace('_', '-'))

		m = ''.join(gen_msg())

		if segwit_opt and not ct_cls.segwit_opts_ok:
			iqmsg(gray(f'INFO → skipping {m}'))
			return None

		# 'networks = ()' means all networks allowed
		nws = [(e.split('_')[0], 'testnet') if '_' in e else (e, 'mainnet') for e in ct_cls.networks]
		if nws:
			coin = proto.coin.lower()
			for a, b in nws:
				if a == coin and b == proto.network:
					break
			else:
				iqmsg(gray(f'INFO → skipping {m} for {proto.coin} {proto.network}'))
				return None

		if do_clean and not cfg.skipping_deps:
			clean(cfgs, tmpdir_ids=ct_cls.tmpdir_nums, extra_dirs=[data_dir, trash_dir, trash_dir2])

		if not quiet:
			bmsg('Executing ' + m)

		if (not self.daemon_started) and self.gm.get_cls_by_gname(gname).need_daemon:
			start_test_daemons(network_id, remove_datadir=True)
			self.daemon_started = True

		if hasattr(self, 'tg'):
			del self.tg

		self.tg = self.gm.gm_init_group(self, gname, sg_name, self.spawn_wrapper)
		self.ct_clsname = type(self.tg).__name__

		# pass through opts from cmdline (po.user_opts)
		self.passthru_opts = ['--{}{}'.format(
				k.replace('_', '-'),
				'' if cfg._uopts[k] is True else '=' + cfg._uopts[k]
			) for k in cfg._uopts if k in self.tg.base_passthru_opts + self.tg.passthru_opts]

		if cfg.resuming:
			rc = cfg.resume or cfg.resume_after
			offset = 1 if cfg.resume_after else 0
			self.resume_cmd = self.gm.cmd_list[self.gm.cmd_list.index(rc)+offset]
			omsg(f'INFO → Resuming at command {self.resume_cmd!r}')
			if cfg.step:
				cfg.exit_after = self.resume_cmd

		if cfg.exit_after and cfg.exit_after not in self.gm.cmd_list:
			die(1, f'{cfg.exit_after!r}: command not recognized')

		return self.tg

	def run_tests(self, cmd_args):
		self.start_time = time.time()
		self.daemon_started = False
		gname_save = None

		def parse_arg(arg):
			if '.' in arg:
				a, b = arg.split('.')
				return [a] + b.split(':') if ':' in b else [a, b, None]
			elif ':' in arg:
				a, b = arg.split(':')
				return [a, None, b]
			else:
				return [self.gm.find_cmd_in_groups(arg), None, arg]

		if cmd_args:
			for arg in cmd_args:
				if arg in self.gm.cmd_groups:
					if self.init_group(arg):
						for cmd in self.gm.cmd_list:
							self.check_needs_rerun(cmd, build=True)
							do_between()
				else:
					gname, sg_name, cmdname = parse_arg(arg)
					if gname:
						same_grp = gname == gname_save # same group as previous cmd: don't clean, suppress blue msg
						if self.init_group(gname, sg_name, cmdname, quiet=same_grp, do_clean=not same_grp):
							if cmdname:
								if cfg.deps_only:
									self.deps_only = cmdname
								try:
									self.check_needs_rerun(cmdname, build=True)
								except Exception as e: # allow calling of functions not in cmd_group
									if isinstance(e, KeyError) and e.args[0] == cmdname:
										ret = getattr(self.tg, cmdname)()
										if type(ret).__name__ == 'coroutine':
											asyncio.run(ret)
									else:
										raise
								do_between()
							else:
								for cmd in self.gm.cmd_list:
									self.check_needs_rerun(cmd, build=True)
									do_between()
							gname_save = gname
					else:
						die(1, f'{arg!r}: command not recognized')
		else:
			if cfg.exclude_groups:
				exclude = cfg.exclude_groups.split(',')
				for e in exclude:
					if e not in self.gm.cmd_groups_dfl:
						die(1, f'{e!r}: group not recognized')
			for gname in self.gm.cmd_groups_dfl:
				if cfg.exclude_groups and gname in exclude:
					continue
				if self.init_group(gname):
					for cmd in self.gm.cmd_list:
						self.check_needs_rerun(cmd, build=True)
						do_between()

		self.end_msg()

	def check_needs_rerun(
			self,
			cmd,
			build        = False,
			root         = True,
			force_delete = False,
			dpy          = False):

		self.tg.test_name = cmd

		if self.ct_clsname == 'CmdTestMain' and testing_segwit and cmd not in self.tg.segwit_do:
			return False

		rerun = root # force_delete is not passed to recursive call

		fns = []
		if force_delete or not root:
			# does cmd produce a needed dependency(ies)?
			ret = self.get_num_exts_for_cmd(cmd)
			if ret:
				for ext in ret[1]:
					fn = get_file_with_ext(cfgs[ret[0]]['tmpdir'], ext, delete=build)
					if fn:
						if force_delete:
							os.unlink(fn)
						else: fns.append(fn)
					else: rerun = True

		fdeps = self.generate_file_deps(cmd)
		cdeps = self.generate_cmd_deps(fdeps)

		for fn in fns:
			my_age = os.stat(fn).st_mtime
			for num, ext in fdeps:
				f = get_file_with_ext(cfgs[num]['tmpdir'], ext, delete=build)
				if f and os.stat(f).st_mtime > my_age:
					rerun = True

		for cdep in cdeps:
			if self.check_needs_rerun(cdep, build=build, root=False, dpy=cmd):
				rerun = True

		if build:
			if rerun:
				for fn in fns:
					if not root:
						os.unlink(fn)
				if not (dpy and cfg.skipping_deps):
					self.run_test(cmd)
				if not root:
					do_between()
		else:
			# If prog produces multiple files:
			if cmd not in self.rebuild_list or rerun is True:
				self.rebuild_list[cmd] = (rerun, fns[0] if fns else '') # FIX

		return rerun

	def run_test(self, cmd):

		if self.deps_only and cmd == self.deps_only:
			sys.exit(0)

		d = [(str(num), ext) for exts, num in self.gm.dpy_data[cmd][2] for ext in exts]

		# delete files depended on by this cmd
		arg_list = [get_file_with_ext(cfgs[num]['tmpdir'], ext) for num, ext in d]

		# remove shared_deps from arg list
		if hasattr(self.tg, 'shared_deps'):
			arg_list = arg_list[:-len(self.tg.shared_deps)]

		if self.resume_cmd:
			if cmd != self.resume_cmd:
				return
			bmsg(f'Resuming at {self.resume_cmd!r}')
			self.resume_cmd = None
			cfg.skipping_deps = False
			cfg.resuming = False

		if cfg.profile:
			start = time.time()

		self.tg.test_name = cmd # NB: Do not remove, this needs to be set twice
		cdata = self.gm.dpy_data[cmd]
#		self.tg.test_dpydata = cdata
		self.tg.tmpdir_num = cdata[0]
#		self.tg.cfg = cfgs[str(cdata[0])] # will remove this eventually
		test_cfg = cfgs[str(cdata[0])]
		for k in (
				'seed_len', 'seed_id', 'wpasswd', 'kapasswd', 'segwit', 'hash_preset', 'bw_filename',
				'bw_params', 'ref_bw_seed_id', 'addr_idx_list', 'pass_idx_list'):
			if k in test_cfg:
				setattr(self.tg, k, test_cfg[k])

		ret = getattr(self.tg, cmd)(*arg_list) # run the test
		if type(ret).__name__ == 'coroutine':
			ret = asyncio.run(ret)
		self.process_retval(cmd, ret)

		if cfg.profile:
			omsg('\r\033[50C{:.4f}'.format(time.time() - start))

		if cmd == cfg.exit_after:
			sys.exit(0)

	def warn_skipped(self):
		if self.skipped_warnings:
			print(yellow('The following tests were skipped and may require attention:'))
			r = '-' * 72 + '\n'
			print(r+('\n'+r).join(self.skipped_warnings))

	def process_retval(self, cmd, ret):
		if type(ret).__name__ == 'MMGenPexpect':
			ret.ok(exit_val=self.exit_val)
			self.cmd_total += 1
		elif ret == 'ok':
			ok()
			self.cmd_total += 1
		elif ret == 'error':
			die(2, red(f'\nTest {self.tg.test_name!r} failed'))
		elif ret in ('skip', 'skip_msg', 'silent'):
			if ret == 'silent':
				self.cmd_total += 1
			elif ret == 'skip_msg':
				ok('SKIP')
		elif isinstance(ret, tuple) and ret[0] == 'skip_warn':
			self.skipped_warnings.append(
				'Test {!r} was skipped:\n  {}'.format(cmd, '\n  '.join(ret[1].split('\n'))))
		else:
			die(2, f'{cmd!r} returned {ret}')

	def check_deps(self, cmds): # TODO: broken
		if len(cmds) != 1:
			die(1, f'Usage: {gc.prog_name} check_deps <command>')

		cmd = cmds[0]

		if cmd not in self.gm.cmd_list:
			die(1, f'{cmd!r}: unrecognized command')

		if not cfg.quiet:
			omsg(f'Checking dependencies for {cmd!r}')

		self.check_needs_rerun(self.tg, cmd)

		w = max(map(len, self.rebuild_list)) + 1
		for cmd in self.rebuild_list:
			c = self.rebuild_list[cmd]
			m = 'Rebuild' if (c[0] and c[1]) else 'Build' if c[0] else 'OK'
			omsg('cmd {:<{w}} {}'.format(cmd+':', m, w=w))

	def generate_file_deps(self, cmd):
		return [(str(n), e) for exts, n in self.gm.dpy_data[cmd][2] for e in exts]

	def generate_cmd_deps(self, fdeps):
		return [cfgs[str(n)]['dep_generators'][ext] for n, ext in fdeps]

	def get_num_exts_for_cmd(self, cmd):
		try:
			num = str(self.gm.dpy_data[cmd][0])
		except KeyError:
			qmsg_r(f'Missing dependency {cmd!r}')
			gname = self.gm.find_cmd_in_groups(cmd)
			if gname:
				kwargs = self.gm.cmd_groups[gname][1]
				kwargs.update({'add_dpy':True})
				self.gm.create_group(gname, None, **kwargs)
				num = str(self.gm.dpy_data[cmd][0])
				qmsg(f' found in group {gname!r}')
			else:
				qmsg(' not found in any command group!')
				raise
		dgl = cfgs[num]['dep_generators']
		if cmd in dgl.values():
			exts = [k for k in dgl if dgl[k] == cmd]
			return (num, exts)
		else:
			return None

if __name__ == '__main__':

	if not cfg.skipping_deps: # do this before list cmds exit, so we stay in sync with shm_dir
		create_tmp_dirs(shm_dir)

	if cfg.list_cmd_groups:
		CmdGroupMgr().list_cmd_groups()
	elif cfg.list_cmds:
		list_cmds()

	if cfg.pause:
		set_restore_term_at_exit()

	from mmgen.exception import TestSuiteSpawnedScriptException

	try:
		tr = CmdTestRunner(data_dir, trash_dir)
		tr.run_tests(cmd_args)
		tr.warn_skipped()
		if tr.daemon_started and not cfg.no_daemon_stop:
			stop_test_daemons(network_id, remove_datadir=True)
		if hasattr(tr, 'tg'):
			del tr.tg
		del tr
	except KeyboardInterrupt:
		if tr.daemon_started and not cfg.no_daemon_stop:
			stop_test_daemons(network_id, remove_datadir=True)
		tr.warn_skipped()
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
		# if cmdtest.py itself is running under exec_wrapper, re-raise so exec_wrapper can handle exception:
		if os.getenv('MMGEN_EXEC_WRAPPER') or not os.getenv('MMGEN_IGNORE_TEST_PY_EXCEPTION'):
			raise
		die(1, red('Test script exited with error'))
