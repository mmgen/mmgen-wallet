#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
tx.new_swap: new swap transaction class
"""

from .new import New

class NewSwap(New):
	desc = 'swap transaction'

	async def process_swap_cmdline_args(self, cmd_args):
		raise NotImplementedError(f'Swap not implemented for protocol {self.proto.__name__}')
