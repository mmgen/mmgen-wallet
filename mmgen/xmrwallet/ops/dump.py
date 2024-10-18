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
xmrwallet.ops.dump: Monero wallet ops for the MMGen Suite
"""

from ...util import msg

from ..file.outputs import MoneroWalletDumpFile
from ..rpc import MoneroWalletRPC

from .wallet import OpWallet

class OpDump(OpWallet):
	wallet_offline = True

	async def process_wallet(self, d, fn, last):
		h = MoneroWalletRPC(self, d)
		h.open_wallet('source')
		wallet_data = h.get_wallet_data(print=False)
		msg('')
		MoneroWalletDumpFile.New(
			parent    = self,
			wallet_fn = fn,
			data      = {'wallet_metadata': wallet_data.addrs_data}
		).write()
		return True
