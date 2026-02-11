#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
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
	desc = 'signed transaction'

	async def compat_send(self):
		"""
		returns integer exit val to system
		"""
		from ....xmrwallet import op as xmrwallet_op
		op_name = 'daemon' if self.cfg.status else 'submit'
		op = xmrwallet_op(op_name, self.cfg, self.filename, None, compat_call=True)
		if self.cfg.status:
			from ....util import msg, msg_r, ymsg, suf
			ret = 0
			txid = self.compat_tx.data.txid
			if not (self.cfg.verbose or self.cfg.quiet):
				from ....obj import CoinTxID
				msg('{} TxID: {}'.format(self.cfg.coin, CoinTxID(txid).hl()))
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
				ret = 1
			if self.cfg.verbose:
				msg_r('\n' + self.compat_tx.get_info())
			return ret
		else:
			await op.restart_wallet_daemon()
			return int(not await op.main())

class Sent(OnlineSigned):
	desc = 'sent transaction'

class AutomountOnlineSigned(OnlineSigned):
	desc = 'signed automount transaction'

class AutomountSent(AutomountOnlineSigned):
	desc = 'sent automount transaction'
