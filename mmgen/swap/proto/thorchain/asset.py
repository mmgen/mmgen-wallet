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
swap.asset: THORChain swap asset class for the MMGen Wallet suite
"""

from ...asset import SwapAsset

class THORChainSwapAsset(SwapAsset):

	_ad = SwapAsset._ad
	assets_data = {
		'BTC':       _ad('Bitcoin',                 'BTC',  None,        'b',  True),
		'LTC':       _ad('Litecoin',                'LTC',  None,        'l',  True),
		'BCH':       _ad('Bitcoin Cash',            'BCH',  None,        'c',  True),
		'ETH':       _ad('Ethereum',                'ETH',  None,        'e',  True),
		'DOGE':      _ad('Dogecoin',                'DOGE', None,        'd',  False),
		'RUNE':      _ad('Rune (THORChain)',        'RUNE', 'THOR.RUNE', 'r',  False),
	}

	evm_contracts = {}

	unsupported = ('DOGE', 'RUNE')

	blacklisted = {}

	evm_chains = ('ETH', 'AVAX', 'BSC', 'BASE')
