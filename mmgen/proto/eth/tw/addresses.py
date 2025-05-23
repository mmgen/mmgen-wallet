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
proto.eth.tw.addresses: Ethereum base protocol tracking wallet address list class
"""

from ....tw.addresses import TwAddresses

from .view import EthereumTwView
from .rpc import EthereumTwRPC

class EthereumTwAddresses(TwAddresses, EthereumTwView, EthereumTwRPC):

	has_age = False
	prompt_fs_in = [
		'Sort options: [a]mt, [M]mgen addr, [r]everse',
		'Filters: show [E]mpty addrs, show all [L]abels',
		'View/Print: pager [v]iew, [w]ide pager view, [p]rint{s}',
		'Actions: [q]uit menu, r[e]draw, [D]elete addr, add [l]abel:']

	def get_column_widths(self, data, *, wide, interactive):

		return self.compute_column_widths(
			widths = { # fixed cols
				'num':  max(2, len(str(len(data)))+1),
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

		self.total = self.proto.coin_amt('0')
		self.minconf = None
		addrs = {}

		used_addrs = self.twctl.used_addrs

		for e in await self.twctl.get_label_addr_pairs():
			bal = await self.twctl.get_balance(e.coinaddr)
			addrs[e.label.mmid] = {
				'addr':  e.coinaddr,
				'amt':   bal,
				'recvd': bal,         # current bal only, CF btc.tw.addresses.get_rpc_data()
				'is_used': bool(bal) or e.coinaddr in used_addrs,
				'confs': 0,
				'lbl':   e.label}
			self.total += bal

		return addrs

class EthereumTokenTwAddresses(EthereumTwAddresses):
	pass
