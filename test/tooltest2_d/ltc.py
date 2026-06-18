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
test.tooltest2_d.ltc: LTC test vectors for the ‘mmgen-tool’ utility
"""

from .coin import kafile_opts

tests = {
	'File': {
		'addrfile_chksum': {
			'ltc_mainnet': [
				(
					['test/ref/litecoin/98831F3A-LTC[1,31-33,500-501,1010-1011].addrs'],
					'AD52 C3FE 8924 AAF0'
				), (
					['test/ref/litecoin/98831F3A-LTC-S[1,31-33,500-501,1010-1011].addrs'],
					'63DF E42A 0827 21C3'
				), (
					['test/ref/litecoin/98831F3A-LTC-B[1,31-33,500-501,1010-1011].addrs'],
					'FF1C 7939 5967 AB82'
				),
			],
			'ltc_testnet': [
				(
					['test/ref/litecoin/98831F3A-LTC[1,31-33,500-501,1010-1011].testnet.addrs'],
					'4EBE 2E85 E969 1B30'
				), (
					['test/ref/litecoin/98831F3A-LTC-S[1,31-33,500-501,1010-1011].testnet.addrs'],
					'5DD1 D186 DBE1 59F2'
				), (
					['test/ref/litecoin/98831F3A-LTC-B[1,31-33,500-501,1010-1011].testnet.addrs'],
					'ED3D 8AA4 BED4 0B40'
				),
			],
		},
		'keyaddrfile_chksum': {
			'ltc_mainnet': [
				(
					['test/ref/litecoin/98831F3A-LTC[1,31-33,500-501,1010-1011].akeys.mmenc'],
					'B804 978A 8796 3ED4', kafile_opts
				),
			],
			'ltc_testnet': [
				(
					['test/ref/litecoin/98831F3A-LTC[1,31-33,500-501,1010-1011].testnet.akeys.mmenc'],
					'98B5 AC35 F334 0398', kafile_opts
				),
			],
		},
		'txview': {
			'ltc_mainnet': [
				(['test/ref/litecoin/AF3CDF-LTC[620.76194,1453,tl=1320969600].rawtx'], None),
			],
			'ltc_testnet': [
				(['test/ref/litecoin/A5A1E0-LTC[1454.64322,1453,tl=1320969600].testnet.rawtx'], None),
			],
		},
	},
}
