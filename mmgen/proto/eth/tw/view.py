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
proto.eth.tw.view: Ethereum base protocol base class for tracking wallet view classes
"""

from ....globalvars import g
from ....tw.view import TwView

class EthereumTwView(TwView):

	def age_disp(self,o,age_fmt): # TODO
		pass

	def get_disp_prec(self,wide):
		return self.proto.coin_amt.max_prec if wide else 8

	def gen_subheader(self,cw,color):
		if self.disp_prec == 8:
			yield 'Balances truncated to 8 decimal points'
		if g.cached_balances:
			from ....color import nocolor,yellow
			yield (nocolor,yellow)[color]('WARNING: Using cached balances. These may be out of date!')
