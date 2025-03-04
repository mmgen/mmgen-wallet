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
swap.proto.thorchain: THORChain swap protocol implementation for the MMGen Wallet suite
"""

__all__ = ['data']

name = 'THORChain'

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

def rpc_client(tx, amt):
	from .midgard import Midgard
	return Midgard(tx, amt)

from .memo import Memo as data
