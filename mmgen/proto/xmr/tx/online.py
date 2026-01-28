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
proto.xmr.tx.online: Monero online signed transaction class
"""

from .completed import Completed

class OnlineSigned(Completed):

	async def compat_send(self):
		from ....xmrwallet import op as xmrwallet_op
		op_name = 'daemon' if self.cfg.status else 'submit'
		op = xmrwallet_op(op_name, self.cfg, self.filename, None, compat_call=True)
		if self.cfg.status:
			from ....util import msg, ymsg, suf
			txid = self.compat_tx.data.txid
			if self.cfg.verbose:
				msg(self.compat_tx.get_info())
			elif not self.cfg.quiet:
				from ....obj import CoinTxID
				msg('TxID: {}'.format(CoinTxID(txid).hl()))
			res = op.dc.call_raw('get_transactions', txs_hashes=[txid])
			if res['status'] == 'OK':
				tx = res['txs'][0]
				if tx['in_pool']:
					msg('Transaction is in mempool')
				else:
					confs = tx['confirmations']
					msg('Transaction has {} confirmation{}'.format(confs, suf(confs)))
			else:
				ymsg('An RPC error occurred while fetching transaction data')
				return False
		else:
			await op.restart_wallet_daemon()
			return await op.main()

class Sent(OnlineSigned):
	pass

class AutomountOnlineSigned(OnlineSigned):
	pass

class AutomountSent(AutomountOnlineSigned):
	pass
