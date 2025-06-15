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
proto.rune.tx.status: THORChain transaction status class
"""

from ....util import msg, gmsg
from ....tx import status as TxBase

class Status(TxBase.Status):

	async def display(self, *, idx=''):

		try:
			self.tx.rpc.get_tx_info(self.tx.coin_txid)
		except Exception as e:
			msg(f'{type(e).__name__}: {e}')
			return 2

		gmsg('Transaction is in blockchain')
		return 0
