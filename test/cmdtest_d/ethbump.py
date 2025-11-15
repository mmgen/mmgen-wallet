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
test.cmdtest_d.ethbump: Ethereum transaction bumping tests for the cmdtest.py test suite
"""

import sys, time, asyncio, json

from mmgen.cfg import Config
from mmgen.protocol import init_proto
from mmgen.util import ymsg, suf

from ..include.common import imsg, omsg_r

from .include.common import cleanup_env, dfl_words_file, dfl_sid
from .include.runner import CmdTestRunner
from .httpd.thornode.swap import ThornodeSwapServer

from .ethdev import CmdTestEthdev, CmdTestEthdevMethods
from .regtest import CmdTestRegtest
from .swap import CmdTestSwapMethods, create_cross_methods
from .ethswap import CmdTestEthSwapMethods

burn_addr = 'beefcafe22' * 4
method_template = """
def {name}(self):
	self.spawn(log_only=True)
	return ethbump_ltc.run_test("{ltc_name}", sub=True)
"""

class CmdTestEthBumpMethods:

	@property
	def devnet_block_period(self):
		return (
			self.cfg.devnet_block_period
			or self.cfg.test_suite_devnet_block_period
			or self.dfl_devnet_block_period[self.daemon.id])

	def _txcreate(self, args, acct):
		self.get_file_with_ext('rawtx', delete_all=True)
		return self.txcreate(args, acct=acct, interactive_fee='0.9G', fee_info_data=('0.0000189', '0.9'))

	def _txsign(self, has_label=True):
		self.get_file_with_ext('sigtx', delete_all=True)
		return self.txsign(has_label=has_label)

	def _txsend(self, has_label=True):
		return self.txsend(has_label=has_label)

	def _txbump_feebump(self, *args, **kwargs):
		self.get_file_with_ext('rawtx', delete_all=True)
		return self._txbump(*args, **kwargs)

	def _txbump_new_outputs(self, *, args, fee, add_opts=[]):
		self.get_file_with_ext('rawtx', delete_all=True)
		ext = '{}.regtest.sigtx'.format('-α' if self.cfg.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext, no_dot=True)
		return self.txbump_ui_common(
			self.spawn('mmgen-txbump', self.eth_opts + add_opts + args + [txfile]),
			fee = fee,
			fee_desc = 'or gas price',
			bad_fee = '0.9G')

	async def _token_fund_user(self, *, mm_idxs):
		return await self._token_transfer_ops(
			op          = 'fund_user',
			mm_idxs     = mm_idxs,
			token_addr  = 'token_addr1',
			amt         = self.token_fund_amt)

	def _token_txcreate(self, *, args, cmd='txcreate'):
		self.get_file_with_ext('sigtx', delete_all=True)
		t = self._create_token_tx(cmd=cmd, fee='1.3G', args=args, add_opts=self.eth_opts)
		t.expect('to confirm: ', 'YES\n')
		t.written_to_file('Sent transaction')
		return t

	async def _wait_for_block(self, require_seen=True):
		self.spawn(msg_only=True)
		if self.devnet_block_period:
			empty_pools_seen = 0
			tx_seen = False
			while True:
				await asyncio.sleep(1)
				t = self.spawn(
					'mmgen-cli',
					['--regtest=1', 'txpool_content'],
					env = cleanup_env(self.cfg),
					no_msg = True,
					silent = True)
				res = json.loads(t.read().strip())
				if p := res['pending']:
					imsg(f'Pool has {len(p)} transaction{suf(p)}')
					if self.tr.quiet:
						omsg_r('+')
					tx_seen = True
				else:
					imsg('Pool is empty')
					if self.tr.quiet:
						omsg_r('+')
					if tx_seen or not require_seen:
						break
					empty_pools_seen += 1
					if empty_pools_seen > 5:
						m = ('\nTransaction pool empty! Try increasing the block period with the'
							' --devnet-block-period option (current value is {})')
						ymsg(m.format(self.devnet_block_period))
						sys.exit(1)

		return 'ok'

class CmdTestEthBump(CmdTestEthBumpMethods, CmdTestEthSwapMethods, CmdTestSwapMethods, CmdTestEthdev):
	'Ethereum transaction bumping operations'

	networks = ('eth',)
	tmpdir_nums = [42]
	dfl_devnet_block_period = {'geth': 7, 'reth': 9}
	fund_amt = 100000
	token_fund_amt = 1000
	cross_group = 'ethbump_ltc'
	cross_coin = 'ltc'
	add_eth_opts = ['--bob']

	cmd_group_in = (
		('subgroup.ltc_init',           []),
		('subgroup.eth_init',           []),
		('subgroup.feebump',            ['eth_init']),
		('subgroup.new_outputs',        ['eth_init']),
		('subgroup.swap_feebump',       ['ltc_init', 'eth_init']),
		('subgroup.swap_new_outputs',   ['ltc_init', 'eth_init']),
		('subgroup.token_init',         ['eth_init']),
		('subgroup.token_feebump',      ['token_init']),
		('subgroup.token_new_outputs',  ['token_init']),
		('subgroup.token_init_swap',    ['token_init']),
		# ('subgroup.token_feebump_swap',  ['token_init_swap']), # TBD
		('subgroup.token_new_outputs_swap',  ['token_init_swap']),
		('ltc_stop',                    ''),
		('swap_server_stop',            'stopping the Thornode server'),
		('stop',                        'stopping daemon'),
	)
	cmd_subgroups = {
		'eth_init': (
			'initializing ETH tracking wallet',
			('setup',               'dev mode transaction bumping tests for Ethereum (start daemon)'),
			('addrgen',             'generating addresses'),
			('addrimport',          'importing addresses'),
			('addrimport_devaddr',  'importing the dev address'),
			('addrimport_reth_devaddr','importing the reth dev address'),
			('fund_devaddr',        'funding the dev address'),
			('wait_reth1',          'waiting for block'),
			('del_reth_devaddr',    'deleting the reth dev address'),
			('fund_mmgen_addr1',    'funding user address :1)'),
			('fund_mmgen_addr2',    'funding user address :11)'),
			('fund_mmgen_addr3',    'funding user address :21)'),
			('wait1',               'waiting for block'),
		),
		'ltc_init': (
			'initializing LTC tracking wallet',
			('ltc_setup',          ''),
			('ltc_walletconv_bob', ''),
			('ltc_addrgen_bob',    ''),
			('ltc_addrimport_bob', ''),
		),
		'feebump': (
			'creating, signing, sending, bumping and resending a transaction (fee-bump only)',
			('txcreate1',   'creating a transaction (send to burn address)'),
			('txsign1',     'signing the transaction'),
			('txsend1',     'sending the transaction'),
			('txbump1',     'creating a replacement transaction (fee-bump)'),
			('txbump1sign', 'signing the replacement transaction'),
			('txbump1send', 'sending the replacement transaction'),
			('wait2',       'waiting for block'),
			('bal1',        'checking the balance'),
		),
		'new_outputs': (
			'creating, signing, sending, bumping and resending a transaction (new outputs)',
			('txcreate2',   'creating a transaction (send to burn address)'),
			('txsign2',     'signing the transaction'),
			('txsend2',     'sending the transaction'),
			('txbump2',     'creating a replacement transaction (new outputs)'),
			('txbump2sign', 'signing the replacement transaction'),
			('txbump2send', 'sending the replacement transaction'),
			('wait3',       'waiting for block'),
			('bal2',        'checking the balance'),
		),
		'swap_feebump': (
			'creating, signing, sending, bumping and resending a swap transaction (fee-bump only)',
			('swaptxcreate1',   'creating a swap transaction (from address :11)'),
			('swaptxsign1',     'signing the transaction'),
			('swaptxsend1',     'sending the transaction'),
			('swaptxbump1',     'creating a replacement swap transaction (fee-bump)'),
			('swaptxbump1sign', 'signing the replacement transaction'),
			('swaptxbump1send', 'sending the replacement transaction'),
			('wait4',           'waiting for block'),
			('bal3',            'checking the balance'),
		),
		'swap_new_outputs': (
			'creating, signing, sending, bumping and resending a swap transaction (new output)',
			('swaptxcreate2',   'creating a swap transaction (from address :21)'),
			('swaptxsign2',     'signing the transaction'),
			('swaptxsend2',     'sending the transaction'),
			('swaptxbump2',     'creating a replacement swap transaction (new output)'),
			('swaptxbump2sign', 'signing the replacement transaction'),
			('swaptxbump2send', 'sending the replacement transaction'),
			('wait5',           'waiting for block'),
			('bal4',            'checking the balance'),
		),
		'token_init': (
			'initializing token wallets',
			('token_compile1',   'compiling ERC20 token #1'),
			('token_deploy_a',   'deploying ERC20 token MM1 (SafeMath)'),
			('token_deploy_b',   'deploying ERC20 token MM1 (Owned)'),
			('token_deploy_c',   'deploying ERC20 token MM1 (Token)'),
			('token_fund_user1', 'transferring token funds from dev to user (addr #1)'),
			('token_addrgen',    'generating token addresses'),
			('token_addrimport', 'importing token addresses using token address (MM1)'),
			('token_bal1',       'the token balance'),
		),
		'token_feebump': (
			'creating, signing, sending, bumping and resending a token transaction (fee-bump only)',
			('token_txdo1',   'creating, signing and sending a token transaction'),
			('token_txbump1', 'bumping the token transaction (fee-bump)'),
			('wait6',         'waiting for block'),
			('token_bal2',    'the token balance'),
		),
		'token_new_outputs': (
			'creating, signing, sending, bumping and resending a token transaction (new outputs)',
			('token_txdo2',       'creating, signing and sending a token transaction'),
			('token_txbump2',     'creating a replacement token transaction (new outputs)'),
			('token_txbump2sign', 'signing the replacement transaction'),
			('token_txbump2send', 'sending the replacement transaction'),
			('wait7',             'waiting for block'),
			('token_bal3',        'the token balance'),
		),
		'token_init_swap': (
			'initializing token swap configuration',
			('token_compile_router',  'compiling THORChain router contract'),
			('token_deploy_router',   'deploying THORChain router contract'),
		),
		'token_feebump_swap': (
			'creating, signing, sending, bumping and resending a token swap transaction (feebump)',
			('token_fund_user11',     'transferring token funds from dev to user (addr #11)'),
			('token_addrimport_inbound', 'importing THORNode inbound token address'),
			('token_swaptxdo1',       'creating, signing and sending a token transaction (feebump)'),
			('token_swaptxbump1',     'bumping the token transaction (fee-bump)'),
			('token_swaptxbump1sign', 'signing the replacement transaction'),
			('token_swaptxbump1send', 'sending the replacement transaction'),
			('wait8',                 'waiting for block'),
			('token_bal5',            'the token balance'),
		),
		'token_new_outputs_swap': (
			'creating, signing, sending, bumping and resending a token swap transaction (new outputs)',
			('token_swaptxdo2',       'creating, signing and sending a token swap transaction (new outputs)'),
			('token_swaptxbump2',     'creating a replacement token transaction'),
			('token_swaptxbump2sign', 'signing the replacement transaction'),
			('token_swaptxbump2send', 'sending the replacement transaction'),
			('wait9',                 'waiting for block'),
			('token_bal6',            'the token balance'),
		),
	}

	exec(create_cross_methods(cross_coin, cross_group, cmd_group_in, cmd_subgroups))

	def __init__(self, cfg, trunner, cfgs, spawn):

		CmdTestEthdev.__init__(self, cfg, trunner, cfgs, spawn)

		if not trunner:
			return

		self.daemon.usr_coind_args = {
			'reth': [f'--dev.block-time={self.devnet_block_period}s'],
			'geth': [f'--dev.period={self.devnet_block_period}']
		}[self.daemon.id]

		imsg(f'devnet block period: {self.devnet_block_period}')

		globals()[self.cross_group] = self.create_cross_runner(trunner)

		self.swap_server = ThornodeSwapServer(cfg)
		self.swap_server.start()

	def txcreate1(self):
		return self._txcreate(args=[f'{burn_addr},987'], acct='1')

	def txbump1(self):
		return self._txbump_feebump(fee='1.3G', ext='{}.regtest.sigtx')

	def txcreate2(self):
		return self._txcreate(args=[f'{burn_addr},789'], acct='1')

	def txbump2(self):
		return self._txbump_new_outputs(args=[f'{dfl_sid}:E:2,777'], fee='1.3G')

	def swaptxcreate1(self):
		return self._swaptxcreate_ui_common(
			self._swaptxcreate(['ETH', '12.34567', 'LTC', f'{dfl_sid}:B:3']),
			inputs = 4)

	def swaptxsign1(self):
		return self._swaptxsign()

	def swaptxsend1(self):
		return self._swaptxsend()

	def swaptxbump1(self):
		return self._swaptxbump('41.1G', add_opts=['--bob'])

	def swaptxbump2(self):
		return self._swaptxbump('1.9G', add_opts=['--bob'], output_args=[f'{dfl_sid}:E:12,4444.3333'])

	def bal1(self):
		return self._bal_check(pat=rf'{dfl_sid}:E:1\s+99012\.9999727\s')

	def bal2(self):
		return self._bal_check(pat=rf'{dfl_sid}:E:2\s+777\s')

	def bal3(self):
		dec = {'geth': '653431389777251448', 'reth': '65337812418775812'}[self.daemon.id]
		return self._bal_check(pat=rf'{dfl_sid}:E:11\s+99987\.{dec}\s')

	def bal4(self):
		return self._bal_check(pat=rf'{dfl_sid}:E:12\s+4444\.3333\s')

	async def token_fund_user1(self):
		return await self._token_fund_user(mm_idxs=[1])

	async def token_fund_user11(self):
		return await self._token_fund_user(mm_idxs=[11])

	def token_txdo1(self):
		return self._token_txcreate(cmd='txdo', args=[f'{dfl_sid}:E:2,1.23456', dfl_words_file])

	def token_txbump1(self):
		t = self._txbump_feebump(
			fee = '60G',
			ext = '{}.regtest.sigtx',
			add_opts = ['--token=MM1'],
			add_args = [dfl_words_file])
		t.expect('to confirm: ', 'YES\n')
		t.written_to_file('Sent transaction')
		return t

	def token_bal2(self):
		return self._token_bal_check(pat=rf'{dfl_sid}:E:2\s+1\.23456')

	def token_txdo2(self):
		return self._token_txcreate(cmd='txdo', args=[f'{dfl_sid}:E:3,5.4321', dfl_words_file])

	def token_txbump2(self):
		return self._txbump_new_outputs(
			args = [f'{dfl_sid}:E:4,6.54321'],
			fee = '1.6G',
			add_opts = ['--token=mm1', '--gas=75000'])

	def token_txbump2sign(self):
		return self._txsign(has_label=False)

	def token_txbump2send(self):
		return self._txsend(has_label=False)

	def token_bal3(self):
		return self._token_bal_check(pat=rf'{dfl_sid}:E:4\s+6\.54321')

	async def wait_reth1(self):
		return await self._wait_for_block() if self.daemon.id == 'reth' else 'silent'

	def token_swaptxdo1(self):
		self.get_file_with_ext('sigtx', delete_all=True)
		t = self._swaptxcreate(
				['ETH.MM1', '0.321', 'ETH', dfl_words_file],
				action = 'txdo')
		t.expect('(Y/n): ', '\n')
		return self._swaptxcreate_ui_common(
			t,
			sign_and_send = True,
			need_passphrase = False,
			file_desc = 'Sent transaction',
			inputs = 11)

	def token_swaptxbump1(self):
		time.sleep(0.2)
		self.get_file_with_ext('rawtx', delete_all=True)
		txfile = self.get_file_with_ext('sigtx', no_dot=True)
		t = self.spawn(
			'mmgen-txbump',
			self.eth_opts
			+ ['--gas=50000'] # , '--router-gas=600000']
			+ ['--yes', txfile])
		t.expect('to continue: ', '\n')     # exit swap quote view
		t.expect('or gas price: ', '8G\n')  # enter fee
		t.expect(r'Gas limit:.*\D650000\D', regex=True)
		t.written_to_file('Fee-bumped transaction')
		return t

	def token_swaptxdo2(self):
		self.get_file_with_ext('sigtx', delete_all=True)
		return self._swaptxcreate_ui_common(
			self._swaptxcreate(
				['ETH.MM1', '0.321', 'ETH', f'{dfl_sid}:E:21', dfl_words_file],
				action = 'txdo'),
			sign_and_send = True,
			need_passphrase = False,
			file_desc = 'Sent transaction',
			inputs = 1)

	def token_swaptxbump2(self):
		return self._txbump_new_outputs(
			args = [f'{dfl_sid}:E:8,0.54321'],
			fee = '1.4G',
			add_opts = ['--gas=67888', '--fee=3G'])

	def token_bal5(self):
		return self._token_bal_check(pat=r'feedbeefcafe\s+non-MMGen\s+0\.321\s')

	def token_bal6(self):
		return self._token_bal_check(pat=rf'{dfl_sid}:E:8\s+0\.54321')

	wait1 = wait2 = wait3 = wait4 = wait5 = wait6 = wait7 = wait8 = wait9 = CmdTestEthBumpMethods._wait_for_block

	txsign1 = txsign2 = txbump1sign = txbump2sign = CmdTestEthBumpMethods._txsign
	txsend1 = txsend2 = txbump1send = txbump2send = CmdTestEthBumpMethods._txsend

	swaptxcreate2 = swaptxcreate1
	swaptxsign2 = swaptxsign1
	swaptxsend2 = swaptxsend1

	token_swaptxbump1sign = token_swaptxbump2sign = swaptxbump1sign = swaptxbump2sign = token_txbump2sign
	token_swaptxbump1send = token_swaptxbump2send = swaptxbump1send = swaptxbump2send = token_txbump2send

	def swap_server_stop(self):
		return self._thornode_server_stop()

class CmdTestEthBumpLTC(CmdTestSwapMethods, CmdTestRegtest):
	'Ethereum transaction bumping operations - LTC wallet'
	network = ('ltc',)
	tmpdir_nums = [43]
	is_helper = True
	cmd_group_in = CmdTestRegtest.cmd_group_in + (
		('setup',           'LTC regtest setup'),
		('walletconv_bob',  'LTC wallet generation'),
		('addrgen_bob',     'LTC address generation'),
		('addrimport_bob',  'importing LTC addresses'),
		('stop',            'stopping the Litecoin daemon'),
	)
