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
proto.btc.twaddrs: Bitcoin base protocol tracking wallet address list class
"""

from ....util import msg,die
from ....obj import MMGenList
from ....addr import CoinAddr
from ....rpc import rpc_init
from ....tw.addrs import TwAddrList
from ....tw.common import get_tw_label
from .common import BitcoinTwCommon

class BitcoinTwAddrList(TwAddrList,BitcoinTwCommon):

	has_age = True

	async def __init__(self,proto,usr_addr_list,minconf,showempty,showcoinaddrs,all_labels,wallet=None):

		self.rpc   = await rpc_init(proto)
		self.proto = proto

		# get balances with 'listunspent'
		self.update( await self.get_unspent_by_mmid(minconf,usr_addr_list) )
		self.total = sum(v['amt'] for v in self.values()) or proto.coin_amt('0')

		# use 'listaccounts' only for empty addresses, as it shows false positive balances
		if showempty or all_labels:
			for label,addr in await self.get_addr_label_pairs():
				if (not label
					or (all_labels and not showempty and not label.comment)
					or (usr_addr_list and (label.mmid not in usr_addr_list)) ):
					continue
				if label.mmid not in self:
					self[label.mmid] = { 'amt':proto.coin_amt('0'), 'lbl':label, 'addr':'' }
					if showcoinaddrs:
						self[label.mmid]['addr'] = CoinAddr(proto,addr)
