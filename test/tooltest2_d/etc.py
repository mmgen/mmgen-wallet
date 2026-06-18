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
test.tooltest2_d.etc: ETC test vectors for the ‘mmgen-tool’ utility
"""

from .coin import kafile_opts

tests = {
	'File': {
		'addrfile_chksum': {
			'etc_mainnet': [
				(
					['test/ref/ethereum_classic/98831F3A-ETC[1,31-33,500-501,1010-1011].addrs'],
					'E97A D796 B495 E8BC'
				),
			],
		},
		'keyaddrfile_chksum': {
			'etc_mainnet': [
				(
					['test/ref/ethereum_classic/98831F3A-ETC[1,31-33,500-501,1010-1011].akeys.mmenc'],
					'EF49 967D BD6C FE45', kafile_opts
				),
			],
		},
		'txview': {
			'etc_mainnet': [(['test/ref/ethereum_classic/ED3848-ETC[1.2345,40000].rawtx'], None),],
		},
	},
}
