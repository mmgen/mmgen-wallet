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
wallet.mnemonic: MMGen mnemonic wallet base class
"""

from ..baseconv import baseconv
from ..util import msg
from ..seed import Seed
from .unenc import wallet

class wallet(wallet):

	stdin_ok = True
	conv_cls = baseconv
	choose_seedlen_prompt = 'Choose a mnemonic length: 1) 12 words, 2) 18 words, 3) 24 words: '
	choose_seedlen_confirm = 'Mnemonic length of {} words chosen. OK?'

	@property
	def mn_lens(self):
		return sorted(self.conv_cls(self.wl_id).seedlen_map_rev)

	def _get_data_from_user(self, desc):

		if not self.cfg.stdin_tty:
			from ..ui import get_data_from_user
			return get_data_from_user(self.cfg, desc=desc)

		self._print_seed_type()

		if self.cfg.seed_len:
			from ..obj import Int
			msg('Using seed length {} (user-configured)'.format(Int(self.cfg.seed_len).hl()))
			mn_len = self.conv_cls(self.wl_id).seedlen_map[self.cfg.seed_len // 8]
		else:
			mn_len = self._choose_seedlen(self.mn_lens)

		from ..mn_entry import mn_entry
		self.mnemonic = mn_entry(self.cfg, self.wl_id)

		return self.mnemonic.get_mnemonic_from_user(mn_len)

	def _format(self):

		seed = self.seed.data

		bc = self.conv_cls(self.wl_id)
		mn  = bc.frombytes(seed, pad='seed')
		rev = bc.tobytes(mn, pad='seed')

		# Internal error, so just die on fail
		self.cfg._util.compare_or_die(rev, 'recomputed seed', seed, 'original seed', e='Internal error')

		self.ssdata.mnemonic = mn
		self.fmt_data = ' '.join(mn) + '\n'

	def _deformat(self):

		bc = self.conv_cls(self.wl_id)
		mn = self.fmt_data.split()

		if len(mn) not in self.mn_lens:
			msg('Invalid mnemonic ({} words).  Valid numbers of words: {}'.format(
				len(mn),
				', '.join(map(str, self.mn_lens))))
			return False

		for n, w in enumerate(mn, 1):
			if w not in bc.digits:
				msg(f'Invalid mnemonic: word #{n} is not in the {self.wl_id.upper()} wordlist')
				return False

		seed = bc.tobytes(mn, pad='seed')
		rev  = bc.frombytes(seed, pad='seed')

		if len(seed) * 8 not in Seed.lens:
			msg('Invalid mnemonic (produces too large a number)')
			return False

		# Internal error, so just die:
		self.cfg._util.compare_or_die(
			val1  = ' '.join(rev),
			val2  = ' '.join(mn),
			desc1 = 'recomputed mnemonic',
			desc2 = 'original mnemonic',
			e     = 'Internal error')

		self.seed = Seed(self.cfg, seed_bin=seed)
		self.ssdata.mnemonic = mn

		self.check_usr_seed_len()

		return True
