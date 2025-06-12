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
proto.eth.tx.completed: Ethereum completed transaction class
"""

from ....tx import completed as TxBase

from ...vm.tx.completed import Completed as VmCompleted

from .base import Base, TokenBase

class Completed(VmCompleted, Base, TxBase.Completed):
	fn_fee_unit = 'Mwei'

	@property
	def total_gas(self):
		return self.txobj['startGas']

	@property
	def fee(self):
		return self.fee_gasPrice2abs(self.txobj['gasPrice'].toWei())

class TokenCompleted(TokenBase, Completed):

	@property
	def change(self):
		return self.sum_inputs() - self.send_amt

	@property
	def total_gas(self):
		return self.txobj['startGas'] + (self.txobj['router_gas'] if self.is_swap else 0)
