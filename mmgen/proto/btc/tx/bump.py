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
proto.btc.tx.bump: Bitcoin transaction bump class
"""

from ....tx import bump as TxBase
from ....util import msg
from .new_swap import NewSwap
from .completed import Completed
from .unsigned import AutomountUnsigned

class Bump(Completed, NewSwap, TxBase.Bump):
	desc = 'fee-bumped transaction'

	def get_orig_rel_fee(self):
		return self.fee_abs2rel(self.sum_inputs() - self.sum_outputs())

	@property
	def min_fee(self):
		return self.sum_inputs() - self.sum_outputs() + self.relay_fee

	def bump_fee(self, idx, fee):
		self.update_output_amt(
			idx,
			self.sum_inputs() - self.sum_outputs(exclude=idx) - fee
		)

	def convert_and_check_fee(self, fee, desc):
		ret = super().convert_and_check_fee(fee, desc)
		if ret is False or self.new_outputs:
			return ret
		if ret < self.min_fee:
			msg('{} {c}: {} fee too small. Minimum fee: {} {c} ({} {})'.format(
				ret.hl(),
				desc,
				self.min_fee,
				self.fee_abs2rel(self.min_fee),
				self.rel_fee_desc,
				c = self.coin))
			return False
		output_amt = self.outputs[self.bump_output_idx].amt
		if ret >= output_amt:
			msg('{} {c}: {} fee too large. Maximum fee: <{} {c}'.format(
				ret.hl(),
				desc,
				output_amt.hl(),
				c = self.coin))
			return False
		return ret

class AutomountBump(Bump):
	desc      = 'unsigned fee-bumped automount transaction'
	ext       = AutomountUnsigned.ext
	automount = AutomountUnsigned.automount
