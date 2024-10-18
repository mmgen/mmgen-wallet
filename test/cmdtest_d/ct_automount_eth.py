#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.cmdtest_d.ct_automount_eth: Ethereum automount autosigning tests for the cmdtest.py test suite
"""
import os, re

from .ct_autosign import CmdTestAutosignThreaded
from .ct_ethdev import CmdTestEthdev, parity_devkey_fn
from .common import dfl_words_file
from ..include.common import cfg

class CmdTestAutosignETH(CmdTestAutosignThreaded, CmdTestEthdev):
	'automounted transacting operations for Ethereum via ethdev'

	networks = ('eth', 'etc')
	tmpdir_nums = [59]

	cmd_group = (
		('setup',                  f'dev mode tests for coin {cfg.coin} (start daemon)'),
		('addrgen',                'generating addresses'),
		('addrimport',             'importing addresses'),
		('addrimport_dev_addr',    "importing dev faucet address 'Ox00a329c..'"),
		('fund_dev_address',       'funding the default (Parity dev) address'),
		('fund_mmgen_address',     'funding an MMGen address'),
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
		('token_addrgen_addr1',    'generating token addresses'),
		('token_addrimport_addr1', 'importing token addresses using token address (MM1)'),
		('token_bal1',             f'the {cfg.coin} balance and token balance'),
		('create_token_tx',        'creating a token transaction'),
		('send_token_tx',          'sending a token transaction'),
		('token_bal2',             f'the {cfg.coin} balance and token balance'),
		('wait_loop_kill',         'stopping autosign wait loop'),
		('stop',                   'stopping daemon'),
		('txview',                 'viewing transactions'),
	)

	def __init__(self, trunner, cfgs, spawn):

		self.coins = [cfg.coin.lower()]

		CmdTestAutosignThreaded.__init__(self, trunner, cfgs, spawn)
		CmdTestEthdev.__init__(self, trunner, cfgs, spawn)

		self.txop_opts = ['--autosign', '--regtest=1', '--quiet']

	def fund_mmgen_address(self):
		keyfile = os.path.join(self.tmpdir, parity_devkey_fn)
		t = self.spawn(
			'mmgen-txdo',
			self.eth_args
			+ [f'--keys-from-file={keyfile}']
			+ ['--fee=40G', '98831F3A:E:1,123.456', dfl_words_file],
		)
		t.expect('efresh balance:\b', 'q')
		t.expect('from: ', '10')
		t.expect('(Y/n): ', 'y')
		t.expect('(Y/n): ', 'y')
		t.expect('(y/N): ', 'n')
		t.expect('view: ', 'n')
		t.expect('confirm: ', 'YES')
		return t

	def create_tx(self):
		self.insert_device_online()
		t = self.spawn('mmgen-txcreate', self.txop_opts + ['-B', '98831F3A:E:11,54.321'])
		t = self.txcreate_ui_common(
			t,
			caller            = 'txcreate',
			input_sels_prompt = 'to spend from',
			inputs            = '1',
			file_desc         = 'transaction',
			interactive_fee   = '50G',
			fee_desc          = 'transaction fee or gas price')
		t.read()
		self.remove_device_online()
		return t

	def run_autosign_setup(self):
		return self.run_setup(mn_type='bip39', mn_file='test/ref/98831F3A.bip39', use_dfl_wallet=None)

	def send_tx(self, add_args=[]):
		self._wait_signed('transaction')
		self.insert_device_online()
		t = self.spawn('mmgen-txsend', self.txop_opts + add_args)
		t.view_tx('t')
		t.expect('(y/N): ', 'n')
		self._do_confirm_send(t, quiet=True)
		t.written_to_file('Sent automount transaction')
		t.read()
		self.remove_device_online()
		return t

	def token_fund_user(self):
		return self.token_transfer_ops(op='do_transfer', num_tokens=1)

	def token_addrgen_addr1(self):
		return self.token_addrgen(num_tokens=1)

	def token_bal1(self):
		return self.token_bal(pat=r':E:11\s+1000\s+54\.321\s+')

	def token_bal2(self):
		return self.token_bal(pat=r':E:11\s+998.76544\s+54.318\d+\s+.*:E:12\s+1\.23456\s+')

	def token_bal(self, pat):
		t = self.spawn('mmgen-tool', ['--regtest=1', '--token=mm1', 'twview', 'wide=1'])
		text = t.read(strip_color=True)
		assert re.search(pat, text, re.DOTALL), f'output failed to match regex {pat}'
		return t

	def create_token_tx(self):
		self.insert_device_online()
		t = self.txcreate_ui_common(
			self.spawn(
				'mmgen-txcreate',
				self.txop_opts + ['--token=MM1', '-B', '--fee=50G', '98831F3A:E:12,1.23456']),
			inputs            = '1',
			input_sels_prompt = 'to spend from',
			file_desc         = 'Unsigned automount transaction')
		t.read()
		self.remove_device_online()
		return t

	def send_token_tx(self):
		return self.send_tx(add_args=['--token=MM1'])
