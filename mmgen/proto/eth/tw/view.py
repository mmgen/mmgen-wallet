#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.eth.tw.view: Ethereum base protocol base class for tracking wallet view classes
"""

from ....tw.view import TwView

class EthereumTwView(TwView):

	sort_funcs = {
		'addr':   lambda i: i.addr,
		'age':    lambda i: 0 - i.confs,
		'amt':    lambda i: i.amt,
		'txid':   lambda i: f'{i.txid} {i.vout:04}',
		'twmmid': lambda i: i.twmmid.sort_key
	}

	def age_disp(self, o, age_fmt): # TODO
		pass

	def get_disp_prec(self, wide):
		return self.proto.coin_amt.max_prec if wide else 8

	def gen_subheader(self, cw, color):
		if self.disp_prec == 8:
			yield 'Balances truncated to 8 decimal points'
		if self.cfg.cached_balances:
			from ....color import nocolor, yellow
			yield (nocolor, yellow)[color]('WARNING: Using cached balances. These may be out of date!')
