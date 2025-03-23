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
proto.btc.tx.new_swap: Bitcoin new swap transaction class
"""

from ....tx.new_swap import NewSwap as TxNewSwap
from ....tx.new_swap import get_swap_proto_mod
from .new import New

class NewSwap(New, TxNewSwap):
	desc = 'Bitcoin swap transaction'

	def update_data_output(self, trade_limit):
		sp = get_swap_proto_mod(self.swap_proto)
		o = self.data_output._asdict()
		parsed_memo = sp.data.parse(o['data'].decode())
		memo = sp.data(
			self.recv_proto,
			self.recv_proto.coin_addr(parsed_memo.address),
			trade_limit = trade_limit)
		o['data'] = f'data:{memo}'
		self.data_output = self.Output(self.proto, **o)

	@property
	def vault_idx(self):
		return self._chg_output_ops('idx', 'is_vault')

	@property
	def vault_output(self):
		return self._chg_output_ops('output', 'is_vault')
