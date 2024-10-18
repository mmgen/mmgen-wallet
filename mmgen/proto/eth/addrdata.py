#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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
proto.eth.addrdata: Ethereum TwAddrData classes
"""

from ...addrdata import TwAddrData

class EthereumTwAddrData(TwAddrData):

	msgs = {
		'multiple_acct_addrs': """
			ERROR: More than one address found for account: {acct!r}.
			Your tracking wallet is corrupted!
		"""
	}

	async def get_tw_data(self, twctl=None):
		from ...tw.ctl import TwCtl
		self.cfg._util.vmsg('Getting address data from tracking wallet')
		twctl = (twctl or await TwCtl(self.cfg, self.proto)).mmid_ordered_dict
		# emulate the output of RPC 'listaccounts' and 'getaddressesbyaccount'
		return [(mmid+' '+d['comment'], [d['addr']]) for mmid, d in list(twctl.items())]

class EthereumTokenTwAddrData(EthereumTwAddrData):
	pass
