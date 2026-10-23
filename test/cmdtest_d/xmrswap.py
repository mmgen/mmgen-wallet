# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.cmdtest_d.xmrswap: Monero swap tests for the cmdtest.py test suite
"""

import json

from .xmr_autosign import CmdTestXMRCompat
from .swap import CmdTestSwap, CmdTestSwapMethods, create_cross_methods

class CmdTestXMRSwapMethods:

	def _swaptxcreate_ui(
			self,
			t,
			prompt,
			*,
			tx_type         = 'swap',
			inputs          = '1',
			interactive_fee = None,
			file_desc       = 'Unsigned transaction',
			tweaks          = [],
			auto_chg_addr   = None,
			auto_dest_addr  = None,
			reload_quote    = False,
			menu_prompt     = None,
			expect_pats     = []):
		if auto_chg_addr:
			t.expect(rf'Using.*{auto_chg_addr}.*as change address.*: ', 'y', regex=True)
		if tx_type == 'registration':
			if auto_dest_addr:
				t.expect(rf'Using.*{auto_dest_addr}.*as destination address.*: ', 'y', regex=True)
			t.expect('continue: ', '\n')
			t.expect(prompt, 'q')
			t.expect('spend from: ', f'{inputs}\n')
		elif tx_type in ('swap', 'xmr_swap'):
			t.expect(prompt, 'q')
			t.expect('to spend: ', f'{inputs}\n')
			t.expect('continue: ', '\n')
			if tx_type == 'xmr_swap':
				for pat in expect_pats:
					t.expect(pat, regex=True)
				t.expect('(y/N): ', 'y')    # save?
				t.written_to_file('Unsigned transaction')
				return t
			t.expect('(Y/n): ', 'y')        # fee OK?
			t.expect('(Y/n): ', 'y')        # change OK?
		t.expect('(y/N): ', 'n')            # add comment?
		t.expect('view: ', 't')
		for pat in expect_pats:
			t.expect(pat, regex=True)
		t.expect('to continue: ', '\n')
		t.expect('(y/N): ', 'y')            # save?
		t.written_to_file('Unsigned automount transaction')
		return t

	def _swaptxcreate_refreq(
			self,
			*,
			args,
			inputs,
			auto_chg_addr  = None,
			auto_dest_addr = None,
			expect_pats    = None,
			exit_val       = 0):
		return self._user_txcreate(
			'bob',
			progname = 'swaptxcreate',
			opts = ['--monero-wallet-rpc-password=abc', '--memoless'],
			ui_handler = self._swaptxcreate_ui,
			ui_handler_args = {
				'prompt': self.rune_menu_prompt,
				'tx_type': 'registration',
				'inputs': inputs,
				'auto_chg_addr': auto_chg_addr,
				'auto_dest_addr': auto_dest_addr,
				'expect_pats': expect_pats},
			exit_val = exit_val,
			output_args = args)

	def _swaptxcreate_refnum(
			self,
			*,
			args,
			inputs,
			tx_type        = 'swap',
			add_opts       = [],
			auto_chg_addr  = None,
			auto_dest_addr = None,
			prompt         = None,
			expect_pats    = None,
			exit_val       = 0):
		data = json.loads(self.read_from_tmpfile('memo_info.json'))
		return self._user_txcreate(
			'bob',
			progname = 'swaptxcreate',
			opts = ['--monero-wallet-rpc-password=abc', f'--refnum={data["reference"]}'] + add_opts,
			exit_val = exit_val,
			ui_handler = self._swaptxcreate_ui,
			ui_handler_args = {
				'prompt': prompt or self.menu_prompt,
				'tx_type': tx_type,
				'inputs': inputs,
				'auto_chg_addr': auto_chg_addr,
				'auto_dest_addr': auto_dest_addr,
				'expect_pats': expect_pats},
			output_args = args)

	def _swaptxsend_refnum(self, expect_pat, *, add_opts=[], is_xmr=False):
		return self._user_txsend(
			'bob',
			add_opts = ['--monero-wallet-rpc-password=abc'] + add_opts,
			expect_pat = expect_pat,
			is_xmr = is_xmr,
			need_rbf = True)

class CmdTestXMRSwap(CmdTestXMRSwapMethods, CmdTestSwap):
	'Monero swap operations'

	bdb_wallet = True
	tmpdir_nums = [77]
	networks = ('ltc',)
	thornode_servers = ('rpc', 'swap')
	cross_group = 'xmrswap_xmr'
	cross_coin = 'xmr'
	refreq_txid = 'ae04ecd8ff1f0c13861bd2d6123ce33ea03a731ccd142f5ca2f2450a54f215ba'
	refreq_txid_xmr = 'fbbbd382edd2d5478e0316b6c31ef6a0bbad57bcebc9d8b30cc52e5dbf107622'
	xmr_prompt = 'efresh balances:\b'

	cmd_group_in = (
		('subgroup.ltc_setup',      []),
		('subgroup.rune_setup',     ['ltc_setup']),
		('subgroup.autosign_setup', []),
		('subgroup.xmr_setup',      ['ltc_setup', 'autosign_setup']),
		('subgroup.wait_loop',      ['autosign_setup']),
		('subgroup.swap',           ['rune_setup', 'xmr_setup', 'wait_loop']),
		('subgroup.xmr_swap',       ['swap']),
		('xmr_wait_loop_kill',      ''),
		('xmr_stop_daemons',        ''))

	cmd_subgroups = {
	'ltc_setup': (
		'setting up Bob’s MMGen wallet and tracking wallet',
		('setup',                 'regtest (Bob and Alice) mode setup'),
		('walletconv_bob',        'MMGen wallet creation (Bob)'),
		('addrgen_bob',           'address generation (Bob)'),
		('addrimport_bob',        'importing Bob’s addresses'),
		('bob_import_miner_addr', 'importing miner’s coinbase addr into Bob’s wallet'),
		('fund_bob1',             'funding Bob’s wallet'),
		('fund_bob2',             'funding Bob’s wallet'),
		('fund_bob3',             'funding Bob’s wallet'),
		('generate_ltc',          'mining a block'),
		('bob_bal1',              'Bob’s balance'),
	),
	'rune_setup': (
		'setting up Bob’s RUNE tracking wallet',
		('rune_addrgen',     'generating RUNE addresses'),
		('rune_addrimport',  'importing RUNE addresses'),
		('rune_bal_refresh', 'refreshing balances in RUNE tracking wallet'),
	),
	'autosign_setup': (
		'setting up offline autosigning',
		('xmr_autosign_setup',     ''),
		('xmr_autosign_xmr_setup', ''),
	),
	'xmr_setup': (
		'setting up miner’s and Bob’s XMR tracking wallets',
		('xmr_addrimport_user',            ''),
		('xmr_gen_kafile_miner',           ''),
		('xmr_gen_vkafile_user',           ''),
		('xmr_create_wallet_miner',        ''),
		('xmr_mine_initial_coins',         ''),
		('xmr_fund_user1',                 ''),
		('xmr_mine_blocks_10',             ''),
		('xmr_new_address_user1',          ''),
		('xmr_new_address_user2',          ''),
		('xmr_new_account_user',           ''),
		('xmr_mine_blocks_10',             ''),
		('xmr_user_listaddresses_refresh', ''),
	),
	'wait_loop': (
		'starting the autosign wait loop',
		('xmr_wait_loop_start_compat', ''),
	),
	'swap': (
		'swap operations (LTC -> XMR)',
		('remote_get_refnum',    'getting the reference number'),
		('swaptxcreate_refreq1', 'creating an LTC->XMR registration transaction (auto chg, auto dest)'),
		('swaptxcreate_abort1',  'aborting the transaction'),
		('swaptxcreate_refreq2', 'creating an LTC->XMR registration transaction (auto chg, 1:0)'),
		('swaptxcreate_abort2',  'aborting the transaction'),
		('swaptxcreate_refreq3', 'creating an LTC->XMR registration transaction (auto chg, mmid dest)'),
		('swaptxsend_refreq1',   'sending the transaction'),
		('swaptxcreate_refreq4', 'creating an LTC->XMR registration transaction (auto chg, 1:1)'),
		('swaptxsend_refreq2',   'sending the transaction'),
		('swaptxcreate_refnum1', 'creating an LTC->XMR swap transaction (auto chg, auto dest)'),
		('swaptxsend_refnum1',   'sending the swap transaction'),
		('generate_ltc',         'generating a block'),
		('swaptxcreate_refnum2', 'creating an LTC->XMR swap transaction (no chg, auto dest)'),
		('swaptxsend_refnum2',   'sending the swap transaction'),
		('generate_ltc',         'generating a block'),
		('bob_bal2',             'Bob’s balance')),
	'xmr_swap': (
		'swap operations (XMR -> LTC)',
		('remote_get_refnum_xmr',    'getting the reference number'),
		('swaptxcreate_refreq7_bad', 'creating an XMR->LTC registration transaction (bad, no amount)'),
		('swaptxcreate_refreq7',     'creating an XMR->LTC registration transaction (auto chg, auto dest)'),
		('swaptxsend_refreq7',       'sending the transaction'),
		('swaptxcreate_refnum7_bad', 'creating an XMR->LTC swap transaction (bad, no amount)'),
		('swaptxcreate_refnum7',     'creating an XMR->LTC swap transaction (auto chg, auto dest)'),
		('swaptxsend_refnum7',       'sending the transaction'),
		('xmr_mine_blocks_10',       ''),
		('swaptxstatus_refnum7',     'getting the transaction status'))}

	exec(create_cross_methods(cross_coin, cross_group, cmd_group_in, cmd_subgroups))

	def __init__(self, cfg, trunner, cfgs, spawn):

		super().__init__(cfg, trunner, cfgs, spawn)

		self.spawn_env['MMGEN_TEST_SUITE_ENABLE_USER_PORT_SHIFT'] = '1'

		if not trunner:
			return

		globals()[self.cross_group] = self.create_cross_runner(trunner, add_cfg={})

	def fund_bob1(self):
		return self.fund_wallet('bob', 500, mmtype='C')

	def fund_bob2(self):
		return self.fund_wallet('bob', 50, mmtype='S')

	def fund_bob3(self):
		return self.fund_wallet('bob', 25, mmtype='B')

	def bob_bal1(self):
		return self._bob_bal(0, '575')

	def swaptxcreate_refreq1(self):
		return self._swaptxcreate_refreq(
			args = ['LTC', '5.4321', 'XMR'],
			inputs = '3',
			auto_chg_addr = '98831F3A:B:2',
			auto_dest_addr = '98831F3A:M:1/0/1',
			expect_pats = ['88u4waXXrPUD9EkCGMcFif', r'to spend:.*\b0\b.*RUNE'])

	def swaptxcreate_abort1(self):
		return self._txsend_abort()

	def swaptxcreate_refreq2(self):
		return self._swaptxcreate_refreq(
			args = ['LTC', '5.4321', 'XMR', '1:0'],
			inputs = '3',
			auto_chg_addr = '98831F3A:B:2',
			auto_dest_addr = '98831F3A:M:1/0/1',
			expect_pats = ['88u4waXXrPUD9EkCGMcFif', r'to spend:.*\b0\b.*RUNE'])

	def swaptxcreate_abort2(self):
		return self._txsend_abort()

	def swaptxcreate_refreq3(self):
		return self._swaptxcreate_refreq(
			args = ['LTC', '5.4321', 'XMR', '98831F3A:M:1/0/1'],
			inputs = '3',
			auto_chg_addr = '98831F3A:B:2',
			expect_pats = ['88u4waXXrPUD9EkCGMcFif', r'to spend:.*\b0\b.*RUNE'])

	def swaptxsend_refreq1(self):
		return self._user_txsend('bob', need_rbf=True)

	def swaptxcreate_refreq4(self):
		return self._swaptxcreate_refreq(
			args = ['LTC', '5.4321', 'XMR', '1:1'],
			inputs = '3',
			auto_chg_addr = '98831F3A:B:2',
			auto_dest_addr = '98831F3A:M:1/1/0',
			expect_pats = ['89NVJJPWPw18P7XoqiYgj4', r'to spend:.*\b0\b.*RUNE'])

	swaptxsend_refreq2 = swaptxsend_refreq1

	def swaptxcreate_refnum1(self):
		return self._swaptxcreate_refnum(
			args = ['LTC', '5.4321', 'XMR'],
			inputs = '1',
			auto_chg_addr = '98831F3A:B:2',
			expect_pats = ['88u4waXXrPUD9EkCGMcFif', r'Spend amount:.*\b5\.43198765\b.*LTC'])

	def swaptxsend_refnum1(self):
		return self._swaptxsend_refnum(r'Spend amount:.*\b5\.43198765\b.*LTC')

	def swaptxcreate_refnum2(self):
		return self._swaptxcreate_refnum(
			args = ['LTC', 'XMR'],
			inputs = '2',
			expect_pats = ['88u4waXXrPUD9EkCGMcFif', r'Spend amount:.*24\.99998765'])

	def swaptxsend_refnum2(self):
		return self._swaptxsend_refnum(r'Spend amount:.*24\.99998765')

	def bob_bal2(self):
		return self._bob_bal(0, '544.56799927')

	def remote_get_refnum_xmr(self):
		return self._remote_get_refnum(self.refreq_txid_xmr)

	def swaptxcreate_refreq7_bad(self):
		return self._swaptxcreate_refreq_xmr(['XMR', 'LTC'], exit_val=1)

	def swaptxcreate_refreq7(self):
		return self._swaptxcreate_refreq_xmr(['XMR', '0.2345', 'LTC'])

	def _swaptxcreate_refreq_xmr(self, args, *, exit_val=0):
		return self._swaptxcreate_refreq(
			args = args,
			inputs = '3',
			exit_val = exit_val,
			auto_dest_addr = '98831F3A:B:3',
			expect_pats = ['rltc1q6rs4znw8k', r'to spend:.*\b0\b.*RUNE'])

	def swaptxsend_refreq7(self):
		return self._user_txsend('bob', need_rbf=True)

	def swaptxcreate_refnum7_bad(self):
		return self._swaptxcreate_refnum_xmr(['XMR', 'LTC'], exit_val=1)

	def swaptxcreate_refnum7(self):
		return self._swaptxcreate_refnum_xmr(['XMR', '0.2345', 'LTC'])

	def _swaptxcreate_refnum_xmr(self, args, *, exit_val=0):
		return self._swaptxcreate_refnum(
			add_opts = ['--priority=3'],
			args = args,
			inputs = '1',
			tx_type = 'xmr_swap',
			prompt = self.xmr_prompt,
			exit_val = exit_val,
			auto_dest_addr = '98831F3A:B:3',
			expect_pats = [r'Amount:.*0.234499978787', r'Priority:.*high'])

	def swaptxsend_refnum7(self):
		return self._swaptxsend_refnum(r'Amount:.*0.234499978787', is_xmr=True)

	def swaptxstatus_refnum7(self):
		return self._swaptxsend_refnum(r'Amount:.*0.234499978787', add_opts=['--status', '--verbose'])

class CmdTestXMRSwapXMR(CmdTestXMRSwapMethods, CmdTestSwapMethods, CmdTestXMRCompat):
	'Monero swap operations - Monero wallet'
	networks = ('xmr',)
	tmpdir_nums = [77]
	is_helper = True
	tx_relay_user = None
	user = 'bob'
	user_data = (
		# user    sid       autosign kal_range add_coind_args
		('miner', 'FE3C6545', False, '1',   []),
		('bob',   '98831F3A', True,  '1-2', []))

	cmd_group = CmdTestXMRCompat.cmd_group + (
		('user_txcreate_sweep1',       'creating a sweep transaction (address sweep)'),
		('new_address_user1',          'adding an address to user’s wallet (acct 0)'),
		('new_address_user2',          'adding an address to user’s wallet (acct 0)'),
		('new_account_user',           'adding an account to user’s wallet'),
		('user_listaddresses_refresh', 'listing the user’s wallet, with refresh'))

	def user_txcreate_sweep1(self):
		return self._user_txops('txcreate', menu='s', sweep_menu='1', sweep_type='sweep')

	def _new_address_user(self, wallet, acct, action):
		return self._new_addr_user_autosign(
			f'{wallet}:{acct}',
			action,
			rf'Creating new address for wallet .*{wallet}.*, account .*#{acct}.* with label '
			r'.*‘xmrwallet new address .*y/N\): ')

	def new_address_user1(self):
		return self._new_address_user(1, 0, 'start')

	def new_address_user2(self):
		return self._new_address_user(1, 0, 'continue')

	def new_account_user(self):
		return self._new_addr_user_autosign(
			'1',
			'stop',
			r'Creating new account for wallet .*1.* with label '
			r'.*‘xmrwallet new account .*y/N\): ')
