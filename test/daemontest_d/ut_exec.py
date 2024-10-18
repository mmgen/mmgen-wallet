#!/usr/bin/env python3

"""
test.daemontest_d.ut_exec: unit test for the MMGen suite's Daemon class
"""

from subprocess import run, PIPE
from collections import namedtuple

from mmgen.color import orange, red
from mmgen.util import fmt_list
from mmgen.daemon import CoinDaemon

from ..include.common import cfg, qmsg, qmsg_r, vmsg, msg

def test_flags():
	d = CoinDaemon(cfg, 'eth')
	vmsg(f'Available opts:  {fmt_list(d.avail_opts, fmt="bare")}')
	vmsg(f'Available flags: {fmt_list(d.avail_flags, fmt="bare")}')
	vals = namedtuple('vals', ['online', 'no_daemonize', 'keep_cfg_file'])

	def gen():
		for opts, flags, val in (
				(None,                       None,              vals(False, False, False)),
				(None,                       ['keep_cfg_file'], vals(False, False, True)),
				(['online'],                 ['keep_cfg_file'], vals(True, False, True)),
				(['online', 'no_daemonize'], ['keep_cfg_file'], vals(True, True, True)),
			):
			d = CoinDaemon(cfg, 'eth', opts=opts, flags=flags)
			assert d.flag.keep_cfg_file == val.keep_cfg_file
			assert d.opt.online == val.online
			assert d.opt.no_daemonize == val.no_daemonize
			d.flag.keep_cfg_file = not val.keep_cfg_file
			d.flag.keep_cfg_file = val.keep_cfg_file
			yield d

	return tuple(gen())

def test_flags_err(ut, d):

	def bad1(): d[0].flag.foo = False
	def bad2(): d[0].opt.foo = False
	def bad3(): d[0].opt.no_daemonize = True
	def bad4(): d[0].flag.keep_cfg_file = 'x'
	def bad5(): d[0].opt.no_daemonize = 'x'
	def bad6(): d[0].flag.keep_cfg_file = False
	def bad7(): d[1].flag.keep_cfg_file = True

	ut.process_bad_data((
		('flag (1)', 'ClassFlagsError', 'unrecognized flag', bad1),
		('opt  (1)', 'ClassFlagsError', 'unrecognized opt',  bad2),
		('opt  (2)', 'AttributeError',  'is read-only',      bad3),
		('flag (2)', 'AssertionError',  'not boolean',       bad4),
		('opt  (3)', 'AttributeError',  'is read-only',      bad5),
		('flag (3)', 'ClassFlagsError', 'not set',           bad6),
		('flag (4)', 'ClassFlagsError', 'already set',       bad7),
	))

class unit_tests:

	win_skip = ('start', 'status', 'stop')

	def _pre(self):
		self.daemon_ctrl_args = ['btc', 'btc_tn', 'btc_rt'] if cfg.no_altcoin_deps else ['all']

	def _test_cmd(self, args_in, message):
		qmsg_r(message)
		args = ['python3', f'test/{args_in[0]}-coin-daemons.py'] + list(args_in[1:]) + self.daemon_ctrl_args
		vmsg('\n' + orange(f"Running '{' '.join(args)}':"))
		cp = run(args, stdout=PIPE, stderr=PIPE, text=True)
		if cp.returncode != 0:
			if cp.stdout:
				msg(cp.stdout)
			if cp.stderr:
				msg(red(cp.stderr))
			return False
		qmsg('OK')
		return True

	def flags(self, name, ut):

		qmsg_r('Testing flags and opts...')
		vmsg('')
		daemons = test_flags()
		qmsg('OK')

		qmsg_r('Testing error handling for flags and opts...')
		vmsg('')
		test_flags_err(ut, daemons)
		qmsg('OK')

		return True

	def avail(self, name, ut):
		return self._test_cmd(['start', '-Vm'], 'Testing availability of coin daemons...')

	def cmds(self, name, ut):
		return self._test_cmd(['start', '-t'], 'Testing start commands for coin daemons...')

	def start(self, name, ut):
		return self._test_cmd(['start'], 'Starting coin daemons...')

	def status(self, name, ut):
		return self._test_cmd(['start'], 'Checking status of coin daemons...')

	def stop(self, name, ut):
		return self._test_cmd(['stop'], 'Stopping coin daemons...')
