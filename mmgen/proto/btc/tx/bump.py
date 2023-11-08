#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
proto.btc.tx.bump: Bitcoin transaction bump class
"""

from ....tx import bump as TxBase
from ....util import msg
from .new import New
from .completed import Completed

class Bump(Completed,New,TxBase.Bump):
	desc = 'fee-bumped transaction'

	@property
	def min_fee(self):
		return self.sum_inputs() - self.sum_outputs() + self.relay_fee

	def bump_fee(self,idx,fee):
		self.update_output_amt(
			idx,
			self.sum_inputs() - self.sum_outputs(exclude=idx) - fee
		)

	def convert_and_check_fee(self,fee,desc):
		ret = super().convert_and_check_fee(fee,desc)
		if ret is False:
			return ret
		if ret < self.min_fee:
			msg('{} {c}: {} fee too small. Minimum fee: {} {c} ({} {})'.format(
				ret.hl(),
				desc,
				self.min_fee,
				self.fee_abs2rel(self.min_fee.hl()),
				self.rel_fee_desc,
				c = self.coin ))
			return False
		output_amt = self.outputs[self.bump_output_idx].amt
		if ret >= output_amt:
			msg('{} {c}: {} fee too large. Maximum fee: <{} {c}'.format(
				ret.hl(),
				desc,
				output_amt.hl(),
				c = self.coin ))
			return False
		return ret
