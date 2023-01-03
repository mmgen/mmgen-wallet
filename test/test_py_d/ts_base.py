#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
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
test.test_py_d.ts_base: Base class for the test.py test suite
"""

import os
from mmgen.globalvars import g
from mmgen.opts import opt
from ..include.common import *
from .common import *

class TestSuiteBase(object):
	'initializer class for the test.py test suite'
	base_passthru_opts = ('data_dir','skip_cfg_file')
	passthru_opts = ()
	extra_spawn_args = []
	networks = ()
	segwit_opts_ok = False
	color = False
	need_daemon = False

	def __init__(self,trunner,cfgs,spawn):
		from mmgen.protocol import init_proto_from_opts
		self.proto = init_proto_from_opts(need_amt=True)
		self.tr = trunner
		self.cfgs = cfgs
		self.spawn = spawn
		self.have_dfl_wallet = False
		self.usr_rand_chars = (5,30)[bool(opt.usr_random)]
		self.usr_rand_arg = f'-r{self.usr_rand_chars}'
		self.altcoin_pfx = '' if self.proto.base_coin == 'BTC' else '-'+self.proto.base_coin
		self.tn_ext = ('','.testnet')[self.proto.testnet]
		d = {'bch':'btc','btc':'btc','ltc':'ltc'}
		self.fork = d[self.proto.coin.lower()] if self.proto.coin.lower() in d else None
		if len(self.tmpdir_nums) == 1:
			self.tmpdir_num = self.tmpdir_nums[0]

	@property
	def tmpdir(self):
		return os.path.join('test','tmp','{}{}'.format(self.tmpdir_num,'-α' if g.debug_utf8 else ''))

	@property
	def segwit_mmtype(self):
		return ('segwit','bech32')[bool(opt.bech32)] if self.segwit else None

	@property
	def segwit_arg(self):
		return ['--type=' + self.segwit_mmtype] if self.segwit_mmtype else []

	def get_file_with_ext(self,ext,**kwargs):
		return get_file_with_ext(self.tmpdir,ext,**kwargs)

	def read_from_tmpfile(self,fn,binary=False):
		return read_from_file(os.path.join(self.tmpdir,fn),binary=binary)

	def write_to_tmpfile(self,fn,data,binary=False):
		return write_to_file(os.path.join(self.tmpdir,fn),data,binary=binary)

	def skip_for_win(self):
		if g.platform == 'win':
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
