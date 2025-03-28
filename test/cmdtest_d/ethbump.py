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

from mmgen.util import ymsg, suf

from .ethdev import CmdTestEthdev, CmdTestEthdevMethods, dfl_sid
from ..include.common import imsg, omsg_r
from .include.common import cleanup_env, dfl_words_file

burn_addr = 'beefcafe22' * 4

class CmdTestEthBumpMethods:

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

class CmdTestEthBump(CmdTestEthdev, CmdTestEthdevMethods, CmdTestEthBumpMethods):
	'Ethereum transaction bumping operations'

	networks = ('eth',)
	tmpdir_nums = [42]
	dfl_devnet_block_period = 7

	cmd_group_in = (
		('setup',                       'dev mode transaction bumping tests for Ethereum (start daemon)'),
		('subgroup.init',               []),
		('subgroup.feebump',            ['init']),
		('subgroup.new_outputs',        ['init']),
		('subgroup.token_init',         ['init']),
		('subgroup.token_feebump',      ['token_init']),
		('subgroup.token_new_outputs',  ['token_init']),
		('stop',                        'stopping daemon'),
	)
	cmd_subgroups = CmdTestEthdev.cmd_subgroups | {
		'init': (
			'initializing wallets',
			('addrgen',             'generating addresses'),
			('addrimport',          'importing addresses'),
			('addrimport_dev_addr', 'importing dev faucet address ‘Ox00a329c..’'),
			('fund_dev_address',    'funding the default (Parity dev) address'),
			('fund_mmgen_address',  'creating a transaction (spend from dev address to address :1)'),
			('wait2',               'waiting for block'),
		),
		'feebump': (
			'creating, signing, sending, bumping and resending a transaction (fee-bump only)',
			('txcreate1',   'creating a transaction (send to burn address)'),
			('txsign1',     'signing the transaction'),
			('txsend1',     'sending the transaction'),
			('txbump1',     'creating a replacement transaction (fee-bump)'),
			('txbump1sign', 'signing the replacement transaction'),
			('txbump1send', 'sending the replacement transaction'),
			('wait3',       'waiting for block'),
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
			('wait4',       'waiting for block'),
			('bal2',        'checking the balance'),
		),
		'token_init': (
			'initializing token wallets',
			('token_compile1',   'compiling ERC20 token #1'),
			('token_deploy_a',   'deploying ERC20 token MM1 (SafeMath)'),
			('token_deploy_b',   'deploying ERC20 token MM1 (Owned)'),
			('token_deploy_c',   'deploying ERC20 token MM1 (Token)'),
			('wait_reth1',       'waiting for block'),
			('token_fund_user',  'transferring token funds from dev to user'),
			('wait6',            'waiting for block'),
			('token_addrgen',    'generating token addresses'),
			('token_addrimport', 'importing token addresses using token address (MM1)'),
			('token_bal1',       'the token balance'),
		),
		'token_feebump': (
			'creating, signing, sending, bumping and resending a token transaction (fee-bump only)',
			('token_txdo1',   'creating, signing and sending a token transaction'),
			('token_txbump1', 'bumping the token transaction (fee-bump)'),
			('wait7',         'waiting for block'),
			('token_bal2',    'the token balance'),
		),
		'token_new_outputs': (
			'creating, signing, sending, bumping and resending a token transaction (new outputs)',
			('token_txdo2',       'creating, signing and sending a token transaction'),
			('token_txbump2',     'creating a replacement token transaction (new outputs)'),
			('token_txbump2sign', 'signing the replacement transaction'),
			('token_txbump2send', 'sending the replacement transaction'),
			('wait8',             'waiting for block'),
			('token_bal3',        'the token balance'),
		)
	}

	def __init__(self, cfg, trunner, cfgs, spawn):
		self.devnet_block_period = cfg.devnet_block_period or self.dfl_devnet_block_period
		CmdTestEthdev.__init__(self, cfg, trunner, cfgs, spawn)

	def fund_mmgen_address(self):
		return self._fund_mmgen_address(arg=f'{dfl_sid}:E:1,98765.4321')

	def txcreate1(self):
		return self._txcreate(args=[f'{burn_addr},987'], acct='1')

	def txbump1(self):
		return self._txbump_feebump(fee='1.3G', ext='{}.regtest.sigtx')

	def txcreate2(self):
		return self._txcreate(args=[f'{burn_addr},789'], acct='1')

	def txbump2(self):
		return self._txbump_new_outputs(args=[f'{dfl_sid}:E:2,777'], fee='1.3G')

	def bal1(self):
		return self._bal_check(pat=rf'{dfl_sid}:E:1\s+97778\.4320727\s')

	def bal2(self):
		return self._bal_check(pat=rf'{dfl_sid}:E:2\s+777\s')

	async def token_deploy_a(self):
		return await self._token_deploy_math(num=1, get_receipt=False)

	async def token_deploy_b(self):
		return await self._token_deploy_owned(num=1, get_receipt=False)

	async def token_deploy_c(self):
		return await self._token_deploy_token(num=1, get_receipt=False)

	def token_fund_user(self):
		return self._token_transfer_ops(op='fund_user', mm_idxs=[1], get_receipt=False)

	def token_addrgen(self):
		return self._token_addrgen(mm_idxs=[1], naddrs=5)

	def token_addrimport(self):
		return self._token_addrimport('token_addr1', '1-5', expect='5/5')

	def token_bal1(self):
		return self._token_bal_check(pat=rf'{dfl_sid}:E:1\s+1000\s')

	def token_txdo1(self):
		return self._token_txcreate(cmd='txdo', args=[f'{dfl_sid}:E:2,1.23456', dfl_words_file])

	def token_txbump1(self):
		t = self._txbump_feebump(
			fee = '60G',
			ext = '{}.regtest.sigtx',
			add_opts = ['--token=MM1'],
			add_args = [dfl_words_file])
		t.expect('to confirm: ', 'YES\n')
		t.written_to_file('Signed transaction')
		return t

	def token_bal2(self):
		return self._token_bal_check(pat=rf'{dfl_sid}:E:1\s+998.76544\s.*\s{dfl_sid}:E:2\s+1\.23456')

	def token_txdo2(self):
		return self._token_txcreate(cmd='txdo', args=[f'{dfl_sid}:E:3,5.4321', dfl_words_file])

	def token_txbump2(self):
		return self._txbump_new_outputs(
			args = [f'{dfl_sid}:E:4,6.54321'],
			fee = '1.6G',
			add_opts = ['--token=mm1'])

	def token_txbump2sign(self):
		return self._txsign(has_label=False)

	def token_txbump2send(self):
		return self._txsend(has_label=False)

	def token_bal3(self):
		return self._token_bal_check(pat=rf'{dfl_sid}:E:4\s+6\.54321')

	def wait_reth1(self):
		return self._wait_for_block() if self.daemon.id == 'reth' else 'silent'

	wait1 = wait2 = wait3 = wait4 = wait5 = wait6 = wait7 = wait8 = CmdTestEthBumpMethods._wait_for_block
	txsign1 = txsign2 = txbump1sign = txbump2sign = CmdTestEthBumpMethods._txsign
	txsend1 = txsend2 = txbump1send = txbump2send = CmdTestEthBumpMethods._txsend
