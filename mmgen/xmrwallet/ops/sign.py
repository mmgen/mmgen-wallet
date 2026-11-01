# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
xmrwallet.ops.sign: Monero wallet ops for the MMGen Suite
"""

from pathlib import Path
from ..rpc import MoneroWalletRPC

from .wallet import OpWallet

class OpSign(OpWallet):
	action = 'signing transaction with'
	stem = 'process'
	return_data = True
	main_starts_daemon = True

	async def process_wallet(self, d, fn, last):
		h = MoneroWalletRPC(self, d)
		h.open_wallet(refresh=False)
		self.head_msg(d.idx, h.fn)
		tx = self.get_tx_cls('Unsigned')(self.cfg, Path(self.uargs.spec))
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
		if self.compat_call:
			return new_tx.make_outer_data()
		return new_tx
