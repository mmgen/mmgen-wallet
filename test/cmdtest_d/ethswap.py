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
test.cmdtest_d.ethswap: Ethereum swap tests for the cmdtest.py test suite
"""

from mmgen.cfg import Config
from mmgen.protocol import init_proto

from .include.runner import CmdTestRunner
from .include.common import dfl_seed_id
from .httpd.thornode import ThornodeServer

from .regtest import CmdTestRegtest
from .swap import CmdTestSwapMethods
from .ethdev import CmdTestEthdev

thornode_server = ThornodeServer()

method_template = """
def {name}(self):
	self.spawn(log_only=True)
	return ethswap_eth.run_test("{eth_name}", sub=True)
"""

class CmdTestEthSwap(CmdTestRegtest, CmdTestSwapMethods):
	'Ethereum swap operations'

	bdb_wallet = True
	tmpdir_nums = [47]
	networks = ('btc',)
	passthru_opts = ('coin', 'rpc_backend', 'eth_daemon_id')
	eth_group = 'ethswap_eth'

	cmd_group_in = (
		('setup',                'regtest (Bob and Alice) mode setup'),
		('eth_setup',            'Ethereum devnet setup'),
		('subgroup.init',        []),
		('subgroup.fund',        ['init']),
		('subgroup.eth_init',    []),
		('subgroup.eth_fund',    ['eth_init']),
		('subgroup.swap',        ['fund', 'eth_fund']),
		('subgroup.eth_swap',    ['fund', 'eth_fund']),
		('stop',                 'stopping regtest daemon'),
		('eth_stop',             'stopping Ethereum daemon'),
		('thornode_server_stop', 'stopping the Thornode server'),
	)
	cmd_subgroups = {
	'init': (
		'creating Bob’s MMGen wallet and tracking wallet',
		('walletconv_bob', 'wallet creation (Bob)'),
		('addrgen_bob',    'address generation (Bob)'),
		('addrimport_bob', 'importing Bob’s addresses'),
	),
	'fund': (
		'funding Bob’s wallet',
		('bob_import_miner_addr', 'importing miner’s coinbase addr into Bob’s wallet'),
		('fund_bob',              'funding Bob’s wallet'),
		('generate',              'mining a block'),
		('bob_bal1',              'Bob’s balance'),
	),
	'eth_init': (
		'initializing the ETH tracking wallet',
		('eth_addrgen',             ''),
		('eth_addrimport',          ''),
		('eth_addrimport_devaddr',  ''),
		('eth_fund_devaddr',        ''),
	),
	'eth_fund': (
		'funding the ETH tracking wallet',
		('eth_txcreate1', ''),
		('eth_txsign1',   ''),
		('eth_txsend1',   ''),
		('eth_bal1',      ''),
	),
	'swap': (
		'swap operations (BTC -> ETH)',
		('swaptxcreate1', 'creating a BTC->ETH swap transaction'),
		('swaptxcreate2', 'creating a BTC->ETH swap transaction (used account)'),
		('swaptxsign1',   'signing the swap transaction'),
		('swaptxsend1',   'sending the swap transaction'),
		('swaptxbump1',   'bumping the swap transaction'),
		('swaptxsign2',   'signing the bump transaction'),
		('swaptxsend2',   'sending the bump transaction'),
		('generate',      'generating a block'),
		('bob_bal2',      'Bob’s balance'),
		('swaptxdo1',     'creating, signing and sending a swap transaction'),
		('generate',      'generating a block'),
		('bob_bal3',      'Bob’s balance'),
	),
	'eth_swap': (
		'swap operations (ETH -> BTC)',
		('eth_swaptxcreate1', ''),
		('eth_swaptxcreate2', ''),
		('eth_swaptxsign1',   ''),
		('eth_swaptxsend1',   ''),
		('eth_swaptxstatus1', ''),
		('eth_bal2',          ''),
	),
	}

	eth_tests = [c[0] for v in tuple(cmd_subgroups.values()) + (cmd_group_in,)
		for c in v if isinstance(c, tuple) and c[0].startswith('eth_')]

	exec(''.join(method_template.format(name=k, eth_name=k.removeprefix('eth_')) for k in eth_tests))

	def __init__(self, cfg, trunner, cfgs, spawn):

		super().__init__(cfg, trunner, cfgs, spawn)

		if not trunner:
			return

		global ethswap_eth
		cfg = Config({
			'_clone': trunner.cfg,
			'coin': 'eth',
			'eth_daemon_id': trunner.cfg.eth_daemon_id,
			'resume': None,
			'resume_after': None,
			'exit_after': None,
			'log': None})
		t = trunner
		ethswap_eth = CmdTestRunner(cfg, t.repo_root, t.data_dir, t.trash_dir, t.trash_dir2)
		ethswap_eth.init_group(self.eth_group)

		thornode_server.start()

	def swaptxcreate1(self):
		t = self._swaptxcreate(['BTC', '8.765', 'ETH'])
		t.expect('OK? (Y/n): ', 'y')
		t.expect(':E:2')
		t.expect('OK? (Y/n): ', 'y')
		return self._swaptxcreate_ui_common(t)

	def swaptxcreate2(self):
		t = self._swaptxcreate(['BTC', '8.765', 'ETH', f'{dfl_seed_id}:E:1'])
		t.expect('OK? (Y/n): ', 'y')
		return self._swaptxcreate_ui_common(t)

	def swaptxsign1(self):
		return self._swaptxsign()

	def swaptxsign2(self):
		return self._swaptxsign()

	def swaptxsend1(self):
		return self._swaptxsend()

	def swaptxsend2(self):
		return self._swaptxsend()

	def swaptxbump1(self): # create one-output TX back to self to rescue funds
		return self._swaptxbump('40s', output_args=[f'{dfl_seed_id}:B:1'])

	def swaptxdo1(self):
		return self._swaptxcreate_ui_common(
			self._swaptxcreate(
				['BTC', '0.223344', f'{dfl_seed_id}:B:3', 'ETH', f'{dfl_seed_id}:E:2'],
				action = 'txdo'),
			sign_and_send = True,
			file_desc = 'Sent transaction')

	def bob_bal2(self):
		return self._user_bal_cli('bob', chk='499.9999252')

	def bob_bal3(self):
		return self._user_bal_cli('bob', chk='499.77656902')

	def thornode_server_stop(self):
		self.spawn(msg_only=True)
		thornode_server.stop()
		return 'ok'

class CmdTestEthSwapEth(CmdTestEthdev, CmdTestSwapMethods):
	'Ethereum swap operations - Ethereum wallet'

	networks = ('eth',)
	tmpdir_nums = [48]

	bals = lambda self, k: {
		'swap1': [('98831F3A:E:1', '123.456')],
		'swap2': [('98831F3A:E:1', '114.690978056')],
	}[k]

	cmd_group_in = CmdTestEthdev.cmd_group_in + (
		('swaptxcreate1', 'creating an ETH->BTC swap transaction'),
		('swaptxcreate2', 'creating an ETH->BTC swap transaction (specific address, trade limit)'),
		('swaptxsign1',   'signing the transaction'),
		('swaptxsend1',   'sending the transaction'),
		('swaptxstatus1', 'getting the transaction status (with --verbose)'),
		('bal1',          'the ETH balance'),
		('bal2',          'the ETH balance'),
	)

	def swaptxcreate1(self):
		t = self._swaptxcreate(['ETH', '8.765', 'BTC'])
		t.expect('OK? (Y/n): ', 'y')
		return self._swaptxcreate_ui_common(t)

	def swaptxcreate2(self):
		return self._swaptxcreate_ui_common(
			self._swaptxcreate(
				['ETH', '8.765', 'BTC', f'{dfl_seed_id}:B:4'],
				add_opts = ['--trade-limit=3%']),
			expect = ':2019e4/1/0')

	def swaptxsign1(self):
		return self._swaptxsign()

	def swaptxsend1(self):
		return self._swaptxsend()

	def swaptxstatus1(self):
		self.mining_delay()
		return self._swaptxsend(add_opts=['--verbose', '--status'], status=True)

	def bal1(self):
		return self.bal('swap1')

	def bal2(self):
		return self.bal('swap2')
