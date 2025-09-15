#!/usr/bin/env python3

"""
test.daemontest_d.exec: unit test for the MMGen suite's Daemon class
"""

from subprocess import run, PIPE
from collections import namedtuple

from mmgen.color import orange, red
from mmgen.util import fmt_list, in_nix_environment
from mmgen.daemon import CoinDaemon

from ..include.common import cfg, qmsg, qmsg_r, vmsg, msg, msg_r

def test_flags(coin):
	d = CoinDaemon(cfg, network_id=coin)
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
			d = CoinDaemon(cfg, network_id=coin, opts=opts, flags=flags)
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
	altcoin_deps = ('flags_eth',)

	def _pre(self):
		self.daemon_ctrl_args = ['btc', 'btc_tn', 'btc_rt'] if cfg.no_altcoin_deps else ['all']

	def _test_cmd(self, args_in, network_ids=[], ok=True):
		args = (
			['python3', f'test/{args_in[0]}-coin-daemons.py']
			+ list(args_in[1:])
			+ (network_ids or self.daemon_ctrl_args))
		vmsg('\n' + orange(f"Running '{' '.join(args)}':"))
		redir = None if cfg.verbose else PIPE
		cp = run(args, stdout=redir, stderr=redir, text=True)
		if cp.returncode != 0:
			if cp.stdout:
				msg(cp.stdout)
			if cp.stderr:
				msg(red(cp.stderr))
			return False
		if ok:
			vmsg('')
			qmsg('OK')
		return True

	def flags(self, name, ut):
		qmsg_r('Testing flags and opts (BTC)...')
		vmsg('')
		daemons = test_flags(coin='btc')
		qmsg('OK')
		qmsg_r('Testing error handling for flags and opts...')
		vmsg('')
		test_flags_err(ut, daemons)
		qmsg('OK')
		return True

	def flags_eth(self, name, ut):
		qmsg_r('Testing flags and opts (ETH)...')
		vmsg('')
		daemons = test_flags(coin='eth')
		qmsg('OK')
		qmsg_r('Testing error handling for flags and opts...')
		vmsg('')
		test_flags_err(ut, daemons)
		qmsg('OK')
		return True

	def avail(self, name, ut):
		qmsg_r('Testing availability of coin daemons...')
		from platform import machine
		test_reth = not (cfg.no_altcoin_deps or cfg.fast)
		test_parity = not (
			cfg.no_altcoin_deps
			or machine() in ('riscv64', 'aarch64', 'armv7l')
			or in_nix_environment())
		ret1 = self._test_cmd(
			['start', '--print-version', '--mainnet-only'],
			network_ids = ['btc'] if cfg.no_altcoin_deps else ['btc', 'ltc', 'bch', 'xmr', 'eth'],
			ok = not (test_reth or test_parity))
		ret2 = self._test_cmd(
			['start', '--print-version', '--mainnet-only', '--daemon-id=reth'],
			network_ids = ['eth'],
			ok = not test_parity) if test_reth else True
		ret3 = self._test_cmd(
			['start', '--print-version', '--mainnet-only'],
			network_ids = ['etc'],
			ok = True) if test_parity else True
		return ret1 and ret2 and ret3

	def versions(self, name, ut):
		qmsg_r('Displaying coin daemon versions...')
		ret1 = self._test_cmd(['start', '--print-version'], ok=False)
		ret2 = self._test_cmd(['start', '--print-version', '--mainnet-only'])
		return ret1 and ret2

	def cmds(self, name, ut):
		qmsg_r('Testing start commands for coin daemons...')
		return self._test_cmd(['start', '--testing'])

	def start(self, name, ut):
		qmsg_r('Starting coin daemons...')
		return self._test_cmd(['start'])

	def status(self, name, ut):
		qmsg_r('Checking status of coin daemons...')
		return self._test_cmd(['start'])

	def stop(self, name, ut):
		qmsg_r('Stopping coin daemons...')
		return self._test_cmd(['stop', '--remove-datadir'])
