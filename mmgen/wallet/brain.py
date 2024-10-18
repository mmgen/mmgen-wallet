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
wallet.brain: brainwallet wallet class
"""

from ..util import msg
from ..color import yellow
from .enc import wallet
from .seed import Seed

class wallet(wallet):

	stdin_ok = True
	desc = 'brainwallet'
	# brainwallet warning message? TODO

	def get_bw_params(self):
		# already checked
		a = self.cfg.brain_params.split(',')
		return int(a[0]), a[1]

	def _deformat(self):
		self.brainpasswd = ' '.join(self.fmt_data.split())
		return True

	def _decrypt(self):
		d = self.ssdata
		if self.cfg.brain_params:
			bw_seed_len, d.hash_preset = self.get_bw_params()
		else:
			if not self.cfg.seed_len:
				self.cfg._util.qmsg(f'Using default seed length of {yellow(str(Seed.dfl_len))} bits\n'
					+ 'If this is not what you want, use the --seed-len option')
			self._get_hash_preset()
			bw_seed_len = self.cfg.seed_len or Seed.dfl_len
		self.cfg._util.qmsg_r('Hashing brainwallet data.  Please wait...')
		# Use buflen arg of scrypt.hash() to get seed of desired length
		seed = self.crypto.scrypt_hash_passphrase(
			self.brainpasswd.encode(),
			b'',
			d.hash_preset,
			buflen = bw_seed_len // 8)
		self.cfg._util.qmsg('Done')
		self.seed = Seed(self.cfg, seed)
		msg(f'Seed ID: {self.seed.sid}')
		self.cfg._util.qmsg('Check this value against your records')
		return True

	def _format(self):
		raise NotImplementedError('Brainwallet not supported as an output format')

	def _encrypt(self):
		raise NotImplementedError('Brainwallet not supported as an output format')
