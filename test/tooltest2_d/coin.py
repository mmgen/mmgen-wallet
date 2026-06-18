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
test.tooltest2_d.coin: Shared coin-specific test vectors for the ‘mmgen-tool’ utility
"""

kafile_opts = ['-p1', '-Ptest/ref/keyaddrfile_password']

privhex1 = '0000000000000000000000000000000000000000000000000000000000000001'
privhex2 = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
privhex3 = '0fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
privhex4 = '00000000000000000000000000000000000000000000000000000000000000ff'
privhex5 = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0f'
privhex6 = 'deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef'
