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
proto.eth.twaddrs: Ethereum tracking wallet address list class
"""

from ....tw.addrs import TwAddrList

class EthereumTwAddrList(TwAddrList):

	has_age = False

	async def __init__(self,proto,usr_addr_list,minconf,showempty,showbtcaddrs,all_labels,wallet=None):

		from ....tw.common import TwLabel
		from ....tw.ctl import TrackingWallet
		from ....addr import CoinAddr

		self.proto = proto
		self.wallet = wallet or await TrackingWallet(self.proto,mode='w')
		tw_dict = self.wallet.mmid_ordered_dict
		self.total = self.proto.coin_amt('0')

		for mmid,d in list(tw_dict.items()):
#			if d['confirmations'] < minconf: continue # cannot get confirmations for eth account
			label = TwLabel(self.proto,mmid+' '+d['comment'])
			if usr_addr_list and (label.mmid not in usr_addr_list):
				continue
			bal = await self.wallet.get_balance(d['addr'])
			if bal == 0 and not showempty:
				if not label.comment or not all_labels:
					continue
			self[label.mmid] = {'amt': self.proto.coin_amt('0'), 'lbl':  label }
			if showbtcaddrs:
				self[label.mmid]['addr'] = CoinAddr(self.proto,d['addr'])
			self[label.mmid]['lbl'].mmid.confs = None
			self[label.mmid]['amt'] += bal
			self.total += bal

		del self.wallet

class EthereumTokenTwAddrList(EthereumTwAddrList):
	pass
