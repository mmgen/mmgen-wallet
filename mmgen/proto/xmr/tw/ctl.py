# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.xmr.tw.ctl: Monero tracking wallet control class
"""

from ....addr import CoinAddr
from ....tw.shared import TwLabel
from ....tw.ctl import TwCtl, write_mode, label_addr_pair
from ....tw.addresses import TwAddresses

class MoneroTwCtl(TwCtl):

	use_cached_balances = True

	async def __init__(self, cfg, proto, *, mode='r', **kwargs):
		await super().__init__(cfg, proto, mode=mode, no_rpc=True)

	@classmethod
	def get_tw_dir(cls, proto):
		return proto.network_datadir / 'tracking-wallets'

	@write_mode
	async def set_comment(
			self,
			addrspec,
			comment      = '',
			*,
			trusted_pair = None,
			silent       = False):

		from ....ui import keypress_confirm
		add_timestr = keypress_confirm(self.cfg, 'Add timestamp to label?')

		m = trusted_pair[0].obj
		from ....xmrwallet import op as xmrwallet_op
		op = xmrwallet_op(
			'label',
			self.cfg,
			None,
			None,
			spec = f'{m.idx}:{m.acct_idx}:{m.addr_idx},{comment}',
			compat_call = True)
		op.c.call('close_wallet')
		return await op.main(add_timestr=add_timestr)

	async def get_label_addr_pairs(self):
		twaddrs = await TwAddresses(self.cfg, self.proto, add_twctl=False)
		rpc_data = await twaddrs.get_rpc_data()
		return [label_addr_pair(
				TwLabel(self.proto, k),
				CoinAddr(self.proto, v['addr'])
			) for k, v in rpc_data.items()]
