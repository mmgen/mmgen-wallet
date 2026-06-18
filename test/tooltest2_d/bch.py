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
test.tooltest2_d.bch: BCH test vectors for the ‘mmgen-tool’ utility
"""

tests = {
	'File': {
		'txview': {
			'bch_mainnet': [(['test/ref/460D4D-BCH[10.19764,tl=1320969600].rawtx'], None),],
			'bch_testnet': [(['test/ref/359FD5-BCH[6.68868,tl=1320969600].testnet.rawtx'], None),],
		},
	},
}
