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
proto.eth.tx.status: Ethereum transaction status class
"""

from ....tx import status as TxBase
from ....util import msg, die, suf, capfirst

class Status(TxBase.Status):

	async def display(self, usr_req=False):

		tx = self.tx

		async def is_in_mempool():
			if not 'full_node' in tx.rpc.caps:
				return False
			if tx.rpc.daemon.id in ('parity', 'openethereum'):
				pool = [x['hash'] for x in await tx.rpc.call('parity_pendingTransactions')]
			elif tx.rpc.daemon.id in ('geth', 'erigon'):
				res = await tx.rpc.call('txpool_content')
				pool = list(res['pending']) + list(res['queued'])
			return '0x'+tx.coin_txid in pool

		async def is_in_wallet():
			d = await tx.rpc.call('eth_getTransactionReceipt', '0x'+tx.coin_txid)
			if d and 'blockNumber' in d and d['blockNumber'] is not None:
				from collections import namedtuple
				receipt_info = namedtuple('receipt_info', ['confs', 'exec_status'])
				return receipt_info(
					confs       = 1 + int(await tx.rpc.call('eth_blockNumber'), 16) - int(d['blockNumber'], 16),
					exec_status = int(d['status'], 16)
				)

		if await is_in_mempool():
			msg(
				'Transaction is in mempool' if usr_req else
				'Warning: transaction is in mempool!')
			return

		if usr_req:
			ret = await is_in_wallet()
			if ret:
				if tx.txobj['data']:
					cd = capfirst(tx.contract_desc)
					if ret.exec_status == 0:
						msg(f'{cd} failed to execute!')
					else:
						msg(f'{cd} successfully executed with status {ret.exec_status}')
				die(0, f'Transaction has {ret.confs} confirmation{suf(ret.confs)}')
			die(1, 'Transaction is neither in mempool nor blockchain!')

class TokenStatus(Status):
	pass
