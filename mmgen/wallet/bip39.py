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
wallet.bip39: BIP39 mnemonic wallet class
"""

from .mnemonic import wallet

class wallet(wallet):

	desc = 'BIP39 mnemonic data'
	mn_type = 'BIP39'
	wl_id = 'bip39'

	def __init__(self, *args, **kwargs):
		from ..bip39 import bip39
		self.conv_cls = bip39
		super().__init__(*args, **kwargs)
