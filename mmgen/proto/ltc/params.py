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
proto.ltc.params: Litecoin protocol
"""

from ..btc.params import mainnet

class mainnet(mainnet):
	block0          = '12a765e31ffd4059bada1e25190f6e98c99d9714d334efa41a195a7e7e04bfe2'
	addr_ver_info   = {'30': 'p2pkh', '05': 'p2sh', '32': 'p2sh'} # new p2sh ver 0x32 must come last
	wif_ver_num     = {'std': 'b0'}
	mmtypes         = ('L', 'C', 'S', 'B')
	coin_amt        = 'LTCAmt'
	max_tx_fee      = '0.3'
	base_coin       = 'LTC'
	forks           = []
	bech32_hrp      = 'ltc'
	avg_bdi         = 150
	halving_interval = 840000
	ignore_daemon_version = False

class testnet(mainnet):
	# addr ver nums same as Bitcoin testnet, except for 'p2sh'
	addr_ver_info      = {'6f': 'p2pkh', 'c4': 'p2sh', '3a': 'p2sh'}
	wif_ver_num        = {'std': 'ef'} # same as Bitcoin testnet
	bech32_hrp         = 'tltc'

class regtest(testnet):
	bech32_hrp         = 'rltc'
	halving_interval   = 150
