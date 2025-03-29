#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.cmdtest_d.include.runner: test runner for the MMGen Wallet cmdtest suite
"""

import sys, os, time, asyncio

from mmgen.cfg import gc
from mmgen.color import red, yellow, green, blue, cyan, gray, nocolor
from mmgen.util import msg, Msg, rmsg, bmsg, die, suf, make_timestr

from ...include.common import (
	cmdtest_py_log_fn,
	iqmsg,
	omsg,
	omsg_r,
	ok,
	start_test_daemons,
	init_coverage,
	clean
)

from .common import get_file_with_ext, confirm_continue
from .cfg import cfgs, cmd_groups_dfl
from .group_mgr import CmdGroupMgr

def format_args(args):
	try:
		return ' '.join((f"'{a}'" if ' ' in a else a) for a in args).replace('\\', '/') # for MSYS2
	except Exception as e:
		print(type(e), e)
		print('cmdline:', args)

class CmdTestRunner:
	'cmdtest.py test runner'

	def __del__(self):
		if self.logging:
			self.log_fd.close()

	def __init__(self, cfg, repo_root, data_dir, trash_dir, trash_dir2):

		self.cfg = cfg
		self.proto = cfg._proto
		self.data_dir = data_dir
		self.trash_dir = trash_dir
		self.trash_dir2 = trash_dir2
		self.cmd_total = 0
		self.rebuild_list = {}
		self.gm = CmdGroupMgr(cfg)
		self.repo_root = repo_root
		self.skipped_warnings = []
		self.resume_cmd = None
		self.deps_only = None
		self.logging = self.cfg.log or os.getenv('MMGEN_EXEC_WRAPPER')
		self.testing_segwit = cfg.segwit or cfg.segwit_random or cfg.bech32
		self.network_id = self.proto.coin.lower() + ('_tn' if self.proto.testnet else '')
		self.daemon_started = False

		global qmsg, qmsg_r
		if cfg.exact_output:
			qmsg = qmsg_r = lambda s: None
		else:
			qmsg = cfg._util.qmsg
			qmsg_r = cfg._util.qmsg_r

		if self.logging:
			self.log_fd = open(cmdtest_py_log_fn, 'a')
			self.log_fd.write(f'\nLog started: {make_timestr()} UTC\n')
			omsg(f'INFO → Logging to file {cmdtest_py_log_fn!r}')
		else:
			self.log_fd = None

		if self.cfg.coverage:
			coverdir, accfile = init_coverage()
			omsg(f'INFO → Writing coverage files to {coverdir!r}')
			self.pre_args = ['python3', '-m', 'trace', '--count', '--coverdir='+coverdir, '--file='+accfile]
		else:
			self.pre_args = ['python3'] if sys.platform == 'win32' else []

		if self.cfg.pexpect_spawn:
			omsg('INFO → Using pexpect.spawn() for real terminal emulation')

		self.set_spawn_env()
		self.start_time = time.time()

	def do_between(self):
		if self.cfg.pause:
			confirm_continue()
		elif (self.cfg.verbose or self.cfg.exact_output) and not self.cfg.skipping_deps:
			sys.stderr.write('\n')

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

		if self.cfg.exact_output:
			from mmgen.term import get_terminal_size
			self.spawn_env['MMGEN_COLUMNS'] = str(get_terminal_size().width)
		else:
			self.spawn_env['MMGEN_COLUMNS'] = '120'

	def spawn_wrapper(
			self,
			cmd             = '',
			args            = [],
			extra_desc      = '',
			no_output       = False,
			msg_only        = False,
			log_only        = False,
			no_msg          = False,
			cmd_dir         = 'cmds',
			no_exec_wrapper = False,
			timeout         = None,
			pexpect_spawn   = None,
			direct_exec     = False,
			no_passthru_opts = False,
			spawn_env_override = None,
			exit_val        = None,
			silent          = False,
			env             = {}):

		self.exit_val = exit_val

		desc = self.tg.test_name if self.cfg.names else self.gm.dpy_data[self.tg.test_name][1]
		if extra_desc:
			desc += ' ' + extra_desc

		cmd_path = (
			cmd if self.cfg.system # self.cfg.system is broken for main test group with overlay tree
			else os.path.relpath(os.path.join(self.repo_root, cmd_dir, cmd)))

		passthru_opts = (
			self.passthru_opts if not no_passthru_opts else
			[] if no_passthru_opts is True else
			[o for o in self.passthru_opts
				if o[2:].split('=')[0].replace('-','_') not in no_passthru_opts])

		args = (
			self.pre_args +
			([] if no_exec_wrapper else ['scripts/exec_wrapper.py']) +
			[cmd_path] +
			passthru_opts +
			args)

		cmd_disp = format_args(args)

		if self.logging:
			self.log_fd.write('[{}][{}:{}] {}\n'.format(
				(self.proto.coin.lower() if 'coin' in self.tg.passthru_opts else 'NONE'),
				self.tg.group_name,
				self.tg.test_name,
				cmd_disp))

		if log_only:
			return

		for i in args: # die only after writing log entry
			if not isinstance(i, str):
				die(2, 'Error: missing input files in cmd line?:\nName: {}\nCmdline: {!r}'.format(
					self.tg.test_name,
					args))

		if not no_msg:
			t_pfx = '' if self.cfg.no_timings else f'[{time.time() - self.start_time:08.2f}] '
			if self.cfg.verbose or self.cfg.print_cmdline or self.cfg.exact_output:
				omsg(green(f'{t_pfx}Testing: {desc}'))
				if not msg_only:
					clr1, clr2 = (nocolor, nocolor) if self.cfg.print_cmdline else (green, cyan)
					omsg(
						clr1('Executing: ') +
						clr2(repr(cmd_disp) if sys.platform == 'win32' else cmd_disp)
					)
			else:
				omsg_r('{a}Testing {b}: {c}'.format(
					a = t_pfx,
					b = desc,
					c = 'OK\n' if direct_exec or self.cfg.direct_exec else ''))

		if msg_only:
			return

		# NB: the `pexpect_spawn` arg enables hold_protect and send_delay while the corresponding cmdline
		# option does not.  For performance reasons, this is the desired behavior.  For full emulation of
		# the user experience with hold protect enabled, specify --buf-keypress or --demo.
		send_delay = 0.4 if pexpect_spawn is True or self.cfg.buf_keypress else None
		pexpect_spawn = pexpect_spawn if pexpect_spawn is not None else bool(self.cfg.pexpect_spawn)

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
			silent        = silent,
			direct_exec   = direct_exec)

	def end_msg(self):
		t = int(time.time() - self.start_time)
		sys.stderr.write(green(
			f'{self.cmd_total} test{suf(self.cmd_total)} performed' +
			('\n' if self.cfg.no_timings else f'.  Elapsed time: {t//60:02d}:{t%60:02d}\n')
		))

	def init_group(self, gname, sg_name=None, cmd=None, quiet=False, do_clean=True):

		from .cfg import cmd_groups_altcoin
		if self.cfg.no_altcoin and gname in cmd_groups_altcoin:
			omsg(gray(f'INFO → skipping test group {gname!r} (--no-altcoin)'))
			return None

		ct_cls = self.gm.load_mod(gname)

		if sys.platform in ct_cls.platform_skip:
			omsg(gray(f'INFO → skipping test {gname!r} for platform {sys.platform!r}'))
			return None

		for k in ('segwit', 'segwit_random', 'bech32'):
			if getattr(self.cfg, k):
				segwit_opt = k
				break
		else:
			segwit_opt = None

		def gen_msg():
			yield ('{g}:{c}' if cmd else 'test group {g!r}').format(g=gname, c=cmd)
			if len(ct_cls.networks) != 1:
				yield f' for {self.proto.coin} {self.proto.network}'
			if segwit_opt:
				yield ' (--{})'.format(segwit_opt.replace('_', '-'))

		m = ''.join(gen_msg())

		if segwit_opt and not ct_cls.segwit_opts_ok:
			iqmsg(gray(f'INFO → skipping {m}'))
			return None

		# 'networks = ()' means all networks allowed
		nws = [(e.split('_')[0], 'testnet') if '_' in e else (e, 'mainnet') for e in ct_cls.networks]
		if nws:
			coin = self.proto.coin.lower()
			for a, b in nws:
				if a == coin and b == self.proto.network:
					break
			else:
				iqmsg(gray(f'INFO → skipping {m} for {self.proto.coin} {self.proto.network}'))
				return None

		if do_clean and not self.cfg.skipping_deps:
			clean(
				cfgs,
				tmpdir_ids = ct_cls.tmpdir_nums,
				extra_dirs = [self.data_dir, self.trash_dir, self.trash_dir2])

		if not quiet:
			bmsg('Executing ' + m)

		if (not self.daemon_started) and self.gm.get_cls_by_gname(gname).need_daemon:
			start_test_daemons(self.network_id, remove_datadir=True)
			self.daemon_started = True

		if hasattr(self, 'tg'):
			del self.tg

		self.tg = self.gm.gm_init_group(self.cfg, self, gname, sg_name, self.spawn_wrapper)
		self.ct_clsname = type(self.tg).__name__

		# pass through opts from cmdline (po.user_opts)
		self.passthru_opts = ['--{}{}'.format(
				k.replace('_', '-'),
				'' if self.cfg._uopts[k] is True else '=' + self.cfg._uopts[k]
			) for k in self.cfg._uopts
				if self.cfg._uopts[k] and k in self.tg.base_passthru_opts + self.tg.passthru_opts]

		if self.cfg.resuming:
			rc = self.cfg.resume or self.cfg.resume_after
			offset = 1 if self.cfg.resume_after else 0
			self.resume_cmd = self.gm.cmd_list[self.gm.cmd_list.index(rc)+offset]
			omsg(f'INFO → Resuming at command {self.resume_cmd!r}')
			if self.cfg.step:
				self.cfg.exit_after = self.resume_cmd

		if self.cfg.exit_after and self.cfg.exit_after not in self.gm.cmd_list:
			die(1, f'{self.cfg.exit_after!r}: command not recognized')

		return self.tg

	def run_tests(self, cmd_args):
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
							self.do_between()
				else:
					gname, sg_name, cmdname = parse_arg(arg)
					if gname:
						same_grp = gname == gname_save # same group as previous cmd: don't clean, suppress blue msg
						if self.init_group(gname, sg_name, cmdname, quiet=same_grp, do_clean=not same_grp):
							if cmdname:
								if self.cfg.deps_only:
									self.deps_only = cmdname
								try:
									self.check_needs_rerun(cmdname, build=True)
								except Exception as e: # allow calling of functions not in cmd_group
									if isinstance(e, KeyError) and e.args[0] == cmdname:
										ret = getattr(self.tg, cmdname)()
										if type(ret).__name__ == 'coroutine':
											ret = asyncio.run(ret)
										self.process_retval(cmdname, ret)
									else:
										raise
								self.do_between()
							else:
								for cmd in self.gm.cmd_list:
									self.check_needs_rerun(cmd, build=True)
									self.do_between()
							gname_save = gname
					else:
						die(1, f'{arg!r}: command not recognized')
		else:
			if self.cfg.exclude_groups:
				exclude = self.cfg.exclude_groups.split(',')
				for e in exclude:
					if e not in cmd_groups_dfl:
						die(1, f'{e!r}: group not recognized')
			for gname in cmd_groups_dfl:
				if self.cfg.exclude_groups and gname in exclude:
					continue
				if self.init_group(gname):
					for cmd in self.gm.cmd_list:
						self.check_needs_rerun(cmd, build=True)
						self.do_between()

		self.end_msg()

	def check_needs_rerun(
			self,
			cmd,
			build        = False,
			root         = True,
			force_delete = False,
			dpy          = False):

		self.tg.test_name = cmd

		if self.ct_clsname == 'CmdTestMain' and self.testing_segwit and cmd not in self.tg.segwit_do:
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
				if not (dpy and self.cfg.skipping_deps):
					self.run_test(cmd)
				if not root:
					self.do_between()
		else:
			# If prog produces multiple files:
			if cmd not in self.rebuild_list or rerun is True:
				self.rebuild_list[cmd] = (rerun, fns[0] if fns else '') # FIX

		return rerun

	def run_test(self, cmd, sub=False):

		if self.deps_only and cmd == self.deps_only:
			sys.exit(0)

		if self.tg.full_data:
			d = [(str(num), ext) for exts, num in self.gm.dpy_data[cmd][2] for ext in exts]
			# delete files depended on by this cmd
			arg_list = [get_file_with_ext(cfgs[num]['tmpdir'], ext) for num, ext in d]

			# remove shared_deps from arg list
			if hasattr(self.tg, 'shared_deps'):
				arg_list = arg_list[:-len(self.tg.shared_deps)]
		else:
			arg_list = []

		if self.resume_cmd:
			if cmd != self.resume_cmd:
				return
			bmsg(f'Resuming at {self.resume_cmd!r}')
			self.resume_cmd = None
			self.cfg.skipping_deps = False
			self.cfg.resuming = False

		if self.cfg.profile:
			start = time.time()

		self.tg.test_name = cmd # NB: Do not remove, this needs to be set twice

		if self.tg.full_data:
			tmpdir_num = self.gm.dpy_data[cmd][0]
			self.tg.tmpdir_num = tmpdir_num
			for k in (test_cfg := cfgs[str(tmpdir_num)]):
				if k in self.gm.cfg_attrs:
					setattr(self.tg, k, test_cfg[k])

		ret = getattr(self.tg, cmd)(*arg_list) # run the test
		if sub:
			return ret

		if type(ret).__name__ == 'coroutine':
			ret = asyncio.run(ret)

		self.process_retval(cmd, ret)

		if self.cfg.profile:
			omsg('\r\033[50C{:.4f}'.format(time.time() - start))

		if cmd == self.cfg.exit_after:
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
		elif ret in ('skip', 'skip_msg', 'silent'):
			if ret == 'silent':
				self.cmd_total += 1
			elif ret == 'skip_msg':
				ok('SKIP')
		elif ret == 'error':
			die(2, red(f'\nTest {self.tg.test_name!r} failed'))
		elif isinstance(ret, tuple) and ret[0] == 'skip_warn':
			self.skipped_warnings.append(
				'Test {!r} was skipped:\n  {}'.format(cmd, '\n  '.join(ret[1].split('\n'))))
		else:
			die(2, f'{cmd!r} returned {ret}')

	def check_deps(self, cmds): # TODO: broken, unused
		if len(cmds) != 1:
			die(1, f'Usage: {gc.prog_name} check_deps <command>')

		cmd = cmds[0]

		if cmd not in self.gm.cmd_list:
			die(1, f'{cmd!r}: unrecognized command')

		if not self.cfg.quiet:
			omsg(f'Checking dependencies for {cmd!r}')

		self.check_needs_rerun(cmd)

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
