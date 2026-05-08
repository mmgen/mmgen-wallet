#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
autosign.swap_mgr: swap management for MMGen Wallet autosigning
"""

import sys
from subprocess import run, PIPE, DEVNULL

from ..util import msg, ymsg, suf, fmt_list, have_sudo, capfirst
from ..color import orange, blue

def SwapMgr(*args, **kwargs):
	match sys.platform:
		case 'linux':
			return SwapMgrLinux(*args, **kwargs)
		case 'darwin':
			return SwapMgrMacOS(*args, **kwargs)

class SwapMgrBase:

	def __init__(self, cfg, *, ignore_zram=False):
		self.cfg = cfg
		self.ignore_zram = ignore_zram
		self.desc = 'disk swap' if ignore_zram else 'swap'

	def enable(self, *, quiet=False):
		ret = self.do_enable()
		if not quiet:
			self.cfg._util.qmsg(
				f'{capfirst(self.desc)} successfully enabled' if ret else
				f'{capfirst(self.desc)} is already enabled' if ret is None else
				f'Could not enable {self.desc}')
		return ret

	def disable(self, *, quiet=False):
		self.cfg._util.qmsg_r(f'Attempting to disable {self.desc}...')
		ret = self.do_disable()
		self.cfg._util.qmsg('success')
		if not quiet:
			self.cfg._util.qmsg(
				f'{capfirst(self.desc)} successfully disabled ({fmt_list(ret, fmt="no_quotes")})'
					if ret and isinstance(ret, list) else
				f'{capfirst(self.desc)} successfully disabled' if ret else
				f'No active {self.desc}')
		return ret

	def process_cmds(self, op, cmds):
		if not cmds:
			return
		if have_sudo(silent=True) and not self.cfg.test_suite:
			for cmd in cmds:
				run(cmd.split(), check=True)
		else:
			pre = 'failure\n' if op == 'disable' else ''
			fs = blue('{a} {b} manually by executing the following command{c}:\n{d}')
			post = orange('[To prevent this message in the future, enable sudo without a password]')
			m = pre + fs.format(
				a = 'Please disable' if op == 'disable' else 'Enable',
				b = self.desc,
				c = suf(cmds),
				d = fmt_list(cmds, indent='  ', fmt='col')) + '\n' + post
			msg(m)
			if not self.cfg.test_suite:
				sys.exit(1)

class SwapMgrLinux(SwapMgrBase):

	def get_active(self):
		for cmd in ('/sbin/swapon', 'swapon'):
			try:
				cp = run([cmd, '--show=NAME', '--noheadings'], stdout=PIPE, text=True, check=True)
				break
			except Exception:
				if cmd == 'swapon':
					raise
		res = cp.stdout.splitlines()
		return [e for e in res if not e.startswith('/dev/zram')] if self.ignore_zram else res

	def do_enable(self):
		if ret := self.get_active():
			ymsg(f'Warning: {self.desc} is already enabled: ({fmt_list(ret, fmt="no_quotes")})')
		self.process_cmds('enable', ['sudo swapon --all'])
		return True

	def do_disable(self):
		swapdevs = self.get_active()
		if not swapdevs:
			return None
		self.process_cmds('disable', [f'sudo swapoff {swapdev}' for swapdev in swapdevs])
		return swapdevs

class SwapMgrMacOS(SwapMgrBase):

	def get_active(self):
		cmd = 'launchctl print system/com.apple.dynamic_pager'
		return run(cmd.split(), stdout=DEVNULL, stderr=DEVNULL).returncode == 0

	def _do_action(self, active, op, cmd):
		if self.get_active() is active:
			return None
		else:
			cmd = f'sudo launchctl {cmd} -w /System/Library/LaunchDaemons/com.apple.dynamic_pager.plist'
			self.process_cmds(op, [cmd])
			return True

	def do_enable(self):
		return self._do_action(active=True, op='enable', cmd='load')

	def do_disable(self):
		return self._do_action(active=False, op='disable', cmd='unload')
