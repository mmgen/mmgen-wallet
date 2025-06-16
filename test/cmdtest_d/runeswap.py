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
test.cmdtest_d.runeswap: THORChain swap tests for the cmdtest.py test suite
"""

from .httpd.thornode.swap import ThornodeSwapServer
from .include.proxy import TestProxy

from .regtest import CmdTestRegtest
from .swap import CmdTestSwapMethods, create_cross_methods
from .rune import CmdTestRune

class CmdTestRuneSwap(CmdTestSwapMethods, CmdTestRegtest):
	'RUNE swap operations'

	bdb_wallet = True
	tmpdir_nums = [57]
	networks = ('btc',)
	passthru_opts = ('coin', 'rpc_backend')
	cross_group = 'runeswap_rune'
	cross_coin = 'rune'

	cmd_group_in = (
		('setup',                'regtest (Bob and Alice) mode setup'),
		('subgroup.init',        []),
		('subgroup.rune_init',   ['init']),
		('subgroup.rune_swap',   ['rune_init']),
		('stop',                 'stopping the regtest daemon'),
		('swap_server_stop',     'stopping the Thornode swap server'),
		('rune_rpc_server_stop', 'stopping the Thornode RPC server'),
	)
	cmd_subgroups = {
		'init': (
			'creating Bob’s MMGen wallet and tracking wallet',
			('walletconv_bob', 'wallet creation (Bob)'),
			('addrgen_bob',    'address generation (Bob)'),
			('addrimport_bob', 'importing Bob’s addresses'),
		),
		'rune_init': (
			'initializing the RUNE tracking wallet',
			('rune_addrgen',     ''),
			('rune_addrimport',  ''),
			('rune_bal_refresh', ''),
			('rune_twview',      ''),
		),
		'rune_swap': (
			'swap operations (RUNE -> BTC)',
			('rune_swaptxcreate1',  ''),
			('rune_swaptxsign1',    ''),
			('rune_swaptxsend1',    ''),
			('rune_swaptxstatus1',  ''),
			('rune_swaptxreceipt1', ''),
		),
	}

	exec(create_cross_methods(cross_coin, cross_group, cmd_group_in, cmd_subgroups))

	def __init__(self, cfg, trunner, cfgs, spawn):

		super().__init__(cfg, trunner, cfgs, spawn)

		if not trunner:
			return

		globals()[self.cross_group] = self.create_cross_runner(trunner)

		self.swap_server = ThornodeSwapServer()
		self.swap_server.start()

		TestProxy(cfg)

	def swap_server_stop(self):
		return self._thornode_server_stop()

class CmdTestRuneSwapRune(CmdTestSwapMethods, CmdTestRune):
	'RUNE swap operations - RUNE wallet'

	networks = ('rune',)
	tmpdir_nums = [58]
	input_sels_prompt = 'to spend from: '
	is_helper = True

	cmd_group_in = CmdTestRune.cmd_group_in + (
		# rune_swap:
		('swaptxcreate1',            'creating a RUNE->BTC swap transaction'),
		('swaptxsign1',              'signing the transaction'),
		('swaptxsend1',              'sending the transaction'),
		('swaptxstatus1',            'getting the transaction status'),
		('swaptxreceipt1',           'getting the transaction receipt'),
		('thornode_server_stop',     'stopping Thornode server'),
	)

	def swaptxcreate1(self):
		t = self._swaptxcreate(['RUNE', '8.765', 'BTC'])
		t.expect('OK? (Y/n): ', 'y')
		return self._swaptxcreate_ui_common(t, inputs='3')

	def swaptxsign1(self):
		return self._swaptxsign()

	def swaptxsend1(self):
		return self._swaptxsend(add_opts=[f'--proxy=localhost:{TestProxy.port}'])

	def swaptxstatus1(self):
		return self._swaptxsend(add_opts=['--verbose', '--status'], status=True)

	def swaptxreceipt1(self):
		return self._swaptxsend(add_opts=['--receipt'], spawn_only=True)
