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
proto.eth.tx.bump: Ethereum transaction bump class
"""

from decimal import Decimal

from ....tx import bump as TxBase
from .completed import Completed, TokenCompleted
from .new import New, TokenNew

class Bump(Completed, New, TxBase.Bump):
	desc = 'fee-bumped transaction'

	@property
	def min_fee(self):
		return self.fee * Decimal('1.101')

	def bump_fee(self, idx, fee):
		self.txobj['gasPrice'] = self.fee_abs2gas(fee)

	async def get_nonce(self):
		return self.txobj['nonce']

class TokenBump(TokenCompleted, TokenNew, Bump):
	desc = 'fee-bumped transaction'

class AutomountBump(Bump):
	pass

class TokenAutomountBump(TokenBump):
	pass
