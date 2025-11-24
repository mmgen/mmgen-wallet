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
proto.xmr.tw.view: Monero protocol base class for tracking wallet view classes
"""

from ....xmrwallet import op as xmrwallet_op
from ....tw.view import TwView

class MoneroTwView:

	class rpc:
		caps = ()
		is_remote = False

	async def get_rpc_data(self):
		from mmgen.tw.shared import TwMMGenID, TwLabel

		op = xmrwallet_op('dump_data', self.cfg, None, None, compat_call=True)
		await op.restart_wallet_daemon()
		wallets_data = await op.main()

		self.total = self.proto.coin_amt('0')

		def gen_addrs():
			for wdata in wallets_data:
				bals_data = {i: {} for i in range(len(wdata['data'].accts_data['subaddress_accounts']))}

				for d in wdata['data'].bals_data.get('per_subaddress', []):
					bals_data[d['account_index']].update({d['address_index']: d['unlocked_balance']})

				for acct_idx, acct_data in enumerate(wdata['data'].addrs_data):
					for addr_data in acct_data['addresses']:
						addr_idx = addr_data['address_index']
						self.total += (bal := self.proto.coin_amt(
							bals_data[acct_idx].get(addr_idx, 0),
							from_unit = 'atomic'))
						if self.include_empty or bal:
							mmid = '{}:M:{}-{}/{}'.format(
								wdata['seed_id'],
								wdata['wallet_num'],
								acct_idx,
								addr_idx)
							yield (TwMMGenID(self.proto, mmid), {
								'addr':    addr_data['address'],
								'amt':     bal,
								'recvd':   bal,
								'is_used': addr_data['used'],
								'confs':   1,
								'lbl':     TwLabel(self.proto, mmid + ' ' + addr_data['label'])})

		return dict(gen_addrs())

	class action(TwView.action):

		async def a_sync_wallets(self, parent):
			from ....util import msg, msg_r
			from ....tw.view import CUR_HOME, ERASE_ALL
			msg('')
			op = xmrwallet_op('sync', parent.cfg, None, None, compat_call=True)
			await op.restart_wallet_daemon()
			await op.main()
			await parent.get_data()
			msg_r(CUR_HOME + ERASE_ALL)
