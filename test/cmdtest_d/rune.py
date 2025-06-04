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
test.cmdtest_d.rune: THORChain RUNE tests for the cmdtest.py test suite
"""

from .include.common import dfl_sid
from .httpd.thornode.rpc import ThornodeRPCServer
from .ethdev import CmdTestEthdevMethods
from .base import CmdTestBase
from .shared import CmdTestShared
from .swap import CmdTestSwapMethods

class CmdTestRune(CmdTestEthdevMethods, CmdTestBase, CmdTestShared):
	'THORChain RUNE tracking wallet and transacting operations'
	networks = ('rune',)
	passthru_opts = ('coin', 'http_timeout')
	tmpdir_nums = [50]
	color = True
	menu_prompt = 'efresh balance:\b'

	cmd_group_in = (
		('subgroup.init',     []),
		('subgroup.main',     ['init']),
	)
	cmd_subgroups = {
		'init': (
			'initializing wallets',
			('addrgen',    'generating addresses'),
			('addrimport', 'importing addresses'),
		),
		'main': (
			'tracking wallet and transaction operations',
			('twview',        'viewing unspent outputs in tracking wallet'),
			('bal_refresh',   'refreshing address balance in tracking wallet'),
			('thornode_server_stop', 'stopping Thornode server'),
		),
	}

	def __init__(self, cfg, trunner, cfgs, spawn):
		CmdTestBase.__init__(self, cfg, trunner, cfgs, spawn)
		if trunner is None:
			return

		self.eth_opts = [f'--outdir={self.tmpdir}', '--regtest=1', '--quiet']
		self.eth_opts_noquiet = [f'--outdir={self.tmpdir}', '--regtest=1']

		self.rune_opts = self.eth_opts

		from mmgen.protocol import init_proto
		self.proto = init_proto(cfg, network_id=self.proto.coin + '_rt', need_amt=True)
		self.spawn_env['MMGEN_BOGUS_SEND'] = ''

		self.thornode_server = ThornodeRPCServer()
		self.thornode_server.start()

	def addrgen(self):
		return self._addrgen()

	def addrimport(self):
		return self._addrimport()

	def twview(self):
		return self.spawn('mmgen-tool', self.rune_opts + ['twview'])

	def bal_refresh(self):
		t = self.spawn('mmgen-tool', self.rune_opts + ['listaddresses', 'interactive=1'])
		t.expect(self.menu_prompt, 'R')
		t.expect('menu): ', '3\n')
		t.expect('(y/N): ', 'y')
		t.expect(r'Total RUNE: \S*\D9876.54321321\D', regex=True)
		t.expect('address #3 refreshed')
		t.expect(self.menu_prompt, 'q')
		return t

	def thornode_server_stop(self):
		return CmdTestSwapMethods._thornode_server_stop(
			self, attrname='thornode_server', name='thornode server')
