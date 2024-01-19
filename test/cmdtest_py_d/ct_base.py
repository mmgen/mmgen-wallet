#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
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
test.cmdtest_py_d.ct_base: Base class for the cmdtest.py test suite
"""

import sys,os

from mmgen.util import msg

from ..include.common import cfg,write_to_file,read_from_file
from .common import get_file_with_ext

class CmdTestBase:
	'initializer class for the cmdtest.py test suite'
	base_passthru_opts = ('data_dir','skip_cfg_file')
	passthru_opts = ()
	extra_spawn_args = []
	networks = ()
	segwit_opts_ok = False
	color = False
	need_daemon = False
	win_skip = False
	tmpdir_nums = []

	def __init__(self,trunner,cfgs,spawn):
		if hasattr(self,'name'): # init will be called multiple times for classes with multiple inheritance
			return
		self.name = type(self).__name__
		self.proto = cfg._proto
		self.tr = trunner
		self.cfgs = cfgs
		self.spawn = spawn
		self.have_dfl_wallet = False
		self.usr_rand_chars = (5,30)[bool(cfg.usr_random)]
		self.usr_rand_arg = f'-r{self.usr_rand_chars}'
		self.altcoin_pfx = '' if self.proto.base_coin == 'BTC' else '-'+self.proto.base_coin
		self.tn_ext = ('','.testnet')[self.proto.testnet]
		d = {'bch':'btc','btc':'btc','ltc':'ltc'}
		self.fork = d[self.proto.coin.lower()] if self.proto.coin.lower() in d else None
		if len(self.tmpdir_nums) == 1:
			self.tmpdir_num = self.tmpdir_nums[0]
		if self.tr:
			self.spawn_env = dict(self.tr.spawn_env)
			self.spawn_env['MMGEN_TEST_SUITE_ENABLE_COLOR'] = '1' if self.color else ''
		else:
			self.spawn_env = {} # placeholder

	@property
	def tmpdir(self):
		return os.path.join('test','tmp','{}{}'.format(self.tmpdir_num,'-α' if cfg.debug_utf8 else ''))

	def get_file_with_ext(self,ext,**kwargs):
		return get_file_with_ext(self.tmpdir,ext,**kwargs)

	def read_from_tmpfile(self,fn,binary=False):
		return read_from_file(os.path.join(self.tmpdir,fn),binary=binary)

	def write_to_tmpfile(self,fn,data,binary=False):
		return write_to_file(os.path.join(self.tmpdir,fn),data,binary=binary)

	def delete_tmpfile(self,fn):
		fn = os.path.join(self.tmpdir,fn)
		try:
			return os.unlink(fn)
		except:
			msg(f'{fn}: file does not exist or could not be deleted')

	def skip_for_win(self):
		if sys.platform == 'win32':
			msg(f'Skipping test {self.test_name!r}: not supported on MSys2 platform')
			return True
		else:
			return False

	def spawn_chk(self,*args,**kwargs):
		"""
		Drop-in replacement for spawn() + t.read() for tests that spawn more than one process.
		Ensures that test script execution stops when a spawned process fails.

		"""
		t = self.spawn(*args,**kwargs)
		t.read()
		t.ok()
		t.skip_ok = True
		return t
