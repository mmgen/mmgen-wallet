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
xmrwallet.ops.sweep: Monero wallet ops for the MMGen Suite
"""

from ...util import msg, msg_r, gmsg, die, fmt_dict, make_timestr
from ...proto.xmr.rpc import MoneroWalletRPCClient
from ...proto.xmr.daemon import MoneroWalletDaemon
from ...ui import keypress_confirm

from .. import tx_priorities
from ..rpc import MoneroWalletRPC

from .spec import OpMixinSpec
from .wallet import OpWallet

class OpSweep(OpMixinSpec, OpWallet):
	spec_id  = 'sweep_spec'
	spec_key = ((1, 'source'), (3, 'dest'))
	opts = (
		'no_relay',
		'tx_relay_daemon',
		'watch_only',
		'priority',
		'skip_empty_accounts',
		'skip_empty_addresses')
	sweep_type = 'single-address'

	def check_uopts(self):
		if self.cfg.tx_relay_daemon and (self.cfg.no_relay or self.cfg.autosign):
			die(1, '--tx-relay-daemon makes no sense in this context!')

		if self.cfg.priority and self.cfg.priority not in list(tx_priorities):
			die(1, '{}: invalid parameter for --priority (valid params: {})'.format(
				self.cfg.priority,
				fmt_dict(tx_priorities, fmt='square_compact')))

	def init_tx_relay_daemon(self):

		m = self.parse_tx_relay_opt()

		wd2 = MoneroWalletDaemon(
			cfg         = self.cfg,
			proto       = self.proto,
			wallet_dir  = self.cfg.wallet_dir or '.',
			test_suite  = self.cfg.test_suite,
			monerod_addr = m[1],
			proxy       = m[2])

		if self.cfg.test_suite:
			wd2.usr_daemon_args = ['--daemon-ssl-allow-any-cert']

		wd2.start()

		self.c = MoneroWalletRPCClient(
			cfg    = self.cfg,
			daemon = wd2)

	def create_tx(self, h, wallet_data):

		def create_new_addr_maybe(h, account, label):
			if keypress_confirm(self.cfg, f'\nCreate new address for account #{account}?'):
				return h.create_new_addr(account, label)
			else:
				keypress_confirm(
					self.cfg,
					f'Sweep to last existing address of account #{account}?',
					do_exit = True)
				return None

		dest_addr_chk = None

		if self.dest is None: # sweep to same account
			dest_acct = self.account
			dest_addr_chk = create_new_addr_maybe(
				h, self.account, f'{self.name} from this account [{make_timestr()}]')
			if dest_addr_chk:
				wallet_data = h.get_wallet_data(print=False)
			dest_addr, dest_addr_idx = h.get_last_addr(
				self.account,
				wallet_data,
				display = not dest_addr_chk)
			if dest_addr_chk:
				h.print_acct_addrs(wallet_data, self.account)
		elif self.dest_acct is None: # sweep to wallet
			h.close_wallet('source')
			h2 = MoneroWalletRPC(self, self.dest)
			h2.open_wallet('destination')
			wallet_data2 = h2.get_wallet_data()

			wf = self.get_wallet_fn(self.dest)
			if keypress_confirm(self.cfg, f'\nCreate new account for wallet {wf.name!r}?'):
				dest_acct, dest_addr = h2.create_acct(
					label = f'{self.name} from {self.source.idx}:{self.account} [{make_timestr()}]')
				dest_addr_idx = 0
				h2.get_wallet_data()
			else:
				keypress_confirm(
					self.cfg,
					f'Sweep to last existing account of wallet {wf.name!r}?',
					do_exit = True)
				dest_acct, dest_addr_chk = h2.get_last_acct(wallet_data2.accts_data)
				dest_addr, dest_addr_idx = h2.get_last_addr(dest_acct, wallet_data2, display=False)

			h2.close_wallet('destination')
			h.open_wallet('source', refresh=False)
		else: # sweep to specific account of wallet

			def get_dest_addr_params(h, wallet_data, dest_acct, label):
				self.check_account_exists(wallet_data.accts_data, dest_acct)
				h.print_acct_addrs(wallet_data, dest_acct)
				dest_addr_chk = create_new_addr_maybe(h, dest_acct, label)
				if dest_addr_chk:
					wallet_data = h.get_wallet_data(print=False)
				dest_addr, dest_addr_idx = h.get_last_addr(
					dest_acct,
					wallet_data,
					display = not dest_addr_chk)
				if dest_addr_chk:
					h.print_acct_addrs(wallet_data, dest_acct)
				return dest_addr, dest_addr_idx, dest_addr_chk

			dest_acct = self.dest_acct

			if self.dest == self.source:
				dest_addr, dest_addr_idx, dest_addr_chk = get_dest_addr_params(
					h, wallet_data, dest_acct,
					f'{self.name} from account #{self.account} [{make_timestr()}]')
			else:
				h.close_wallet('source')
				h2 = MoneroWalletRPC(self, self.dest)
				h2.open_wallet('destination')
				dest_addr, dest_addr_idx, dest_addr_chk = get_dest_addr_params(
					h2, h2.get_wallet_data(), dest_acct,
					f'{self.name} from {self.source.idx}:{self.account} [{make_timestr()}]')
				h2.close_wallet('destination')
				h.open_wallet('source', refresh=False)

		assert dest_addr_chk in (None, dest_addr), (
			f'dest_addr: ({dest_addr}) != dest_addr_chk: ({dest_addr_chk})')

		msg(f'\n    Creating {self.name} transaction...')
		return (h, h.make_sweep_tx(
			self.account,
			dest_acct,
			dest_addr_idx,
			dest_addr,
			wallet_data.addrs_data))

	@property
	def add_desc(self):
		return (
			r' to new address' if self.dest is None else
			f' to new account in wallet {self.dest.idx}' if self.dest_acct is None else
			f' to account #{self.dest_acct} of wallet {self.dest.idx}') + f' ({self.sweep_type} sweep)'

	def check_account_exists(self, accts_data, idx):
		max_acct = len(accts_data['subaddress_accounts']) - 1
		if self.account > max_acct:
			die(2, f'{self.account}: requested account index out of bounds (>{max_acct})')

	async def main(self):
		if not self.compat_call:
			gmsg(
				f'\n{self.stem.capitalize()}ing account #{self.account}'
				f' of wallet {self.source.idx}{self.add_desc}')

		h = MoneroWalletRPC(self, self.source)

		h.open_wallet('source')

		wallet_data = h.get_wallet_data(skip_empty_ok=True)

		self.check_account_exists(wallet_data.accts_data, self.account)

		h.print_acct_addrs(wallet_data, self.account)

		h, new_tx = self.create_tx(h, wallet_data)

		msg('\n' + new_tx.get_info(indent='    '))

		if self.cfg.tx_relay_daemon:
			self.display_tx_relay_info(indent='    ')

		if not self.compat_call:
			msg('Saving TX data to file')

		new_tx.write(delete_metadata=True)

		if self.cfg.no_relay or self.cfg.autosign:
			return True

		keypress_confirm(
			self.cfg,
			f'Relay {self.name} transaction?',
			do_exit = True,
			exit_msg = '\nExiting at user request')

		if self.cfg.tx_relay_daemon:
			await h.stop_wallet('source')
			msg('')
			self.init_tx_relay_daemon()
			h = MoneroWalletRPC(self, self.source)
			h.open_wallet('TX-relay-configured source', refresh=False)
		msg_r(f'\n    Relaying {self.name} transaction...')
		h.relay_tx(new_tx.data.metadata)
		gmsg('\nAll done')
		return True

class OpSweepAll(OpSweep):
	stem = 'sweep'
	sweep_type = 'all-address'

class OpTransfer(OpSweep):
	stem    = 'transferr'
	spec_id = 'transfer_spec'
	spec_key = ((1, 'source'),)

	@property
	def add_desc(self):
		return f': {self.amount} XMR to {self.dest_addr}'

	def create_tx(self, h, wallet_data):
		msg(f'\n    Creating {self.name} transaction...')
		return (h, h.make_transfer_tx(self.account, self.dest_addr, self.amount))
