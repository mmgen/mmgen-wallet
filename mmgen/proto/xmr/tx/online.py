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

from ....xmrwallet import op as xmrwallet_op
from ....tx.online import OnlineSigned as TxOnlineSigned
from .completed import Completed

class OnlineSigned(Completed, TxOnlineSigned):

	async def post_network_send(self, coin_txid):
		return True

	async def check_memoless_presend(self):
		return await super().check_memoless_presend(amt=self.send_amt)

	async def send_with_node(self, txhex):
		op = xmrwallet_op('submit', self.cfg, self.infile, None, compat_call=True)
		await op.restart_wallet_daemon()
		self.compat_data = await op.main()
		return self.compat_data['data']['txid']

class AutomountOnlineSigned(OnlineSigned):
	desc = 'signed automount transaction'
	ext = 'asigtx'

class Sent(OnlineSigned):
	desc = 'sent transaction'
	ext = 'asubtx'

class AutomountSent(OnlineSigned):
	desc = 'sent automount transaction'
	ext = 'asubtx'
