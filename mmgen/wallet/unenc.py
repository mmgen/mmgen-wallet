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
wallet.unenc: unencrypted wallet base class
"""

from ..color import blue, yellow
from ..util import msg, msg_r, capfirst, is_int
from .base import wallet

class wallet(wallet):

	def _decrypt_retry(self):
		pass

	def _encrypt(self):
		pass

	def _filename(self):
		s = self.seed
		return '{}[{}].{}'.format(s.fn_stem, s.bitlen, self.ext)

	def _print_seed_type(self):
		msg('{} {}'.format(
			blue(f'{capfirst(self.base_type or self.type)} type:'),
			yellow(self.mn_type)
		))

	def _choose_seedlen(self, ok_lens):

		from ..term import get_char
		def choose_len():
			prompt = self.choose_seedlen_prompt
			while True:
				r = get_char('\r'+prompt)
				if is_int(r) and 1 <= int(r) <= len(ok_lens):
					break
			msg_r(('\r', '\n')[self.cfg.test_suite] + ' '*len(prompt) + '\r')
			return ok_lens[int(r)-1]

		while True:
			usr_len = choose_len()
			prompt = self.choose_seedlen_confirm.format(usr_len)
			from ..ui import keypress_confirm
			if keypress_confirm(
					self.cfg,
					prompt,
					default_yes = True,
					no_nl       = not self.cfg.test_suite):
				return usr_len
