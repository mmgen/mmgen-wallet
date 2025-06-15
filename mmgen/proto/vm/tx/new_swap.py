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
proto.vm.tx.new_swap: new swap transaction methods for VM chains
"""

class VmNewSwap:

	def update_data_output(self, trade_limit):
		parsed_memo = self.swap_proto_mod.Memo.parse(self.swap_memo)
		self.swap_memo = str(self.swap_proto_mod.Memo(
			self.swap_cfg,
			self.recv_proto,
			self.recv_asset,
			self.recv_proto.coin_addr(parsed_memo.address),
			trade_limit = trade_limit))
		self.set_gas_with_data(self.swap_memo.encode())

	@property
	def vault_idx(self):
		return 0

	@property
	def vault_output(self):
		return self.outputs[0]
