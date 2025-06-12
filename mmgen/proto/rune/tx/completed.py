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
proto.rune.tx.completed: THORChain completed transaction class
"""

from ....tx import completed as TxBase

from ...vm.tx.completed import Completed as VmCompleted

from .base import Base

class Completed(VmCompleted, Base, TxBase.Completed):

	@property
	def total_gas(self):
		return self.txobj['gas']

	@property
	def fee(self):
		return self.proto.coin_amt(self.dfl_fee, from_unit='satoshi')
