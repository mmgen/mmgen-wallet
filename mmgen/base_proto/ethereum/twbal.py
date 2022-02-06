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
base_proto.ethereum.twbal: Ethereum tracking wallet getbalance class
"""

from ...twctl import TrackingWallet
from ...twbal import TwGetBalance

class EthereumTwGetBalance(TwGetBalance):

	fs = '{w:13} {c}\n' # TODO - for now, just suppress display of meaningless data

	async def __init__(self,proto,*args,**kwargs):
		self.wallet = await TrackingWallet(proto,mode='w')
		await super().__init__(proto,*args,**kwargs)

	async def create_data(self):
		data = self.wallet.mmid_ordered_dict
		for d in data:
			if d.type == 'mmgen':
				key = d.obj.sid
				if key not in self.data:
					self.data[key] = [self.proto.coin_amt('0')] * 4
			else:
				key = 'Non-MMGen'

			conf_level = 2 # TODO
			amt = await self.wallet.get_balance(data[d]['addr'])

			self.data['TOTAL'][conf_level] += amt
			self.data[key][conf_level] += amt

		del self.wallet

class EthereumTokenTwGetBalance(EthereumTwGetBalance): pass
