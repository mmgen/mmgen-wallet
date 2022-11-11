#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
proto.eth.tw.addresses: Ethereum base protocol tracking wallet address list class
"""

from ....tw.addresses import TwAddresses
from ....tw.ctl import TrackingWallet
from ....addr import CoinAddr
from .common import EthereumTwCommon

class EthereumTwAddresses(EthereumTwCommon,TwAddresses):

	has_age = False
	prompt = """
Sort options: [a]mt, [M]mid, [r]everse
Filters: show [E]mpty addrs, all [L]abels
View/Print: pager [v]iew, [w]ide view, [p]rint
Actions: [q]uit, r[e]draw, [D]elete address, add [l]abel:
"""
	key_mappings = {
		'a':'s_amt',
		'M':'s_twmmid',
		'r':'d_reverse',
		'e':'d_redraw',
		'E':'d_showempty',
		'L':'d_all_labels',
		'q':'a_quit',
		'l':'a_comment_add',
		'D':'a_addr_delete',
		'v':'a_view',
		'w':'a_view_detail',
		'p':'a_print_detail' }

	squeezed_fs_fs     = ' {{n:>{nw}}} {{m:}}%s {{c:}} {{A:}}'
	squeezed_hdr_fs_fs = ' {{n:>{nw}}} {{m:{mw}}}%s {{c:{cw}}} {{A:{Aw}}}'
	wide_fs_fs         = ' {{n:>{nw}}} {{m:}} {{a:}} {{c:}} {{A:}}'
	wide_hdr_fs_fs     = ' {{n:>{nw}}} {{m:{mw}}} {{a:{aw}}} {{c:{cw}}} {{A:{Aw}}}'

	async def get_rpc_data(self):

		amt0 = self.proto.coin_amt('0')
		self.total = amt0
		self.minconf = None
		addrs = {}

		for label,addr in await self.get_addr_label_pairs():
			bal = await self.wallet.get_balance(addr)
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
