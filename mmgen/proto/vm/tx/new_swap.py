#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
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
		self.swap_memo = str(self.update_memo(self.swap_memo, trade_limit))
		self.set_gas_with_data(self.swap_memo.encode())

	@property
	def vault_idx(self):
		return 0

	@property
	def vault_output(self):
		return self.outputs[0]
