#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
proto.eth.tw.unspent: Ethereum tracking wallet unspent outputs class
"""

from ....tw.shared import TwLabel
from ....tw.unspent import TwUnspentOutputs
from .view import EthereumTwView

# No unspent outputs with Ethereum, but naming must be consistent
class EthereumTwUnspentOutputs(EthereumTwView, TwUnspentOutputs):

	class display_type(TwUnspentOutputs.display_type):

		class squeezed(TwUnspentOutputs.display_type.squeezed):
			cols = ('num', 'addr', 'mmid', 'comment', 'amt', 'amt2')

		class detail(TwUnspentOutputs.display_type.detail):
			cols = ('num', 'addr', 'mmid', 'amt', 'amt2', 'comment')

	class MMGenTwUnspentOutput(TwUnspentOutputs.MMGenTwUnspentOutput):
		valid_attrs = {'txid', 'vout', 'amt', 'amt2', 'comment', 'twmmid', 'addr', 'confs', 'skip'}
		invalid_attrs = {'proto'}

	has_age = False
	can_group = False
	hdr_lbl = 'tracked accounts'
	desc    = 'account balances'
	item_desc = 'account'
	dump_fn_pfx = 'balances'
	prompt_fs_in = [
		'Sort options: [a]mount, a[d]dr, [M]mgen addr, [r]everse',
		'Display options: show [m]mgen addr, r[e]draw screen',
		'View/Print: pager [v]iew, [w]ide pager view, [p]rint to file{s}',
		'Actions: [q]uit menu, [D]elete addr, add [l]abel, [R]efresh balance:']
	key_mappings = {
		'a':'s_amt',
		'd':'s_addr',
		'r':'s_reverse',
		'M':'s_twmmid',
		'm':'d_mmid',
		'e':'d_redraw',
		'p':'a_print_detail',
		'v':'a_view',
		'w':'a_view_detail',
		'l':'i_comment_add',
		'D':'i_addr_delete',
		'R':'i_balance_refresh'}

	no_data_errmsg = 'No accounts in tracking wallet!'

	def get_column_widths(self, data, wide, interactive):
		# min screen width: 80 cols
		# num addr [mmid] [comment] amt [amt2]
		return self.compute_column_widths(
			widths = { # fixed cols
				'num': max(2, len(str(len(data)))+1),
				'mmid': max(len(d.twmmid.disp) for d in data) if self.show_mmid else 0,
				'amt': self.amt_widths['amt'],
				'amt2': self.amt_widths.get('amt2', 0),
				'spc': (5 if self.show_mmid else 3) + self.has_amt2, # 5(3) spaces in fs
				'txid': 0,
				'vout': 0,
				'block': 0,
				'date': 0,
				'date_time': 0,
			},
			maxws = { # expandable cols
				'addr': max(len(d.addr) for d in data),
				'comment': max(d.comment.screen_width for d in data) if self.show_mmid else 0,
			},
			minws = {
				'addr': 10,
				'comment': len('Comment') if self.show_mmid else 0,
			},
			maxws_nice = {'addr': 14} if self.show_mmid else {},
			wide = wide,
			interactive = interactive,
		)

	def do_sort(self, key=None, reverse=False):
		if key == 'txid':
			return
		super().do_sort(key=key, reverse=reverse)

	async def get_rpc_data(self):
		wl = self.twctl.sorted_list
		if self.addrs:
			wl = [d for d in wl if d['addr'] in self.addrs]
		return [{
				'account': TwLabel(self.proto, d['mmid']+' '+d['comment']),
				'address': d['addr'],
				'amt': await self.twctl.get_balance(d['addr']),
				'confirmations': 0, # TODO
				} for d in wl]

class EthereumTokenTwUnspentOutputs(EthereumTwUnspentOutputs):

	has_amt2 = True

	async def __init__(self, proto, *args, **kwargs):
		await super().__init__(proto, *args, **kwargs)
		self.proto.tokensym = self.twctl.symbol

	async def get_data(self, *args, **kwargs):
		await super().get_data(*args, **kwargs)
		for e in self.data:
			e.amt2 = await self.twctl.get_eth_balance(e.addr)
