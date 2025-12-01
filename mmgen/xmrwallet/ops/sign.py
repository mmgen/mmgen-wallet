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
xmrwallet.ops.sign: Monero wallet ops for the MMGen Suite
"""

from ..rpc import MoneroWalletRPC

from .wallet import OpWallet

class OpSign(OpWallet):
	action = 'signing transaction with'
	start_daemon = False

	async def main(self, fn, *, restart_daemon=True):
		if restart_daemon:
			await self.restart_wallet_daemon()
		tx = self.get_tx_cls('Unsigned')(self.cfg, fn)
		h = MoneroWalletRPC(self, self.addr_data[0])
		self.head_msg(tx.src_wallet_idx, h.fn)
		if restart_daemon:
			h.open_wallet(refresh=False)
		res = self.c.call(
			'sign_transfer',
			unsigned_txset = tx.data.unsigned_txset,
			export_raw = True,
			get_tx_keys = True)
		new_tx = self.get_tx_cls('NewColdSigned')(
			cfg            = self.cfg,
			txid           = res['tx_hash_list'][0],
			unsigned_txset = None,
			signed_txset   = res['signed_txset'],
			_in_tx         = tx)
		return new_tx
