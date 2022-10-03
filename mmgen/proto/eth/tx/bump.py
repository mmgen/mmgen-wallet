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
proto.eth.tx.bump: Ethereum transaction bump class
"""

import mmgen.tx.bump as TxBase
from .completed import Completed,TokenCompleted
from .new import New,TokenNew
from ....amt import ETHAmt
from decimal import Decimal

class Bump(Completed,New,TxBase.Bump):
	desc = 'fee-bumped transaction'

	@property
	def min_fee(self):
		return ETHAmt(self.fee * Decimal('1.101'))

	def bump_fee(self,idx,fee):
		self.txobj['gasPrice'] = self.fee_abs2rel(fee,to_unit='eth')

	async def get_nonce(self):
		return self.txobj['nonce']

class TokenBump(TokenCompleted,TokenNew,Bump):
	desc = 'fee-bumped transaction'
