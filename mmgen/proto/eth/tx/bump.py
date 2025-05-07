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
proto.eth.tx.bump: Ethereum transaction bump class
"""

from decimal import Decimal

from ....tx import bump as TxBase
from .completed import Completed, TokenCompleted
from .new import TokenNew
from .new_swap import NewSwap
from .unsigned import AutomountUnsigned, TokenAutomountUnsigned

class Bump(Completed, NewSwap, TxBase.Bump):
	desc = 'fee-bumped transaction'

	def get_orig_rel_fee(self):
		return self.txobj['gasPrice'].to_unit('Gwei')

	@property
	def min_fee(self):
		return self.fee * Decimal('1.101')

	def bump_fee(self, idx, fee):
		self.txobj['gasPrice'] = self.fee_abs2gasprice(fee)

	async def get_nonce(self):
		return self.txobj['nonce']

class TokenBump(TokenCompleted, TokenNew, Bump):
	desc = 'fee-bumped transaction'

class AutomountBump(Bump):
	ext       = AutomountUnsigned.ext
	automount = AutomountUnsigned.automount

class TokenAutomountBump(TokenBump):
	ext       = TokenAutomountUnsigned.ext
	automount = TokenAutomountUnsigned.automount
