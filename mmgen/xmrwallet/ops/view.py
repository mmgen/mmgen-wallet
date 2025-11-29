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
xmrwallet.ops.view: Monero wallet ops for the MMGen Suite
"""

from ...color import green
from ...util import msg, ymsg

from ..include import gen_acct_addr_info
from ..rpc import MoneroWalletRPC

from .sync import OpSync

class OpList(OpSync):
	stem = 'sync'

	def gen_body(self, wallets_data):
		for (wallet_fn, wallet_data) in wallets_data.items():
			ad = wallet_data.accts_data['subaddress_accounts']
			yield green(f'Wallet {wallet_fn}:')
			for account in range(len(wallet_data.addrs_data)):
				bal = ad[account]['unlocked_balance']
				if self.cfg.skip_empty_accounts and not bal:
					continue
				yield ''
				yield '  Account #{a} [{b} {c}]'.format(
					a = account,
					b = self.proto.coin_amt(bal, from_unit='atomic').hl(),
					c = self.proto.coin_amt.hlc('XMR'))
				yield from gen_acct_addr_info(self, wallet_data, account, indent='  ')

			yield ''

class OpView(OpSync):
	stem = 'open'
	opts = ()
	wallet_offline = True

	def pre_init_action(self):
		ymsg('Running in offline mode. Balances may be out of date!')

	async def process_wallet(self, d, fn, last):

		self.c.call(
			'open_wallet',
			filename = fn.name,
			password = d.wallet_passwd)

		wallet_height = self.c.call('get_height')['height']
		msg(f'  Wallet height: {wallet_height}')

		self.wallets_data[fn.name] = MoneroWalletRPC(self, d).get_wallet_data(
			print = False,
			skip_empty_ok = True)

		if not last:
			self.c.call('close_wallet')

		return True

class OpListview(OpView, OpList):
	pass
