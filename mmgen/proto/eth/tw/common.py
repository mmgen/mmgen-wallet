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
proto.eth.tw.common: Ethereum base protocol tracking wallet dependency classes
"""
from ....globalvars import g
from ....tw.ctl import TrackingWallet
from ....tw.view import TwView
from ....addr import CoinAddr
from ....tw.view import TwLabel

class EthereumTwCommon(TwView):

	def age_disp(self,o,age_fmt): # TODO
		pass

	def get_disp_prec(self,wide):
		return self.proto.coin_amt.max_prec if wide else 8

	def subheader(self,color):
		ret = ''
		if self.disp_prec == 8:
			ret += 'Balances truncated to 8 decimal points\n'
		if g.cached_balances:
			from ....color import nocolor,yellow
			ret += (nocolor,yellow)[color](
				'WARNING: Using cached balances. These may be out of date!') + '\n'
		return ret

	async def get_addr_label_pairs(self,twmmid=None):
		wallet = (
			self if isinstance(self,TrackingWallet) else
			(self.wallet or await TrackingWallet(self.proto,mode='w'))
		)

		ret = [(
				TwLabel( self.proto, mmid + ' ' + d['comment'] ),
				CoinAddr( self.proto, d['addr'] )
			) for mmid,d in wallet.mmid_ordered_dict.items() ]

		if wallet is not self:
			del wallet

		if twmmid:
			ret = [e for e in ret if e[0].mmid == twmmid]

		return ret or None
