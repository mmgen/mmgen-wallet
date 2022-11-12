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
proto.btc.tw.addresses: Bitcoin base protocol tracking wallet address list class
"""

from ....tw.addresses import TwAddresses
from ....tw.shared import TwLabel
from ....util import msg,msg_r
from ....addr import CoinAddr
from ....obj import NonNegativeInt,get_obj
from .common import BitcoinTwCommon

class BitcoinTwAddresses(TwAddresses,BitcoinTwCommon):

	has_age = True
	prompt = """
Sort options: [a]mt, [A]ge, [M]mid, [r]everse
Column options: toggle [D]ays/date/confs/block
Filters: show [E]mpty addrs, [u]sed addrs, all [L]abels
View/Print: pager [v]iew, [w]ide view, [p]rint
Actions: [q]uit, r[e]draw, add [l]abel:
"""
	key_mappings = {
		'a':'s_amt',
		'A':'s_age',
		'M':'s_twmmid',
		'r':'d_reverse',
		'D':'d_days',
		'e':'d_redraw',
		'E':'d_showempty',
		'u':'d_showused',
		'L':'d_all_labels',
		'q':'a_quit',
		'v':'a_view',
		'w':'a_view_detail',
		'p':'a_print_detail',
		'l':'a_comment_add' }

	async def get_rpc_data(self):

		msg_r('Getting unspent outputs...')
		addrs = await self.get_unspent_by_mmid(self.minconf)
		msg('done')

		amt0 = self.proto.coin_amt('0')
		self.total = sum((v['amt'] for v in addrs.values()), start=amt0 )

		msg_r('Getting labels and associated addresses...')
		for label,addr in await self.get_addr_label_pairs():
			if label and label.mmid not in addrs:
				addrs[label.mmid] = {
					'addr':   addr,
					'amt':    amt0,
					'recvd':  amt0,
					'confs':  0,
					'lbl':    label }
		msg('done')

		msg_r('Getting received funds data...')
		# args: 1:minconf, 2:include_empty, 3:include_watchonly, 4:include_immature_coinbase
		for d in await self.rpc.call( 'listreceivedbylabel', 1, False, True ):
			label = get_obj( TwLabel, proto=self.proto, text=d['label'] )
			if label:
				assert label.mmid in addrs, f'{label.mmid!r} not found in addrlist!'
				addrs[label.mmid]['recvd'] = d['amount']
				addrs[label.mmid]['confs'] = d['confirmations']
		msg('done')

		return addrs
