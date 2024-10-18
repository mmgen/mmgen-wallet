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
wallet.incog_hex: hexadecimal incognito wallet class
"""

from ..util2 import pretty_hexdump, decode_pretty_hexdump
from .incog_base import wallet

class wallet(wallet):

	desc = 'hex incognito data'
	file_mode = 'text'
	no_tty = False

	def _deformat(self):
		ret = decode_pretty_hexdump(self.fmt_data)
		if ret:
			self.fmt_data = ret
			return super()._deformat()
		else:
			return False

	def _format(self):
		super()._format()
		self.fmt_data = pretty_hexdump(self.fmt_data)
