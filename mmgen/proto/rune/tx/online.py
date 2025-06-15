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
proto.rune.tx.online: THORChain online signed transaction class
"""

from ....util import msg, pp_msg, die
from ....tx import online as TxBase

from .signed import Signed

class OnlineSigned(Signed, TxBase.OnlineSigned):

	async def test_sendable(self, txhex):
		res = self.rpc.tx_op(txhex, op='check_tx')
		if res['code'] == 0:
			return True
		else:
			pp_msg(res)
			return False

	async def send_checks(self):
		pass

	async def send_with_node(self, txhex):
		res = self.rpc.tx_op(txhex, op='broadcast_tx_sync') # broadcast_tx_async
		if res['code'] == 0:
			return res['hash'].lower()
		else:
			pp_msg(res)
			die(2, 'Transaction send failed')

	async def post_network_send(self, coin_txid):
		return True

	async def get_receipt(self, txid, *, receipt_only=False):
		try:
			return self.rpc.get_tx_info(txid)
		except Exception as e:
			msg(f'{type(e).__name__}: {e}')
			return False

class Sent(TxBase.Sent, OnlineSigned):
	pass

class AutomountOnlineSigned(TxBase.AutomountOnlineSigned, OnlineSigned):
	pass

class AutomountSent(TxBase.AutomountSent, AutomountOnlineSigned):
	pass
