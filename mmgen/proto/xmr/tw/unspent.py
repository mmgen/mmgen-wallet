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
proto.xmr.tw.unspent: Monero protocol tracking wallet unspent outputs class
"""

from ....tw.unspent import TwUnspentOutputs

from .view import MoneroTwView

class MoneroTwUnspentOutputs(MoneroTwView, TwUnspentOutputs):

	hdr_lbl = 'spendable accounts'
	desc = 'spendable accounts'

	async def __init__(self, cfg, proto, *, minconf=1, addrs=[], tx=None):
		self.prompt_fs_in = [
			'Sort options: [a]mount, [A]ge, a[d]dr, [M]mgen addr, [r]everse',
			'View/Print: pager [v]iew, [w]ide pager view, [p]rint to file{s}',
			'Actions: [q]uit menu, add [l]abel, r[e]draw, [R]efresh balances:']
		self.extra_key_mappings = {
			'R': 'a_sync_wallets',
			'\x12': 'a_sync_wallets',
			'A': 's_age'}
		if tx and tx.is_sweep:
			self.prompt_fs_in[-1] = 'Actions: [q]uit, add [l]abel, r[e]draw, [R]efresh balances:'
			self.prompt_fs_in.insert(-1, 'Transaction ops: [s]weep to address, [S]weep to account')
			self.extra_key_mappings.update({
				's': 'i_addr_sweep',
				'S': 'i_acct_sweep'})
		await super().__init__(cfg, proto, minconf=minconf, addrs=addrs, tx=tx)
		self.is_sweep = self.include_empty = self.tx and self.tx.is_sweep

	async def get_idx_from_user(self, method_name):
		if method_name in ('i_acct_sweep', 'i_addr_sweep'):
			from collections import namedtuple
			ret = []
			for acct_desc in {
					'i_acct_sweep': ['source', 'destination'],
					'i_addr_sweep': ['source']}[method_name]:
				if res := await self.get_idx(f'{acct_desc} account number', self.accts_data):
					ret.append(res)
				else:
					return None
			return namedtuple('usr_idx_data', 'idx acct_addr_idx', defaults=[None])(*ret)
		else:
			return await super().get_idx_from_user(method_name)

	class item_action(TwUnspentOutputs.item_action):
		acct_methods = ('i_acct_sweep', 'i_addr_sweep')

		async def i_acct_sweep(self, parent, idx, acct_addr_idx=None):
			d = parent.accts_data
			d1 = d[idx.idx - 1]
			d2 = d[acct_addr_idx.idx - 1]
			parent.tx.sweep_spec = f'{d1.idx}:{d1.acct_idx},{d2.idx}:{d2.acct_idx}'
			return 'quit_view'

		async def i_addr_sweep(self, parent, idx, acct_addr_idx=None):
			d = parent.accts_data[idx.idx - 1]
			parent.tx.sweep_spec = f'{d.idx}:{d.acct_idx}'
			return 'quit_view'
