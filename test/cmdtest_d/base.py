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
test.cmdtest_d.base: Base class for the cmdtest.py test suite
"""

import sys, os

from mmgen.util import msg
from mmgen.color import gray, purple, yellow

from ..include.common import write_to_file, read_from_file, imsg
from .include.common import get_file_with_ext

class CmdTestBase:
	'initializer class for the cmdtest.py test suite'
	base_passthru_opts = ('data_dir', 'skip_cfg_file')
	passthru_opts = ()
	networks = ()
	segwit_opts_ok = False
	color = False
	need_daemon = False
	platform_skip = ()
	tmpdir_nums = []
	skip_cmds = ()
	test_name = None
	is_helper = False
	extra_daemons = []

	def __init__(self, cfg, trunner, cfgs, spawn):
		if hasattr(self, 'name'): # init may called multiple times
			return
		self.name = type(self).__name__
		self.cfg = cfg
		self.proto = cfg._proto
		self.tr = trunner
		self.cfgs = cfgs
		self.spawn = spawn
		self.have_dfl_wallet = False
		self.usr_rand_chars = (5, 30)[bool(cfg.usr_random)]
		self.usr_rand_arg = f'-r{self.usr_rand_chars}'
		self.tn_ext = ('', '.testnet')[self.proto.testnet]
		self.coin = self.proto.coin.lower()
		self.fork = 'btc' if self.coin == 'bch' and not cfg.cashaddr else self.coin
		self.altcoin_pfx = '' if self.fork == 'btc' else f'-{self.proto.coin}'
		self.testnet_opt = ['--testnet=1'] if cfg.testnet else []
		if len(self.tmpdir_nums) == 1:
			self.tmpdir_num = self.tmpdir_nums[0]
		if self.tr:
			self.spawn_env = dict(self.tr.spawn_env)
			self.spawn_env['MMGEN_TEST_SUITE_ENABLE_COLOR'] = '1' if self.color else ''
		else:
			self.spawn_env = {} # placeholder

	def get_altcoin_pfx(self, coin, cashaddr=True):
		coin = coin.lower()
		fork = 'btc' if coin == 'bch' and not cashaddr else coin
		return '' if fork == 'btc' else f'-{coin.upper()}'

	@property
	def tmpdir(self):
		return os.path.join('test', 'tmp', '{}{}'.format(self.tmpdir_num, '-α' if self.cfg.debug_utf8 else ''))

	def get_file_with_ext(self, ext, **kwargs):
		return get_file_with_ext(self.tmpdir, ext, **kwargs)

	def read_from_tmpfile(self, fn, binary=False, subdir=None):
		tdir = os.path.join(self.tmpdir, subdir) if subdir else self.tmpdir
		return read_from_file(os.path.join(tdir, fn), binary=binary)

	def write_to_tmpfile(self, fn, data, binary=False):
		return write_to_file(os.path.join(self.tmpdir, fn), data, binary=binary)

	def delete_tmpfile(self, fn):
		fn = os.path.join(self.tmpdir, fn)
		try:
			return os.unlink(fn)
		except:
			msg(f'{fn}: file does not exist or could not be deleted')

	def skip_for_platform(self, name, extra_msg=None):
		if sys.platform == name:
			msg(gray('Skipping test {!r} for {} platform{}'.format(
				self.test_name,
				name,
				f' ({extra_msg})' if extra_msg else "")))
			return True
		else:
			return False

	def skip_for_mac(self, extra_msg=None):
		return self.skip_for_platform('darwin', extra_msg)

	def skip_for_win(self, extra_msg=None):
		return self.skip_for_platform('win32', extra_msg)

	def spawn_chk(self, *args, **kwargs):
		"""
		Drop-in replacement for spawn() + t.read() for tests that spawn more than one process.
		Ensures that test script execution stops when a spawned process fails.

		"""
		t = self.spawn(*args, **kwargs)
		t.read()
		t.ok()
		t.skip_ok = True
		return t

	def noop(self):
		return 'ok'

	def _cashaddr_opt(self, val):
		return [f'--cashaddr={val}'] if self.proto.coin == 'BCH' else []

	def _kill_process_from_pid_file(self, fn, desc):
		self.spawn(msg_only=True)
		pid = int(self.read_from_tmpfile(fn))
		self.delete_tmpfile(fn)
		from signal import SIGTERM
		imsg(purple(f'Killing {desc} [PID {pid}]'))
		try:
			os.kill(pid, SIGTERM)
		except:
			imsg(yellow(f'{pid}: no such process'))
		return 'ok'
