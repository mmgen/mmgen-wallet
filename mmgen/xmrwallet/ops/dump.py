# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
xmrwallet.ops.dump: Monero wallet ops for the MMGen Suite
"""

from ...util import msg, Msg, gmsg

from ..file.outputs import MoneroWalletDumpFile

from .wallet import OpWallet

class OpDump(OpWallet):
	wallet_offline = True
	wallet_desc = 'source'

	async def process_wallet(self, d, h, last):
		wallet_data = h.get_wallet_data(print=False)
		msg('')
		MoneroWalletDumpFile.New(
			parent    = self,
			wallet_fn = h.fn,
			data      = {'wallet_metadata': wallet_data.addrs_data}
		).write()
		return True

class OpDumpDataCommon(OpWallet):
	return_data = True
	wallet_desc = 'source'
	skip_refresh = True

	async def process_wallet(self, d, h, last):

		if (height := self.c.call('get_height')['height']) > 1:
			from requests.exceptions import ConnectionError
			blockcount = height - 1
			dc = self.get_coin_daemon_rpc(test_connection=False)
			try:
				timestamp = dc.call('getblock', height=blockcount)['block_header']['timestamp']
			except ConnectionError:
				timestamp = None
		else:
			blockcount = 0
			timestamp = None

		return {
			'seed_id': self.kal.al_id.sid,
			'wallet_num': d.idx,
			'blockcount': blockcount,
			'timestamp': timestamp,
			'data': h.get_wallet_data(print=False)}

	def post_main_success(self):
		pass

class OpDumpData(OpDumpDataCommon):
	start_daemon = False
	stem = 'load'

class OpDumpDataRefresh(OpDumpData):

	async def process_wallet(self, d, h, last):
		self.wd.test_monerod_port() # raises SocketError on fail, handled by caller
		gmsg('  Refreshing wallet')
		self.c.call('refresh')
		return await super().process_wallet(d, h, last)

class OpDumpJson(OpDumpDataCommon):
	stem = 'dump'

	async def main(self):
		import json
		data = await super().main()
		Msg(json.dumps(data))
		return sum(map(bool, data))
