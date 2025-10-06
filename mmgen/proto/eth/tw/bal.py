#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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
proto.eth.tw.bal: Ethereum tracking wallet getbalance class
"""

from ....tw.ctl import TwCtl
from ....tw.bal import TwGetBalance

class EthereumTwGetBalance(TwGetBalance):

	start_labels = ('TOTAL', 'Non-MMGen')
	conf_cols = {
		'ge_minconf': 'Balance'}

	async def __init__(self, cfg, proto, *, minconf, quiet):
		self.twctl = await TwCtl(cfg, proto, mode='w')
		await super().__init__(cfg, proto, minconf=minconf, quiet=quiet)

	async def create_data(self):
		in_data = self.twctl.mmid_ordered_dict
		block = self.twctl.rpc.get_block_from_minconf(self.minconf)
		for d in in_data:
			if d.type == 'mmgen':
				label = d.obj.sid
				if label not in self.data:
					self.data[label] = self.balance_info()
			else:
				label = 'Non-MMGen'

			amt = await self.twctl.get_balance(in_data[d]['addr'], block=block)

			self.data['TOTAL']['ge_minconf'] += amt
			self.data[label]['ge_minconf'] += amt

		del self.twctl

class EthereumTokenTwGetBalance(EthereumTwGetBalance):
	pass
