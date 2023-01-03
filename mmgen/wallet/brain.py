#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
wallet.brain: brainwallet wallet class
"""

from ..opts import opt
from ..util import msg,qmsg,qmsg_r
from ..color import yellow
from .enc import wallet
from .seed import Seed
import mmgen.crypto as crypto

class wallet(wallet):

	stdin_ok = True
	desc = 'brainwallet'
	# brainwallet warning message? TODO

	def get_bw_params(self):
		# already checked
		a = opt.brain_params.split(',')
		return int(a[0]),a[1]

	def _deformat(self):
		self.brainpasswd = ' '.join(self.fmt_data.split())
		return True

	def _decrypt(self):
		d = self.ssdata
		if opt.brain_params:
			"""
			Don't set opt.seed_len!  When using multiple wallets, BW seed len might differ from others
			"""
			bw_seed_len,d.hash_preset = self.get_bw_params()
		else:
			if not opt.seed_len:
				qmsg(f'Using default seed length of {yellow(str(Seed.dfl_len))} bits\n'
					+ 'If this is not what you want, use the --seed-len option' )
			self._get_hash_preset()
			bw_seed_len = opt.seed_len or Seed.dfl_len
		qmsg_r('Hashing brainwallet data.  Please wait...')
		# Use buflen arg of scrypt.hash() to get seed of desired length
		seed = crypto.scrypt_hash_passphrase(
			self.brainpasswd.encode(),
			b'',
			d.hash_preset,
			buflen = bw_seed_len // 8 )
		qmsg('Done')
		self.seed = Seed(seed)
		msg(f'Seed ID: {self.seed.sid}')
		qmsg('Check this value against your records')
		return True

	def _format(self):
		raise NotImplementedError('Brainwallet not supported as an output format')

	def _encrypt(self):
		raise NotImplementedError('Brainwallet not supported as an output format')
