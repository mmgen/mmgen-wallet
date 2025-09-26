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
wallet.mmhex: MMGen hexadecimal file wallet class
"""

from ..util import make_chksum_6, split_into_cols
from ..seed import Seed
from ..util import msg, is_chksum_6, is_hex_str
from .unenc import wallet

class wallet(wallet):

	stdin_ok = True
	desc = 'hexadecimal seed data with checksum'

	def _format(self):
		seed_hex = self.seed.data.hex()
		self.ssdata.chksum = make_chksum_6(seed_hex)
		self.fmt_data = f'{self.ssdata.chksum} {split_into_cols(4, seed_hex)}\n'

	def _deformat(self):
		match self.fmt_data.split():
			case [chksum, *hex_chunks] if hex_chunks:
				hex_str = ''.join(hex_chunks)
			case _:
				msg(f'{self.fmt_data!r}: invalid {self.desc}')
				return False

		if not len(hex_str) * 4 in Seed.lens:
			msg(f'Invalid data length ({len(hex_str)}) in {self.desc}')
			return False

		if not is_chksum_6(chksum):
			msg(f'{chksum!r}: invalid checksum format in {self.desc}')
			return False

		if not is_hex_str(hex_str):
			msg(f'{hex_str!r}: not a hexadecimal string, in {self.desc}')
			return False

		self.cfg._util.vmsg_r(f'Validating {self.desc} checksum...')

		if not self.cfg._util.compare_chksums(
				chksum, 'file',
				make_chksum_6(hex_str), 'computed',
				verbose = True):
			return False

		self.seed = Seed(self.cfg, seed_bin=bytes.fromhex(hex_str))
		self.ssdata.chksum = chksum

		self.check_usr_seed_len()

		return True
