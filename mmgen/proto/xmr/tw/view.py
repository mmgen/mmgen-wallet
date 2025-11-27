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

from collections import namedtuple

from ....xmrwallet import op as xmrwallet_op
from ....seed import SeedID
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

		if wallets_data:
			self.sid = SeedID(sid=wallets_data[0]['seed_id'])

		self.total = self.unlocked_total = self.proto.coin_amt('0')

		def gen_addrs():
			bd = namedtuple('address_balance_data', ['bal', 'unlocked_bal', 'blocks_to_unlock'])
			for wdata in wallets_data:
				bals_data = {i: {} for i in range(len(wdata['data'].accts_data['subaddress_accounts']))}

				for d in wdata['data'].bals_data.get('per_subaddress', []):
					bals_data[d['account_index']].update({
						d['address_index']: bd(
							d['balance'],
							d['unlocked_balance'],
							d['blocks_to_unlock'])})

				for acct_idx, acct_data in enumerate(wdata['data'].addrs_data):
					for addr_data in acct_data['addresses']:
						addr_idx = addr_data['address_index']
						addr_bals = bals_data[acct_idx].get(addr_idx)
						bal = self.proto.coin_amt(
							addr_bals.bal if addr_bals else 0,
							from_unit = 'atomic')
						unlocked_bal = self.proto.coin_amt(
							addr_bals.unlocked_bal if addr_bals else 0,
							from_unit = 'atomic')
						if bal or self.include_empty:
							self.total += bal
							self.unlocked_total += unlocked_bal
							mmid = '{}:M:{}-{}/{}'.format(
								wdata['seed_id'],
								wdata['wallet_num'],
								acct_idx,
								addr_idx)
							btu = addr_bals.blocks_to_unlock if addr_bals else 0
							if not btu and bal != unlocked_bal:
								btu = 12
							yield (TwMMGenID(self.proto, mmid), {
								'addr':    addr_data['address'],
								'amt':     bal,
								'unlocked_amt': unlocked_bal,
								'recvd':   bal,
								'is_used': addr_data['used'],
								'confs':   11 - btu,
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
