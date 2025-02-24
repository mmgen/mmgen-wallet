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
swap.proto.thorchain.params: THORChain swap protocol parameters
"""

class params:

	coins = {
		'send': {
			'BTC': 'Bitcoin',
			'LTC': 'Litecoin',
			'BCH': 'Bitcoin Cash',
		},
		'receive': {
			'BTC': 'Bitcoin',
			'LTC': 'Litecoin',
			'BCH': 'Bitcoin Cash',
		}
	}
