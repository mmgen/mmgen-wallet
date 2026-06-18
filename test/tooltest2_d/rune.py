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
test.tooltest2_d.rune: RUNE test vectors for the ‘mmgen-tool’ utility
"""

from .btc import pubhash2

addr1 = 'thor1xptlvmwaymaxa7pxkr2u5pn7c0508stcr9tw2z'

tests = {
	'Coin': {
		'addr2pubhash': {
			'rune_mainnet': [
				([addr1], pubhash2),
			],
		},
		'pubhash2addr': {
			'rune_mainnet': [
				([pubhash2], addr1, ['--type=X'], 'bech32x'),
			],
		},
	},
	'File': {
		'addrfile_chksum': {
			'rune_mainnet': [
				(
					['test/ref/thorchain/98831F3A-RUNE-X[1,31-33,500-501,1010-1011].addrs'],
					'00C6 1930 557F 5E99'
				),
			],
		},
	},
}
