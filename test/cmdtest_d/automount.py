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
test.cmdtest_d.automount: autosigning with automount tests for the cmdtest.py test suite
"""
import time

from .autosign import CmdTestAutosignThreaded
from .regtest import CmdTestRegtest, rt_pw
from ..include.common import gr_uc

class CmdTestAutosignAutomount(CmdTestAutosignThreaded, CmdTestRegtest):
	'automounted transacting operations via regtest mode'

	networks = ('btc', 'bch', 'ltc')
	tmpdir_nums = [49]
	bdb_wallet = True

	rt_data = {
		'rtFundAmt': {'btc':'500', 'bch':'500', 'ltc':'5500'},
	}
	bal2_chk = {
		'btc': '491.11002204',
		'bch': '498.7653392',
		'ltc': '5491.11002204'}

	cmd_group = (
		('setup',                            'regtest mode setup'),
		('walletgen_alice',                  'wallet generation (Alice)'),
		('addrgen_alice',                    'address generation (Alice)'),
		('addrimport_alice',                 'importing Alice’s addresses'),
		('fund_alice',                       'funding Alice’s wallet'),
		('generate',                         'mining a block'),
		('alice_bal1',                       'checking Alice’s balance'),
		('alice_txcreate1',                  'creating a transaction'),
		('alice_txcreate_bad_have_unsigned', 'creating the transaction again (error)'),
		('alice_run_autosign_setup',         'running ‘autosign setup’ (with default wallet)'),
		('wait_loop_start',                  'starting autosign wait loop'),
		('alice_txstatus1',                  'getting transaction status (unsigned)'),
		('alice_txstatus2',                  'getting transaction status (unsent)'),
		('alice_txcreate_bad_have_unsent',   'creating the transaction again (error)'),
		('alice_txsend1',                    'sending a transaction, editing comment'),
		('alice_txstatus3',                  'getting transaction status (in mempool)'),
		('alice_txsend_bad_no_unsent',       'sending the transaction again (error)'),
		('generate',                         'mining a block'),
		('alice_txstatus4',                  'getting transaction status (one confirmation)'),
		('alice_txcreate2',                  'creating a transaction'),
		('alice_txsend_abort1',              'aborting the transaction (raw only)'),
		('alice_txsend_abort2',              'aborting the transaction again (error)'),
		('alice_txcreate3',                  'creating a transaction'),
		('alice_txsend_abort3',              'aborting the transaction (user exit)'),
		('alice_txsend_abort4',              'aborting the transaction (raw + signed)'),
		('alice_txsend_abort5',              'aborting the transaction again (error)'),
		('generate',                         'mining a block'),
		('alice_txcreate4',                  'creating a transaction'),
		('alice_txbump1',                    'bumping the unsigned transaction (error)'),
		('alice_txbump2',                    'bumping the unsent transaction (error)'),
		('alice_txsend2_dump_hex',           'dumping the transaction to hex'),
		('alice_txsend2_cli',                'sending the transaction via cli'),
		('alice_txsend2_mark_sent',          'marking the transaction sent'),
		('alice_txbump3',                    'bumping the transaction'),
		('alice_txsend3',                    'sending the bumped transaction'),
		('alice_txbump4',                    'bumping the transaction (new outputs, fee too low)'),
		('alice_txbump_abort1',              'aborting the transaction'),
		('alice_txbump5',                    'bumping the transaction (new outputs)'),
		('alice_txsend5',                    'sending the bumped transaction'),
		('alice_txstatus5',                  'getting transaction status (in mempool)'),
		('generate',                         'mining a block'),
		('alice_bal2',                       'checking Alice’s balance'),
		('wait_loop_kill',                   'stopping autosign wait loop'),
		('stop',                             'stopping regtest daemon'),
		('txview',                           'viewing transactions'),
	)

	def __init__(self, cfg, trunner, cfgs, spawn):

		self.coins = [cfg.coin.lower()]

		CmdTestAutosignThreaded.__init__(self, cfg, trunner, cfgs, spawn)
		CmdTestRegtest.__init__(self, cfg, trunner, cfgs, spawn)

		if trunner is None:
			return

		self.opts.append('--alice')

	def alice_txcreate1(self):
		return self._user_txcreate(
			'alice',
			chg_addr = 'C:5',
			data_arg = 'data:'+gr_uc[:24])

	def alice_txcreate2(self):
		return self._user_txcreate('alice', chg_addr='L:5')

	alice_txcreate3 = alice_txcreate2

	def alice_txcreate4(self):
		return self._user_txcreate('alice', chg_addr='L:4', need_rbf=True)

	def _alice_txsend_abort(self, err=False, send_resp='y', expect=None, shred_expect=[]):
		self.insert_device_online()
		t = self.spawn(
				'mmgen-txsend',
				['--quiet', '--abort'],
				no_passthru_opts = ['coin'],
				exit_val = 2 if err else 1 if send_resp == 'n' else None)
		if err:
			t.expect(expect)
		else:
			t.expect('(y/N): ', send_resp)
			if expect:
				t.expect(expect)
			for pat in shred_expect:
				t.expect(pat, regex=True)
		t.read()
		self.remove_device_online()
		return t

	def alice_txsend_abort1(self):
		return self._alice_txsend_abort(shred_expect=['Shredding .*arawtx'])

	def alice_txsend_abort2(self):
		return self._alice_txsend_abort(err=True, expect='No unsent transactions')

	def alice_txsend_abort3(self):
		return self._alice_txsend_abort(send_resp='n', expect='Exiting at user request')

	def alice_txsend_abort4(self):
		self._wait_signed('transaction')
		return self._alice_txsend_abort(shred_expect=[r'Shredding .*arawtx', r'Shredding .*asigtx'])

	alice_txsend_abort5 = alice_txsend_abort2

	def alice_txcreate_bad_have_unsigned(self):
		return self._user_txcreate('alice', chg_addr='C:5', exit_val=2, expect_str='already present')

	def alice_txcreate_bad_have_unsent(self):
		return self._user_txcreate('alice', chg_addr='C:5', exit_val=2, expect_str='unsent transaction')

	def alice_run_autosign_setup(self):
		return self.run_setup(mn_type='default', use_dfl_wallet=True, passwd=rt_pw)

	def alice_txsend1(self):
		return self._user_txsend('alice', comment='This one’s worth a comment', no_wait=True)

	def alice_txsend2_dump_hex(self):
		return self._user_txsend('alice', need_rbf=True, dump_hex=True)

	def alice_txsend2_cli(self):
		if not self.proto.cap('rbf'):
			return 'skip'
		return self._user_dump_hex_send_cli('alice')

	def alice_txsend2_mark_sent(self):
		return self._user_txsend('alice', need_rbf=True, mark_sent=True)

	def alice_txsend3(self):
		return self._user_txsend('alice', need_rbf=True)

	def alice_txsend5(self):
		return self._user_txsend('alice', need_rbf=True)

	def _alice_txstatus(self, expect, exit_val=None, need_rbf=False):

		if need_rbf and not self.proto.cap('rbf'):
			return 'skip'

		self.insert_device_online()
		t = self.spawn(
				'mmgen-txsend',
				['--alice', '--autosign', '--status', '--verbose'],
				no_passthru_opts = ['coin'],
				exit_val = exit_val)
		t.expect(expect)
		if not exit_val:
			t.expect('view: ', 'n')
		t.read()
		self.remove_device_online()
		return t

	def alice_txstatus1(self):
		return self._alice_txstatus('unsigned', 1)

	def alice_txstatus2(self):
		self._wait_signed('transaction')
		return self._alice_txstatus('unsent', 1)

	def alice_txstatus3(self):
		return self._alice_txstatus('in mempool', 0)

	def alice_txstatus4(self):
		return self._alice_txstatus('1 confirmation', 0)

	def alice_txstatus5(self):
		return self._alice_txstatus('in mempool', need_rbf=True)

	def alice_txsend_bad_no_unsent(self):
		self.insert_device_online()
		t = self.spawn('mmgen-txsend', ['--quiet', '--autosign'], exit_val=2, no_passthru_opts=['coin'])
		t.expect('No unsent transactions')
		t.read()
		self.remove_device_online()
		return t

	def _alice_txbump(self, fee_opt=None, output_args=[], bad_tx_expect=None, low_fee_fix=None):
		if not self.proto.cap('rbf'):
			return 'skip'
		self.insert_device_online()
		t = self.spawn(
				'mmgen-txbump',
				['--alice', '--autosign']
				+ ([fee_opt] if fee_opt else [])
				+ output_args,
				exit_val = 1 if bad_tx_expect else None)
		if bad_tx_expect:
			time.sleep(0.5)
			t.expect('Only sent transactions')
			t.expect(bad_tx_expect)
		else:
			if not output_args:
				t.expect(r'to deduct the fee from .* change output\): ', '\n', regex=True)
				t.expect(r'(Y/n): ', 'y')  # output OK?
			if low_fee_fix or not fee_opt:
				if low_fee_fix:
					t.expect('Please choose a higher fee')
				t.expect('transaction fee: ', (low_fee_fix or '200s') + '\n')
			if output_args:
				t.expect(r'(Y/n): ', 'y')
			t.expect(r'(Y/n): ', 'y')  # fee OK?
			t.expect(r'(y/N): ', '\n') # add comment?
			t.expect(r'(y/N): ', 'y')  # save?
		t.read()
		self.remove_device_online()
		return t

	def alice_txbump1(self):
		return self._alice_txbump(bad_tx_expect='unsigned transaction')

	def alice_txbump2(self):
		self._wait_signed('transaction')
		return self._alice_txbump(bad_tx_expect='unsent transaction')

	def alice_txbump3(self):
		return self._alice_txbump()

	def alice_txbump4(self):
		sid = self._user_sid('alice')
		return self._alice_txbump(
			fee_opt = '--fee=3s',
			output_args = [f'{self.burn_addr},7.654321', f'{sid}:C:1'],
			low_fee_fix = '300s')

	def alice_txbump_abort1(self):
		if not self.proto.cap('rbf'):
			return 'skip'
		return self._alice_txsend_abort(shred_expect=['Shredding .*arawtx'])

	def alice_txbump5(self):
		sid = self._user_sid('alice')
		return self._alice_txbump(
			fee_opt = '--fee=400s',
			output_args = ['data:message for posterity', f'{self.burn_addr},7.654321', f'{sid}:C:1'])

	def alice_bal2(self):
		return self.user_bal('alice', self.bal2_chk[self.coin])
