#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.cmdtest_py_d.ct_automount: autosigning with automount tests for the cmdtest.py test suite
"""
import os, time
from pathlib import Path

from .ct_autosign import CmdTestAutosignThreaded
from .ct_regtest import CmdTestRegtestBDBWallet, rt_pw
from .common import get_file_with_ext
from ..include.common import cfg

class CmdTestAutosignAutomount(CmdTestAutosignThreaded, CmdTestRegtestBDBWallet):
	'automounted transacting operations via regtest mode'

	networks = ('btc', 'bch', 'ltc')
	tmpdir_nums = [49]
	extra_spawn_args = []

	rtFundAmt = None # pylint
	rt_data = {
		'rtFundAmt': {'btc':'500', 'bch':'500', 'ltc':'5500'},
	}

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
		('copy_wallet',                      'copying Alice’s wallet'),
		('alice_run_autosign_setup',         'running ‘autosign setup’ (with default wallet)'),
		('autosign_start_thread',            'starting autosign wait loop'),
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
		('alice_txsend2',                    'sending the transaction'),
		('alice_txbump3',                    'bumping the transaction'),
		('alice_txsend3',                    'sending the bumped transaction'),
		('autosign_kill_thread',             'stopping autosign wait loop'),
		('stop',                             'stopping regtest daemon'),
		('txview',                           'viewing transactions'),
	)

	def __init__(self, trunner, cfgs, spawn):

		self.coins = [cfg.coin.lower()]

		CmdTestAutosignThreaded.__init__(self, trunner, cfgs, spawn)
		CmdTestRegtestBDBWallet.__init__(self, trunner, cfgs, spawn)

		if trunner == None:
			return

		self.opts.append('--alice')

	def _alice_txcreate(self, chg_addr, opts=[], exit_val=0, expect=None):
		self.insert_device_online()
		sid = self._user_sid('alice')
		t = self.spawn(
			'mmgen-txcreate',
			opts
			+ ['--alice', '--autosign']
			+ [f'{self.burn_addr},1.23456', f'{sid}:{chg_addr}'],
			exit_val = exit_val or None)
		if exit_val:
			t.expect(expect)
			t.read()
			self.remove_device_online()
			return t
		t = self.txcreate_ui_common(
			t,
			inputs          = '1',
			interactive_fee = '32s',
			file_desc       = 'Unsigned automount transaction')
		if expect:
			t.expect(expect)
		t.read()
		self.remove_device_online()
		return t

	def alice_txcreate1(self):
		return self._alice_txcreate(chg_addr='C:5')

	def alice_txcreate2(self):
		return self._alice_txcreate(chg_addr='L:5')

	alice_txcreate3 = alice_txcreate2

	def alice_txcreate4(self):
		if cfg.coin == 'BCH':
			return 'skip'
		return self._alice_txcreate(chg_addr='L:4')

	def _alice_txsend_abort(self, err=False, send_resp='y', expect=None, shred_expect=[]):
		self.insert_device_online()
		t = self.spawn(
				'mmgen-txsend',
				['--quiet', '--abort'],
				exit_val = 2 if err else 1 if send_resp == 'n' else None)
		if err:
			t.expect(expect)
		else:
			t.expect('(y/N): ', send_resp)
			if expect:
				t.expect(expect)
			for pat in shred_expect:
				t.expect(pat, regex=True)
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
		return self._alice_txcreate(chg_addr='C:5', exit_val=2, expect='already present')

	def alice_txcreate_bad_have_unsent(self):
		return self._alice_txcreate(chg_addr='C:5', exit_val=2, expect='unsent transaction')

	def copy_wallet(self):
		self.spawn('', msg_only=True)
		if cfg.coin == 'BTC':
			return 'skip_msg'
		src  = Path(self.tr.data_dir, 'regtest', cfg.coin.lower(), 'alice')
		dest = Path(self.tr.data_dir, 'regtest', 'btc', 'alice')
		dest.mkdir(parents=True, exist_ok=True)
		wf = Path(get_file_with_ext(src, 'mmdat')).absolute()
		link_path = dest / wf.name
		if not link_path.exists():
			link_path.symlink_to(wf)
		return 'ok'

	def alice_run_autosign_setup(self):
		self.insert_device()
		t = self.run_setup(mn_type='default', use_dfl_wallet=True, passwd=rt_pw)
		t.read()
		self.remove_device()
		return t

	def alice_txsend1(self):
		return self._alice_txsend('This one’s worth a comment', no_wait=True)

	def alice_txsend2(self):
		if cfg.coin == 'BCH':
			return 'skip'
		return self._alice_txsend()

	def alice_txsend3(self):
		if cfg.coin == 'BCH':
			return 'skip'
		return self._alice_txsend()

	def _alice_txstatus(self, expect, exit_val=None):
		self.insert_device_online()
		t = self.spawn(
				'mmgen-txsend',
				['--alice', '--autosign', '--status', '--verbose'],
				exit_val = exit_val)
		t.expect(expect)
		self.remove_device_online()
		return t

	def alice_txstatus1(self):
		return self._alice_txstatus('unsigned', 1)

	def alice_txstatus2(self):
		self._wait_signed('transaction')
		return self._alice_txstatus('unsent', 1)

	def alice_txstatus3(self):
		return self._alice_txstatus('in mempool')

	def alice_txstatus4(self):
		return self._alice_txstatus('1 confirmation', 0)

	def _alice_txsend(self, comment=None, no_wait=False):
		if not no_wait:
			self._wait_signed('transaction')
		self.insert_device_online()
		t = self.spawn('mmgen-txsend', ['--alice', '--quiet', '--autosign'])
		t.view_tx('t')
		t.do_comment(comment)
		self._do_confirm_send(t, quiet=True)
		t.written_to_file('Sent automount transaction')
		t.read()
		self.remove_device_online()
		return t

	def alice_txsend_bad_no_unsent(self):
		self.insert_device_online()
		t = self.spawn('mmgen-txsend', ['--quiet', '--autosign'], exit_val=2)
		t.expect('No unsent transactions')
		t.read()
		self.remove_device_online()
		return t

	def _alice_txbump(self, bad_tx_desc=None):
		if cfg.coin == 'BCH':
			return 'skip'
		self.insert_device_online()
		t = self.spawn(
				'mmgen-txbump',
				['--alice', '--autosign'],
				exit_val = 1 if bad_tx_desc else None)
		if bad_tx_desc:
			t.expect('Only sent transactions')
			t.expect(bad_tx_desc)
		else:
			t.expect(f'to deduct the fee from .* change output\): ', '\n', regex=True)
			t.expect(r'(Y/n): ', 'y')  # output OK?
			t.expect('transaction fee: ', '200s\n')
			t.expect(r'(Y/n): ', 'y')  # fee OK?
			t.expect(r'(y/N): ', '\n') # add comment?
			t.expect(r'(y/N): ', 'y')  # save?
		t.read()
		self.remove_device_online()
		return t

	def alice_txbump1(self):
		return self._alice_txbump(bad_tx_desc='unsigned transaction')

	def alice_txbump2(self):
		self._wait_signed('transaction')
		return self._alice_txbump(bad_tx_desc='unsent transaction')

	def alice_txbump3(self):
		return self._alice_txbump()
