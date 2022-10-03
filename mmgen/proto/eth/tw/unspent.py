#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
proto.eth.twuo: Ethereum tracking wallet unspent outputs class
"""

from ....tw.common import TwLabel
from ....tw.unspent import TwUnspentOutputs

# No unspent outputs with Ethereum, but naming must be consistent
class EthereumTwUnspentOutputs(TwUnspentOutputs):

	class MMGenTwUnspentOutput(TwUnspentOutputs.MMGenTwUnspentOutput):
		valid_attrs = {'txid','vout','amt','amt2','label','twmmid','addr','confs','skip'}
		invalid_attrs = {'proto'}

	has_age = False
	can_group = False
	col_adj = 29
	hdr_fmt = 'TRACKED ACCOUNTS (sort order: {a})\nTotal {b}: {c}'
	desc    = 'account balances'
	item_desc = 'account'
	dump_fn_pfx = 'balances'
	prompt = """
Sort options:    [a]mount, a[d]dress, [r]everse, [M]mgen addr
Display options: show [m]mgen addr, r[e]draw screen
Actions:         [q]uit view, [p]rint to file, pager [v]iew, [w]ide view,
                 add [l]abel, [D]elete address, [R]efresh balance:
"""
	key_mappings = {
		'a':'s_amt',
		'd':'s_addr',
		'r':'d_reverse',
		'M':'s_twmmid',
		'm':'d_mmid',
		'e':'d_redraw',
		'q':'a_quit',
		'p':'a_print_detail',
		'v':'a_view',
		'w':'a_view_detail',
		'l':'a_lbl_add',
		'D':'a_addr_delete',
		'R':'a_balance_refresh' }

	squeezed_fs_fs = squeezed_hdr_fs_fs = ' {{n:{cw}}} {{a}} {{A}}'
	wide_fs_fs = ' {{n:4}} {{a}} {{m}} {{A:{aw}}} {{l}}'
	no_data_errmsg = 'No accounts in tracking wallet!'

	async def __init__(self,proto,*args,**kwargs):
		from ....globalvars import g
		if g.cached_balances:
			from ....color import yellow
			self.hdr_fmt += '\n' + yellow('WARNING: Using cached balances. These may be out of date!')
		await super().__init__(proto,*args,**kwargs)

	def do_sort(self,key=None,reverse=False):
		if key == 'txid': return
		super().do_sort(key=key,reverse=reverse)

	async def get_rpc_data(self):
		wl = self.wallet.sorted_list
		if self.addrs:
			wl = [d for d in wl if d['addr'] in self.addrs]
		return [{
				'account': TwLabel(self.proto,d['mmid']+' '+d['comment']),
				'address': d['addr'],
				'amount': await self.wallet.get_balance(d['addr']),
				'confirmations': 0, # TODO
				} for d in wl]

	def age_disp(self,o,age_fmt): # TODO
		pass

class EthereumTokenTwUnspentOutputs(EthereumTwUnspentOutputs):

	prompt_fs = 'Total to spend: {} {}\n\n'
	col_adj = 37
	squeezed_fs_fs = squeezed_hdr_fs_fs = ' {{n:{cw}}} {{a}} {{A}} {{A2}}'
	wide_fs_fs = ' {{n:4}} {{a}} {{m}} {{A:{aw}}} {{A2:{aw}}} {{l}}'

	async def __init__(self,proto,*args,**kwargs):
		await super().__init__(proto,*args,**kwargs)
		self.proto.tokensym = self.wallet.symbol

	@property
	def disp_prec(self):
		return 10 # truncate precision for narrow display

	async def get_data(self,*args,**kwargs):
		await super().get_data(*args,**kwargs)
		for e in self.data:
			e.amt2 = await self.wallet.get_eth_balance(e.addr)
