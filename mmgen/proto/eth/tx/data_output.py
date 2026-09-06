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
proto.eth.tx.data_output: Ethereum data output class
"""

from ....tx.data_output import DataOutput

class EthereumDataOutput(DataOutput):

	desc = 'data'

	@property
	def max_len(self):
		return self.proto.max_data_len

class EthereumTokenDataOutput(EthereumDataOutput):
	pass
