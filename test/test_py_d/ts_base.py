#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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
ts_base.py: Base class for the test.py test suite
"""

import os
from mmgen.globalvars import g
from mmgen.opts import opt
from ..include.common import *
from .common import *

class TestSuiteBase(object):
	'initializer class for the test.py test suite'
	base_passthru_opts = ('data_dir',)
	passthru_opts = ()
	extra_spawn_args = []
	networks = ()
	segwit_opts_ok = False

	def __init__(self,trunner,cfgs,spawn):
		self.tr = trunner
		self.cfgs = cfgs
		self.spawn = spawn
		self.have_dfl_wallet = False
		self.usr_rand_chars = (5,30)[bool(opt.usr_random)]
		self.usr_rand_arg = '-r{}'.format(self.usr_rand_chars)
		self.altcoin_pfx = '' if g.proto.base_coin == 'BTC' else '-'+g.proto.base_coin
		self.tn_ext = ('','.testnet')[g.proto.testnet]
		d = {'bch':'btc','btc':'btc','ltc':'ltc'}
		self.fork = d[g.coin.lower()] if g.coin.lower() in d else None

	@property
	def tmpdir(self):
		return os.path.join('test','tmp{}{}'.format(self.tmpdir_num,'-α' if g.debug_utf8 else ''))

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
			msg("Skipping test '{}': not supported on MSys2 platform".format(self.test_name))
			return True
		else:
			return False
