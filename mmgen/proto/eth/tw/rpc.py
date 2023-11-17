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
proto.eth.tw.rpc: Ethereum base protocol tracking wallet RPC class
"""

from ....addr import CoinAddr
from ....tw.shared import TwLabel
from ....tw.rpc import TwRPC

class EthereumTwRPC(TwRPC):

	async def get_addr_label_pairs(self,twmmid=None):

		ret = [(
				TwLabel( self.proto, mmid + ' ' + d['comment'] ),
				CoinAddr( self.proto, d['addr'] )
			) for mmid,d in self.twctl.mmid_ordered_dict.items() ]

		if twmmid:
			ret = [e for e in ret if e[0].mmid == twmmid]

		return ret or None

class EthereumTokenTwRPC(EthereumTwRPC):
	pass
