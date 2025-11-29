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

class MoneroTwAddresses(MoneroTwView, TwAddresses):

	include_empty = True
	has_used = True

	prompt_fs_repl = {'XMR': (
		(1, 'Filters: show [E]mpty addrs, [u]sed addrs, all [L]abels'),
		(3, 'Actions: [q]uit menu, add [l]abel, [R]efresh balances:'))}
	extra_key_mappings = {
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
