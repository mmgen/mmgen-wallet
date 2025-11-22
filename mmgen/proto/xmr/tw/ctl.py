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
proto.xmr.tw.ctl: Monero tracking wallet control class
"""

from ....tw.ctl import write_mode
from ....tw.store import TwCtlWithStore

class MoneroTwCtl(TwCtlWithStore):

	tw_subdir = 'tracking-wallets'
	use_cached_balances = True

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
		await op.restart_wallet_daemon()
		return await op.main(add_timestr=add_timestr, auto=True)
