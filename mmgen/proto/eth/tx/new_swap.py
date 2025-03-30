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
proto.eth.tx.new_swap: Ethereum new swap transaction class
"""

from ....tx.new_swap import NewSwap as TxNewSwap
from ....tx.new_swap import get_swap_proto_mod
from .new import New

class NewSwap(New, TxNewSwap):
	desc = 'Ethereum swap transaction'

	def update_data_output(self, trade_limit):
		sp = get_swap_proto_mod(self.swap_proto)
		data = bytes.fromhex(self.txobj['data']) if self.is_bump else self.usr_contract_data
		parsed_memo = sp.data.parse(data.decode())
		memo = sp.data(
			self.recv_proto,
			self.recv_proto.coin_addr(parsed_memo.address),
			trade_limit = trade_limit)
		self.usr_contract_data = str(memo).encode()
		self.set_gas_with_data(self.usr_contract_data)

	@property
	def vault_idx(self):
		return 0

	@property
	def vault_output(self):
		return self.outputs[0]
