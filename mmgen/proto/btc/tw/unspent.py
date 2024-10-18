#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.btc.tw.unspent: Bitcoin base protocol tracking wallet unspent outputs class
"""

from ....tw.unspent import TwUnspentOutputs

class BitcoinTwUnspentOutputs(TwUnspentOutputs):

	class MMGenTwUnspentOutput(TwUnspentOutputs.MMGenTwUnspentOutput):
		# required by gen_unspent(); setting valid_attrs explicitly is also more efficient
		valid_attrs = {
			'txid',
			'vout',
			'amt',
			'amt2',
			'comment',
			'twmmid',
			'addr',
			'confs',
			'date',
			'scriptPubKey',
			'skip'}
		invalid_attrs = {'proto'}

	has_age = True
	can_group = True
	hdr_lbl = 'unspent outputs'
	desc = 'unspent outputs'
	item_desc = 'unspent output'
	no_data_errmsg = 'No unspent outputs in tracking wallet!'
	dump_fn_pfx = 'listunspent'
	prompt_fs_in = [
		'Sort options: [t]xid, [a]mount, [A]ge, a[d]dr, [M]mgen addr, [r]everse',
		'Column options: toggle [D]ays/date/confs/block, gr[o]up, show [m]mgen addr',
		'View options: pager [v]iew, [w]ide pager view{s}',
		'Actions: [q]uit menu, [p]rint, r[e]draw, add [l]abel:']
	prompt_fs_repl = {
		'BCH': (1, 'Column options: toggle [D]ate/confs, cas[h]addr, gr[o]up, show [m]mgen addr')
	}
	key_mappings = {
		't':'s_txid',
		'a':'s_amt',
		'd':'s_addr',
		'A':'s_age',
		'M':'s_twmmid',
		'r':'s_reverse',
		'D':'d_days',
		'o':'d_group',
		'm':'d_mmid',
		'e':'d_redraw',
		'p':'a_print_detail',
		'v':'a_view',
		'w':'a_view_detail',
		'l':'i_comment_add'}

	async def get_rpc_data(self):
		# bitcoin-cli help listunspent:
		# Arguments:
		# 1. minconf        (numeric, optional, default=1) The minimum confirmations to filter
		# 2. maxconf        (numeric, optional, default=9999999) The maximum confirmations to filter
		# 3. addresses      (json array, optional, default=empty array) A json array of bitcoin addresses
		# 4. include_unsafe (boolean, optional, default=true) Include outputs that are not safe to spend
		# 5. query_options  (json object, optional) JSON with query options

		# for now, self.addrs is just an empty list for Bitcoin and friends
		add_args = (9999999, self.addrs) if self.addrs else ()
		return await self.rpc.call('listunspent', self.minconf, *add_args)
