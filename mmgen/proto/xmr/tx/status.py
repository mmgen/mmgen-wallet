# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.xmr.tx.status: Monero transaction status class
"""

from ....util import msg, ymsg, suf
from ....tx import status as TxBase
from ....xmrwallet import op as xmrwallet_op

class Status(TxBase.Status):

	async def display(self, *, idx=''):
		tx = self.tx
		if tx.cfg.verbose:
			msg(f'{tx.proto.coin} TxID: {tx.coin_txid.hl()}')
		op = xmrwallet_op('daemon', tx.cfg, tx.infile, None, compat_call=True)
		res = op.dc.call_raw('get_transactions', txs_hashes=[tx.coin_txid])
		if res['status'] == 'OK':
			data = res['txs'][0]
			if data['in_pool']:
				msg('Transaction is in mempool')
			else:
				confs = data['confirmations']
				msg(f'Transaction has {confs} confirmation{suf(confs)}')
		else:
			ymsg('An RPC error occurred while fetching transaction data')
			return 1
		return 0
