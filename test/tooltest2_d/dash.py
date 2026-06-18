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
test.tooltest2_d.dash: DASH test vectors for the ‘mmgen-tool’ utility
"""

from .coin import kafile_opts

tests = {
	'File': {
		'addrfile_chksum': {
			'dash_mainnet': [
				(
					['test/ref/dash/98831F3A-DASH-C[1,31-33,500-501,1010-1011].addrs'],
					'FBC1 6B6A 0988 4403'),
			],
		},
		'keyaddrfile_chksum': {
			'dash_mainnet': [
				(
					['test/ref/dash/98831F3A-DASH-C[1,31-33,500-501,1010-1011].akeys.mmenc'],
					'E83D 2C63 FEA2 4142', kafile_opts
				),
			],
		}
	}
}
