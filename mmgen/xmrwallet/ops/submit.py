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
xmrwallet.ops.submit: Monero wallet ops for the MMGen Suite
"""

import time
from pathlib import Path

from ...util import msg, msg_r, gmsg, die
from ...ui import keypress_confirm
from ...proto.xmr.daemon import MoneroWalletDaemon
from ...proto.xmr.rpc import MoneroWalletRPCClient

from ..rpc import MoneroWalletRPC

from . import OpBase
from .wallet import OpWallet

class OpSubmit(OpWallet):
	action = 'submitting transaction with'
	opts = ('tx_relay_daemon',)

	def post_mount_action(self):
		self.tx # trigger an exit if no suitable transaction present

	@property
	def tx(self):
		if not hasattr(self, '_tx'):
			self._tx = self.get_tx()
		return self._tx

	def get_tx(self):
		if self.uargs.infile:
			fn = Path(self.uargs.infile)
		else:
			from ...autosign import Signable
			fn = Signable.xmr_transaction(self.asi).get_unsubmitted()
		return self.get_tx_cls('ColdSigned')(cfg=self.cfg, fn=fn)

	def get_relay_rpc(self):

		relay_opt = self.parse_tx_relay_opt()

		wd = MoneroWalletDaemon(
			cfg         = self.cfg,
			proto       = self.proto,
			wallet_dir  = self.cfg.wallet_dir or '.',
			test_suite  = self.cfg.test_suite,
			monerod_addr = relay_opt[1])

		u = wd.usr_daemon_args = []
		if self.cfg.test_suite:
			u.append('--daemon-ssl-allow-any-cert')
		if relay_opt[2]:
			u.append(f'--proxy={relay_opt[2]}')

		return MoneroWalletRPCClient(
			cfg             = self.cfg,
			daemon          = wd,
			test_connection = False)

	async def main(self):
		tx = self.tx
		h = MoneroWalletRPC(self, self.kal.entry(tx.src_wallet_idx))
		self.head_msg(tx.src_wallet_idx, h.fn)
		h.open_wallet()

		if self.cfg.tx_relay_daemon:
			await self.c.stop_daemon()
			self.c = self.get_relay_rpc()
			self.c.start_daemon()
			h = MoneroWalletRPC(self, self.kal.entry(tx.src_wallet_idx))
			h.open_wallet('TX-relay-configured watch-only', refresh=False)

		msg('\n' + tx.get_info(indent='    '))

		if self.cfg.tx_relay_daemon:
			self.display_tx_relay_info(indent='    ')

		keypress_confirm(self.cfg, f'{self.name.capitalize()} transaction?', do_exit=True)

		if self.cfg.tx_relay_daemon:
			msg_r('Relaying transaction to remote daemon, please be patient...')
			t_start = time.time()
		res = self.c.call(
			'submit_transfer',
			tx_data_hex = tx.data.signed_txset)
		assert res['tx_hash_list'][0] == tx.data.txid, 'TxID mismatch in ‘submit_transfer’ result!'
		if self.cfg.tx_relay_daemon:
			from ...util2 import format_elapsed_hr
			msg(f'success\nRelay time: {format_elapsed_hr(t_start, rel_now=False, show_secs=True)}')

		new_tx = self.get_tx_cls('NewSubmitted')(cfg=self.cfg, _in_tx=tx)

		gmsg('\nOK')
		new_tx.write(
			ask_write     = not self.cfg.autosign,
			ask_overwrite = not self.cfg.autosign)
		return new_tx

class OpResubmit(OpSubmit):
	action = 'resubmitting transaction with'

	def check_uopts(self):
		if not self.cfg.autosign:
			die(1, '--autosign is required for this operation')

	def get_tx(self):
		from ...autosign import Signable
		fns = Signable.xmr_transaction(self.asi).get_submitted()
		cls = self.get_tx_cls('Submitted')
		return sorted((cls(self.cfg, Path(fn)) for fn in fns),
			key = lambda x: getattr(x.data, 'submit_time', None) or x.data.create_time)[-1]

class OpAbort(OpBase):
	opts = ('watch_only', 'autosign')

	def __init__(self, cfg, uarg_tuple):
		super().__init__(cfg, uarg_tuple)
		self.mount_removable_device()
		from ...autosign import Signable
		Signable.xmr_transaction(self.asi).shred_abortable() # prompts user, then raises exception or exits
