#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.eth.tw.view: Ethereum base protocol base class for tracking wallet view classes
"""

class EthereumTwView:

	def get_disp_prec(self, wide):
		return self.proto.coin_amt.max_prec if wide else 8

	def gen_subheader(self, cw, color):
		if self.disp_prec == 8:
			yield 'Balances truncated to 8 decimal points'
		yield from super().gen_subheader(cw, color)
