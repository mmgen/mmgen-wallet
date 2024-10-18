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
wallet.words: MMGen mnemonic wallet class
"""

from .mnemonic import wallet

class wallet(wallet):

	desc = 'MMGen native mnemonic data'
	mn_type = 'MMGen native'
	wl_id = 'mmgen'
