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
proto.btc.tw.unspent: Bitcoin base protocol tracking wallet unspent outputs class
"""

from ....tw.unspent import TwUnspentOutputs
from ....addr import CoinAddr

class BitcoinTwUnspentOutputs(TwUnspentOutputs):

	class MMGenTwUnspentOutput(TwUnspentOutputs.MMGenTwUnspentOutput):
		# required by gen_unspent(); setting valid_attrs explicitly is also more efficient
		valid_attrs = {'txid','vout','amt','amt2','comment','twmmid','addr','confs','date','scriptPubKey','skip'}
		invalid_attrs = {'proto'}

	has_age = True
	can_group = True
	hdr_lbl = 'unspent outputs'
	desc = 'unspent outputs'
	item_desc = 'unspent output'
	no_data_errmsg = 'No unspent outputs in tracking wallet!'
	dump_fn_pfx = 'listunspent'
	prompt_fs = 'Total to spend, excluding fees: {} {}\n\n'
	prompt = """
Sort options: [t]xid, [a]mount, a[d]dr, [A]ge, [r]everse, [M]mid
Display options: toggle [D]ays/date, show gr[o]up, show [m]mid
View options: pager [v]iew, [w]ide view
Actions: [q]uit view, [p]rint, r[e]draw, add [l]abel:
"""
	prompt_scroll = """
Sort options: [t]xid, [a]mount, a[d]dr, [A]ge, [r]everse, [M]mid
Display options: toggle [D]ays/date, show gr[o]up, show [m]mid
Scrolling: k=up, j=down, b=pgup, f=pgdown, g=top, G=bottom
View/Actions: [w]ide view, [q]uit, [p]rint, r[e]draw, add [l]abel:
"""
	key_mappings = {
		't':'s_txid',
		'a':'s_amt',
		'd':'s_addr',
		'A':'s_age',
		'r':'d_reverse',
		'M':'s_twmmid',
		'D':'d_days',
		'o':'d_group',
		'm':'d_mmid',
		'e':'d_redraw',
		'q':'a_quit',
		'p':'a_print_detail',
		'v':'a_view',
		'w':'a_view_detail',
		'l':'a_comment_add' }

	async def get_rpc_data(self):
		# bitcoin-cli help listunspent:
		# Arguments:
		# 1. minconf        (numeric, optional, default=1) The minimum confirmations to filter
		# 2. maxconf        (numeric, optional, default=9999999) The maximum confirmations to filter
		# 3. addresses      (json array, optional, default=empty array) A json array of bitcoin addresses
		# 4. include_unsafe (boolean, optional, default=true) Include outputs that are not safe to spend
		# 5. query_options  (json object, optional) JSON with query options

		# for now, self.addrs is just an empty list for Bitcoin and friends
		add_args = (9999999,self.addrs) if self.addrs else ()
		return await self.rpc.call('listunspent',self.minconf,*add_args)
