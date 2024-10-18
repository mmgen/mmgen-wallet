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
wallet.seed: seed file wallet class
"""

from ..util import msg, make_chksum_6, split_into_cols, is_chksum_6
from ..baseconv import baseconv, is_b58_str
from ..seed import Seed
from .unenc import wallet

class wallet(wallet):

	stdin_ok = True
	desc = 'seed data'

	def _format(self):
		b58seed = baseconv('b58').frombytes(self.seed.data, pad='seed', tostr=True)
		self.ssdata.chksum = make_chksum_6(b58seed)
		self.ssdata.b58seed = b58seed
		self.fmt_data = '{} {}\n'.format(
			self.ssdata.chksum,
			split_into_cols(4, b58seed))

	def _deformat(self):
		desc = self.desc
		ld = self.fmt_data.split()

		if not (7 <= len(ld) <= 12): # 6 <= padded b58 data (ld[1:]) <= 11
			msg(f'Invalid data length ({len(ld)}) in {desc}')
			return False

		a, b = ld[0], ''.join(ld[1:])

		if not is_chksum_6(a):
			msg(f'{a!r}: invalid checksum format in {desc}')
			return False

		if not is_b58_str(b):
			msg(f'{b!r}: not a base 58 string, in {desc}')
			return False

		self.cfg._util.vmsg_r(f'Validating {desc} checksum...')

		if not self.cfg._util.compare_chksums(a, 'file', make_chksum_6(b), 'computed', verbose=True):
			return False

		ret = baseconv('b58').tobytes(b, pad='seed')

		if ret is False:
			msg(f'Invalid base-58 encoded seed: {b}')
			return False

		self.seed = Seed(self.cfg, ret)
		self.ssdata.chksum = a
		self.ssdata.b58seed = b

		self.check_usr_seed_len()

		return True
