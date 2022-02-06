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
base_proto.bitcoin.twbal: Bitcoin base protocol tracking wallet balance class
"""

from ...twbal import TwGetBalance
from ...tw import get_tw_label

class BitcoinTwGetBalance(TwGetBalance):

	fs = '{w:13} {u:<16} {p:<16} {c}'

	async def create_data(self):
		# 0: unconfirmed, 1: below minconf, 2: confirmed, 3: spendable (privkey in wallet)
		lbl_id = ('account','label')['label_api' in self.rpc.caps]
		for d in await self.rpc.call('listunspent',0):
			lbl = get_tw_label(self.proto,d[lbl_id])
			if lbl:
				if lbl.mmid.type == 'mmgen':
					key = lbl.mmid.obj.sid
					if key not in self.data:
						self.data[key] = [self.proto.coin_amt('0')] * 4
				else:
					key = 'Non-MMGen'
			else:
				lbl,key = None,'Non-wallet'

			amt = self.proto.coin_amt(d['amount'])

			if not d['confirmations']:
				self.data['TOTAL'][0] += amt
				self.data[key][0] += amt

			conf_level = (1,2)[d['confirmations'] >= self.minconf]

			self.data['TOTAL'][conf_level] += amt
			self.data[key][conf_level] += amt

			if d['spendable']:
				self.data[key][3] += amt
