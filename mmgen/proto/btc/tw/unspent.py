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
proto.btc.tw.unspent: Bitcoin base protocol tracking wallet unspent outputs class
"""

from ....obj import ImmutableAttr, ListItemAttr, HexStr
from ....tw.unspent import TwUnspentOutputs

from .view import BitcoinTwView

class BitcoinTwUnspentOutputs(BitcoinTwView, TwUnspentOutputs):

	class display_type(TwUnspentOutputs.display_type):

		class squeezed(TwUnspentOutputs.display_type.squeezed):
			cols = ('num', 'txid', 'vout', 'addr', 'mmid', 'comment', 'amt', 'amt2', 'date')

		class detail(TwUnspentOutputs.display_type.detail):
			cols = ('num', 'txid', 'vout', 'addr', 'mmid', 'amt', 'amt2', 'block', 'date_time', 'comment')

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
		date         = ListItemAttr(int, typeconv=False, reassign_ok=True)
		scriptPubKey = ImmutableAttr(HexStr)

	has_age = True
	groupable = {
		'addr':   'addr',
		'twmmid': 'addr',
		'txid':   'txid'}
	disp_spc = 5
	vout_w = 4
	hdr_lbl = 'unspent outputs'
	desc = 'unspent outputs'
	item_desc = 'unspent output'
	item_desc_pl = 'unspent outputs'
	dump_fn_pfx = 'listunspent'
	prompt_fs_in = [
		'Sort options: [t]xid, [a]mount, [A]ge, a[d]dr, [M]mgen addr, [r]everse',
		'Column options: toggle [D]ays/date/confs/block, gr[o]up, show [m]mgen addr',
		'View options: pager [v]iew, [w]ide pager view{s}',
		'Actions: [q]uit menu, [p]rint, r[e]draw, add [l]abel:']
	prompt_fs_repl = {
		'BCH': (1, 'Column options: toggle [D]ate/confs, cas[h]addr, gr[o]up, show [m]mgen addr')}
	extra_key_mappings = {
		'D':'d_days',
		'o':'d_group',
		't':'s_txid',
		'A':'s_age'}

	sort_funcs = {
		'addr':   lambda i: '{} {:010} {:024.12f}'.format(i.addr, 0xffffffff - abs(i.confs), i.amt),
		'age':    lambda i: '{:010} {:024.12f}'.format(0xffffffff - abs(i.confs), i.amt),
		'amt':    lambda i: '{:024.12f} {:010} {}'.format(i.amt, 0xffffffff - abs(i.confs), i.addr),
		'txid':   lambda i: f'{i.txid} {i.vout:04}',
		'twmmid': lambda i: '{} {:010} {:024.12f}'.format(
			i.twmmid.sort_key, 0xffffffff - abs(i.confs), i.amt)}

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
