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
proto.xmr.tw.addresses: Monero protocol tracking wallet address list class
"""

from ....tw.addresses import TwAddresses

from .view import MoneroTwView

async def add_new_address(parent, spec, ok_msg):
	from ....color import green, yellow
	from ....xmrwallet import op as xmrwallet_op
	lbl, add_timestr = parent.get_label_from_user()
	op = xmrwallet_op(
		'new',
		parent.cfg,
		None,
		None,
		spec = spec + (',' + lbl if lbl else ''),
		compat_call = True)
	op.c.call('close_wallet')
	if await op.main(add_timestr=add_timestr):
		await parent.get_data()
		parent.oneshot_msg = green(ok_msg)
		return 'redraw'
	else:
		parent.oneshot_msg = yellow('Operation cancelled')
		return False

class MoneroTwAddresses(MoneroTwView, TwAddresses):

	include_empty = True
	has_used = True

	prompt_fs_repl = {'XMR': (
		(1, 'Filters: show [E]mpty addrs, [u]sed addrs, all [L]abels'),
		(3, 'Actions: [q]uit menu, add [l]abel, [N]ew acct, [n]ew addr, [R]efresh bals:'))}
	extra_key_mappings = {
		'N': 'a_acct_new',
		'n': 'i_addr_new',
		'u': 'd_showused',
		'R': 'a_sync_wallets'}
	removed_key_mappings = {
		'D': 'i_addr_delete'}

	class display_type:

		class squeezed(MoneroTwView.display_type.squeezed):
			cols = ('addr_idx', 'addr', 'used', 'comment', 'amt')

		class detail(MoneroTwView.display_type.detail):
			cols = ('addr_idx', 'addr', 'used', 'amt', 'comment')

	def get_disp_data(self):
		return MoneroTwView.get_disp_data(self, input_data=tuple(TwAddresses.get_disp_data(self)))

	class action(MoneroTwView.action):

		async def a_acct_new(self, parent):
			if res := parent.choose_wallet('Choose a wallet to add a new account to'):
				return await add_new_address(
					parent,
					str(res.item[0]),
					f'New account added to wallet {parent.make_wallet_id(res.item[0]).hl()}')
			else:
				return 'erase'

	class item_action(TwAddresses.item_action):
		acct_methods = ('i_addr_new')

		async def i_addr_new(self, parent, idx, acct_addr_idx=None):
			e = parent.accts_data[idx-1]
			return await add_new_address(
				parent,
				f'{e.idx}:{e.acct_idx}',
				f'New address added to wallet {e.idx}, account #{e.acct_idx}')
