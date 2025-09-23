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
proto.eth.tx.status: Ethereum transaction status class
"""

from ....tx import status as TxBase
from ....util import msg, suf, capfirst

class Status(TxBase.Status):

	async def display(self, *, idx=''):

		def do_return(exitval, message):
			if message:
				msg(message)
			return exitval

		tx = self.tx
		coin_txid = '0x' + getattr(tx, f'coin_txid{idx}')
		tx_desc = 'transaction' + (f' {idx}' if idx else '')

		async def is_in_mempool():
			if not 'full_node' in tx.rpc.caps:
				return False
			match tx.rpc.daemon.id:
				case 'parity' | 'openethereum':
					return coin_txid in [x['hash'] for x in await tx.rpc.call('parity_pendingTransactions')]
				case 'geth' | 'reth' | 'erigon':
					def gen(key):
						for e in res[key].values():
							for v in e.values():
								yield v['hash']
					res = await tx.rpc.call('txpool_content')
					return coin_txid in list(gen('queued')) + list(gen('pending'))

		async def is_in_wallet():
			d = await tx.rpc.call('eth_getTransactionReceipt', coin_txid)
			if d and 'blockNumber' in d and d['blockNumber'] is not None:
				from collections import namedtuple
				receipt_info = namedtuple('receipt_info', ['confs', 'exec_status', 'rx'])
				return receipt_info(
					confs = 1 + int(await tx.rpc.call('eth_blockNumber'), 16) - int(d['blockNumber'], 16),
					exec_status = int(d['status'], 16),
					rx = d)

		if await is_in_mempool():
			return do_return(0, f'{capfirst(tx_desc)} is in mempool')

		if res := await is_in_wallet():
			if tx.txobj['data'] and not tx.is_swap:
				cd = capfirst(tx.contract_desc)
				msg(f'{cd} failed to execute!' if res.exec_status == 0 else
					f'{cd} successfully executed with status {res.exec_status}')
			return do_return(
				int(not res.exec_status),
				f'{capfirst(tx_desc)} has {res.confs} confirmation{suf(res.confs)}')

		return do_return(1, f'{capfirst(tx_desc)} is neither in mempool nor blockchain!')

class TokenStatus(Status):
	pass
