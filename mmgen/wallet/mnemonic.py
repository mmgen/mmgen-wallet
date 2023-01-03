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
wallet.mnemonic: MMGen mnemonic wallet base class
"""

from ..globalvars import g
from ..baseconv import baseconv
from ..util import msg,compare_or_die
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

	def _get_data_from_user(self,desc):

		if not g.stdin_tty:
			from ..ui import get_data_from_user
			return get_data_from_user(desc)

		from ..mn_entry import mn_entry # import here to catch cfg var errors
		mn_len = self._choose_seedlen( self.mn_lens )
		return mn_entry(self.wl_id).get_mnemonic_from_user(mn_len)

	def _format(self):

		hexseed = self.seed.hexdata

		bc = self.conv_cls(self.wl_id)
		mn  = bc.fromhex( hexseed, 'seed' )
		rev = bc.tohex( mn, 'seed' )

		# Internal error, so just die on fail
		compare_or_die( rev, 'recomputed seed', hexseed, 'original', e='Internal error' )

		self.ssdata.mnemonic = mn
		self.fmt_data = ' '.join(mn) + '\n'

	def _deformat(self):

		bc = self.conv_cls(self.wl_id)
		mn = self.fmt_data.split()

		if len(mn) not in self.mn_lens:
			msg('Invalid mnemonic ({} words).  Valid numbers of words: {}'.format(
				len(mn),
				', '.join(map(str,self.mn_lens)) ))
			return False

		for n,w in enumerate(mn,1):
			if w not in bc.digits:
				msg(f'Invalid mnemonic: word #{n} is not in the {self.wl_id.upper()} wordlist')
				return False

		hexseed = bc.tohex( mn, 'seed' )
		rev     = bc.fromhex( hexseed, 'seed' )

		if len(hexseed) * 4 not in Seed.lens:
			msg('Invalid mnemonic (produces too large a number)')
			return False

		# Internal error, so just die
		compare_or_die( ' '.join(rev), 'recomputed mnemonic', ' '.join(mn), 'original', e='Internal error' )

		self.seed = Seed(bytes.fromhex(hexseed))
		self.ssdata.mnemonic = mn

		self.check_usr_seed_len()

		return True
