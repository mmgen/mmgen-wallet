#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
proto.btc.tw.addresses: Bitcoin base protocol tracking wallet address list class
"""

from ....tw.addresses import TwAddresses
from ....tw.shared import TwLabel
from ....util import msg,msg_r
from ....obj import get_obj
from .rpc import BitcoinTwRPC

class BitcoinTwAddresses(TwAddresses,BitcoinTwRPC):

	has_age = True
	prompt_fs = """
Sort options: [a]mt, [A]ge, [M]mgen addr, [r]everse
Column options: toggle [D]ays/date/confs/block
Filters: show [E]mpty addrs, [u]sed addrs, all [L]abels
View/Print: pager [v]iew, [w]ide pager view, [p]rint{s}
Actions: [q]uit menu, r[e]draw, add [l]abel:
"""
	key_mappings = {
		'a':'s_amt',
		'A':'s_age',
		'M':'s_twmmid',
		'r':'s_reverse',
		'D':'d_days',
		'e':'d_redraw',
		'E':'d_showempty',
		'u':'d_showused',
		'L':'d_all_labels',
		'v':'a_view',
		'w':'a_view_detail',
		'p':'a_print_detail',
		'l':'i_comment_add' }

	async def get_rpc_data(self):

		msg_r('Getting unspent outputs...')
		addrs = await self.get_unspent_by_mmid(self.minconf)
		msg('done')

		amt0 = self.proto.coin_amt('0')
		self.total = sum((v['amt'] for v in addrs.values())) or amt0 # Python 3.8: start=amt0

		msg_r('Getting labels and associated addresses...')
		pairs = await self.get_addr_label_pairs()

		if pairs:
			for label,addr in pairs:
				if label and label.mmid not in addrs:
					addrs[label.mmid] = {
						'addr':   addr,
						'amt':    amt0,
						'recvd':  amt0,
						'confs':  0,
						'lbl':    label }
			msg('done')
		else:
			msg('[none]')

		msg_r('Getting received funds data...')
		# args: 1:minconf, 2:include_empty, 3:include_watchonly, 4:include_immature_coinbase (>=v23.0.0)
		for d in await self.rpc.call( 'listreceivedbylabel', 1, True, True ):
			label = get_obj( TwLabel, proto=self.proto, text=d['label'] )
			if label:
				assert label.mmid in addrs, f'{label.mmid!r} not found in addrlist!'
				addrs[label.mmid]['recvd'] = d['amount']
				addrs[label.mmid]['confs'] = d['confirmations']
		msg('done')

		return addrs
