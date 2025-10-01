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
test.cmdtest_d.automount_eth: Ethereum automount autosigning tests for the cmdtest.py test suite
"""
import os, re

from .autosign import CmdTestAutosignThreaded
from .ethdev import CmdTestEthdev, CmdTestEthdevMethods
from .include.common import dfl_words_file
from ..include.common import cfg, joinpath

class CmdTestAutosignETH(CmdTestAutosignThreaded, CmdTestEthdev, CmdTestEthdevMethods):
	'automounted transacting operations for Ethereum via ethdev'

	networks = ('eth', 'etc')
	tmpdir_nums = [59]

	cmd_group = (
		('setup',                  f'dev mode tests for coin {cfg.coin} (start daemon)'),
		('addrgen',                'generating addresses'),
		('addrimport',             'importing addresses'),
		('addrimport_devaddr',     'importing the dev address'),
		('addrimport_reth_devaddr','importing the reth dev address'),
		('fund_devaddr',           'funding the dev address'),
		('del_reth_devaddr',       'deleting the reth dev address'),
		('fund_mmgen_addr',        'funding an MMGen address'),
		('create_tx',              'creating a transaction'),
		('run_autosign_setup',     'running ‘autosign setup’'),
		('wait_loop_start',        'starting autosign wait loop'),
		('send_tx',                'sending the transaction'),
		('token_compile1',         'compiling ERC20 token #1'),
		('token_deploy1a',         'deploying ERC20 token #1 (SafeMath)'),
		('token_deploy1b',         'deploying ERC20 token #1 (Owned)'),
		('token_deploy1c',         'deploying ERC20 token #1 (Token)'),
		('tx_status2',             'getting the transaction status'),
		('token_fund_user',        'transferring token funds from dev to user'),
		('token_addrgen',          'generating token addresses'),
		('token_addrimport',       'importing token addresses using token address (MM1)'),
		('token_bal1',             f'the {cfg.coin} balance and token balance'),
		('create_token_tx',        'creating a token transaction'),
		('send_token_tx',          'sending a token transaction'),
		('token_bal2',             f'the {cfg.coin} balance and token balance'),
		('wait_loop_kill',         'stopping autosign wait loop'),
		('stop',                   'stopping daemon'),
		('txview',                 'viewing transactions'),
	)

	def __init__(self, cfg, trunner, cfgs, spawn):

		self.coins = [cfg.coin.lower()]

		CmdTestAutosignThreaded.__init__(self, cfg, trunner, cfgs, spawn)
		CmdTestEthdev.__init__(self, cfg, trunner, cfgs, spawn)

		self.txop_opts = ['--autosign', '--regtest=1', '--quiet']

	def fund_mmgen_addr(self):
		return self._fund_mmgen_addr(arg='98831F3A:E:1,123.456')

	def create_tx(self):
		self.mining_delay()
		self.insert_device_online()
		t = self._create_tx(fee='50G', args=['98831F3A:E:11,54.321'], add_opts=self.txop_opts)
		t.read()
		self.remove_device_online()
		return t

	def run_autosign_setup(self):
		return self.run_setup(mn_type='bip39', mn_file='test/ref/98831F3A.bip39', use_dfl_wallet=None)

	def send_tx(self):
		self._wait_signed('transaction')
		self.insert_device_online()
		t = self._send_tx(desc='automount transaction', add_opts=self.txop_opts)
		t.read()
		self.remove_device_online()
		return t

	def token_addrgen(self):
		return self._token_addrgen(mm_idxs=[11], naddrs=3)

	def token_addrimport(self):
		return self._token_addrimport('token_addr1', '11-13', expect='3/3')

	async def token_fund_user(self):
		return await self._token_transfer_ops(op='fund_user', mm_idxs=[11])

	def token_bal1(self):
		return self._token_bal_check(pat=r':E:11\s+1000\s+54\.321\s+')

	def token_bal2(self):
		return self._token_bal_check(pat=r':E:11\s+998.76544\s+54.318\d+\s+.*:E:12\s+1\.23456\s+')

	def create_token_tx(self):
		self.insert_device_online()
		t = self._create_token_tx(
			cmd = 'txcreate',
			fee = '50G',
			args = ['98831F3A:E:12,1.23456'],
			add_opts = self.txop_opts)
		t.read()
		self.remove_device_online()
		return t

	send_token_tx = send_tx
