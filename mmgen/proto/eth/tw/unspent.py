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
proto.eth.tw.unspent: Ethereum tracking wallet unspent outputs class
"""

from ....tw.unspent import TwUnspentOutputs
from .view import EthereumTwView

class EthereumTwUnspentOutputs(EthereumTwView, TwUnspentOutputs):

	hdr_lbl = 'tracked accounts'
	desc    = 'account balances'
	item_desc = 'account'
	item_desc_pl = 'accounts'

class EthereumTokenTwUnspentOutputs(EthereumTwUnspentOutputs):

	has_amt2 = True

	async def get_data(self):
		await super().get_data()
		for e in self.data:
			e.amt2 = await self.twctl.get_eth_balance(e.addr)
