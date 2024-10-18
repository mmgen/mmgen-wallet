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
xmrwallet.ops.new: Monero wallet ops for the MMGen Suite
"""

from ...color import red, pink
from ...util import msg, ymsg, make_timestr

from ...ui import keypress_confirm

from ..rpc import MoneroWalletRPC

from .spec import OpMixinSpec
from .wallet import OpWallet

class OpNew(OpMixinSpec, OpWallet):
	spec_id = 'newaddr_spec'
	spec_key = ((1, 'source'),)
	wallet_offline = True

	async def main(self):
		h = MoneroWalletRPC(self, self.source)
		h.open_wallet('Monero')

		desc = 'account' if self.account is None else 'address'
		label = (
			None if self.label == '' else
			'{} [{}]'.format(self.label or f'xmrwallet new {desc}', make_timestr()))

		wallet_data = h.get_wallet_data()

		if desc == 'address':
			h.print_acct_addrs(wallet_data, self.account)

		if keypress_confirm(
				self.cfg,
				'\nCreating new {a} for wallet {b}{c} with {d}\nOK?'.format(
					a = desc,
					b = red(str(self.source.idx)),
					c = '' if desc == 'account' else f', account {red("#"+str(self.account))}',
					d = 'label ' + pink('‘'+label+'’') if label else 'empty label')
				):

			if desc == 'address':
				h.create_new_addr(self.account, label=label)
			else:
				h.create_acct(label=label)

			wallet_data = h.get_wallet_data(print=desc=='account')

			if desc == 'address':
				h.print_acct_addrs(wallet_data, self.account)
		else:
			ymsg('\nOperation cancelled by user request')

		# wallet must be left open: otherwise the 'stop_wallet' RPC call used to stop the daemon will fail
		if self.cfg.no_stop_wallet_daemon:
			h.close_wallet('Monero')

		msg('')
