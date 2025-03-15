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
wallet.plainhex: plain hexadecimal wallet class
"""

from ..util import msg, is_hex_str_lc
from ..seed import Seed
from .unenc import wallet

class wallet(wallet):

	stdin_ok = True
	desc = 'plain hexadecimal seed data'

	def _format(self):
		self.fmt_data = self.seed.data.hex() + '\n'

	def _deformat(self):
		desc = self.desc
		d = self.fmt_data.strip()

		if not is_hex_str_lc(d):
			msg(f'{d!r}: not a lowercase hexadecimal string, in {desc}')
			return False

		if not len(d)*4 in Seed.lens:
			msg(f'Invalid data length ({len(d)}) in {desc}')
			return False

		self.seed = Seed(self.cfg, seed_bin=bytes.fromhex(d))

		self.check_usr_seed_len()

		return True
