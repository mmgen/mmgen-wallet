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
proto.rune.tw.ctl: THORChain tracking wallet control class
"""

from ....util import ymsg
from ....tw.store import TwCtlWithStore

class THORChainTwCtl(TwCtlWithStore):

	use_cached_balances = True

	async def rpc_get_balance(self, addr, block='latest'):
		assert self.rpc.is_remote, 'tw.store.rpc_get_balance(): RPC is not remote!'
		try:
			return self.rpc.get_balance(addr, block=block)
		except Exception as e:
			ymsg(f'{type(e).__name__}: {e}')
			ymsg(f'Unable to get balance for address ‘{addr}’')
			if self.get_cached_balance(addr, self.cur_balances, self.data_root):
				from ....ui import keypress_confirm
				if keypress_confirm(self.cfg, 'Zero the balance for this address?'):
					return self.proto.coin_amt('0')
			else:
				import asyncio
				await asyncio.sleep(3)
