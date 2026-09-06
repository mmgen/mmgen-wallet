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
proto.rune.tx.data_output: THORChain data output class
"""

from ....tx.data_output import DataOutput

class THORChainDataOutput(DataOutput):

	desc = 'memo'

	@property
	def max_len(self):
		from ....swap.proto.thorchain.memo import THORChainMemo
		return THORChainMemo.max_len
