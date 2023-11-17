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
proto.btc.tw.bal: Bitcoin base protocol tracking wallet balance class
"""

from ....tw.bal import TwGetBalance
from ....tw.shared import get_tw_label

class BitcoinTwGetBalance(TwGetBalance):

	start_labels = ('TOTAL','Non-MMGen','Non-wallet')
	conf_cols = {
		'unconfirmed': 'Unconfirmed',
		'lt_minconf':  '<{minconf} confs',
		'ge_minconf':  '>={minconf} confs',
	}

	async def create_data(self):
		lbl_id = ('account','label')['label_api' in self.rpc.caps]
		for d in await self.rpc.call('listunspent',0):
			tw_lbl = get_tw_label(self.proto,d[lbl_id])
			if tw_lbl:
				if tw_lbl.mmid.type == 'mmgen':
					label = tw_lbl.mmid.obj.sid
					if label not in self.data:
						self.data[label] = self.balance_info()
				else:
					label = 'Non-MMGen'
			else:
				label = 'Non-wallet'

			amt = self.proto.coin_amt(d['amount'])

			if not d['confirmations']:
				self.data['TOTAL']['unconfirmed'] += amt
				self.data[label]['unconfirmed'] += amt

			col_key = ('lt_minconf','ge_minconf')[d['confirmations'] >= self.minconf]
			self.data['TOTAL'][col_key] += amt
			self.data[label][col_key] += amt

			if d['spendable']:
				self.data[label]['spendable'] += amt
