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
proto.rune.tx.new: THORChain new transaction class
"""

from ....tx import new as TxBase

from ...vm.tx.new import New as VmNew

from .base import Base

class New(VmNew, Base, TxBase.New):

	async def get_fee(self, fee, outputs_sum, start_fee_desc):
		return await self.twctl.get_balance(self.inputs[0].addr)

	async def set_gas(self, *, to_addr=None, force=False):
		self.gas = self.dfl_gas

	def set_gas_with_data(self, data):
		pass

	def update_txid(self):
		return super().update_txid(
			self.serialized |
			({'memo': self.swap_memo} if self.is_swap else {}))

	async def make_txobj(self): # called by create_serialized()
		acct_info = self.rpc.get_account_info(self.inputs[0].addr)
		self.txobj = {
			'from':           self.inputs[0].addr,
			'to':             self.outputs[0].addr if self.outputs else None,
			'amt':            self.outputs[0].amt if self.outputs else self.swap_amt,
			'gas':            self.gas,
			'account_number': int(acct_info['account_number']),
			'sequence':       int(acct_info['sequence']),
			'chain_id':       self.proto.chain_id}
