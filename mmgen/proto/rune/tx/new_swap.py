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
proto.rune.tx.new_swap: THORChain new swap transaction class
"""

from ....tx.new_swap import NewSwap as TxNewSwap

from ...vm.tx.new_swap import VmNewSwap

from .new import New

class NewSwap(VmNewSwap, New, TxNewSwap):
	desc = 'RUNE swap transaction'

	def update_vault_addr(self, c, *, addr='inbound_address'):
		pass
