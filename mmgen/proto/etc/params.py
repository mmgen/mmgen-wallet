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
proto.etc.params: Ethereum Classic protocol
"""

from ..eth.params import mainnet

class mainnet(mainnet):
	chain_names = ['classic', 'ethereum_classic']
	max_tx_fee  = 0.005
	coin_amt    = 'ETCAmt'

class testnet(mainnet):
	chain_names = ['morden', 'morden_testnet', 'classic-testnet']

class regtest(testnet):
	chain_names = ['developmentchain']
	decimal_prec = 64
