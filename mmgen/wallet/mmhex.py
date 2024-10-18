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
		h = self.seed.data.hex()
		self.ssdata.chksum = make_chksum_6(h)
		self.fmt_data = f'{self.ssdata.chksum} {split_into_cols(4, h)}\n'

	def _deformat(self):
		desc = self.desc
		d = self.fmt_data.split()
		try:
			d[1]
			chk, hstr = d[0], ''.join(d[1:])
		except:
			msg(f'{self.fmt_data.strip()!r}: invalid {desc}')
			return False

		if not len(hstr)*4 in Seed.lens:
			msg(f'Invalid data length ({len(hstr)}) in {desc}')
			return False

		if not is_chksum_6(chk):
			msg(f'{chk!r}: invalid checksum format in {desc}')
			return False

		if not is_hex_str(hstr):
			msg(f'{hstr!r}: not a hexadecimal string, in {desc}')
			return False

		self.cfg._util.vmsg_r(f'Validating {desc} checksum...')

		if not self.cfg._util.compare_chksums(chk, 'file', make_chksum_6(hstr), 'computed', verbose=True):
			return False

		self.seed = Seed(self.cfg, bytes.fromhex(hstr))
		self.ssdata.chksum = chk

		self.check_usr_seed_len()

		return True
