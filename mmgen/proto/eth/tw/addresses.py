#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.eth.tw.addresses: Ethereum base protocol tracking wallet address list class
"""

from ....tw.addresses import TwAddresses
from .view import EthereumTwView
from .rpc import EthereumTwRPC

class EthereumTwAddresses(TwAddresses,EthereumTwView,EthereumTwRPC):

	has_age = False
	prompt_fs = """
Sort options: [a]mt, [M]mgen addr, [r]everse
Filters: show [E]mpty addrs, show all [L]abels
View/Print: pager [v]iew, [w]ide pager view, [p]rint{s}
Actions: [q]uit menu, r[e]draw, [D]elete addr, add [l]abel:
"""
	key_mappings = {
		'a':'s_amt',
		'M':'s_twmmid',
		'r':'s_reverse',
		'e':'d_redraw',
		'E':'d_showempty',
		'L':'d_all_labels',
		'l':'i_comment_add',
		'D':'i_addr_delete',
		'v':'a_view',
		'w':'a_view_detail',
		'p':'a_print_detail' }

	def get_column_widths(self,data,wide,interactive):

		return self.compute_column_widths(
			widths = { # fixed cols
				'num':  max(2,len(str(len(data)))+1),
				'mmid': max(len(d.twmmid.disp) for d in data),
				'used': 0,
				'amt':  self.amt_widths['amt'],
				'date': 0,
				'block': 0,
				'date_time': 0,
				'spc':  5, # 4 spaces between cols + 1 leading space in fs
			},
			maxws = { # expandable cols
				'addr':    max(len(d.addr) for d in data) if self.showcoinaddrs else 0,
				'comment': max(d.comment.screen_width for d in data),
			},
			minws = {
				'addr': 12 if self.showcoinaddrs else 0,
				'comment': len('Comment'),
			},
			maxws_nice = {'addr': 18},
			wide = wide,
			interactive = interactive,
		)

	async def get_rpc_data(self):

		amt0 = self.proto.coin_amt('0')
		self.total = amt0
		self.minconf = None
		addrs = {}

		for label,addr in await self.get_addr_label_pairs():
			bal = await self.twctl.get_balance(addr)
			addrs[label.mmid] = {
				'addr':  addr,
				'amt':   bal,
				'recvd': amt0,
				'confs': 0,
				'lbl':   label }
			self.total += bal

		return addrs

class EthereumTokenTwAddresses(EthereumTwAddresses):
	pass
