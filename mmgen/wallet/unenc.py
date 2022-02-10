#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
wallet.unenc: unencrypted wallet base class
"""

from ..globalvars import g
from ..color import blue,yellow
from ..util import msg,msg_r,capfirst,is_int,keypress_confirm
from .base import wallet

class wallet(wallet):

	def _decrypt_retry(self):
		pass

	def _encrypt(self):
		pass

	def _filename(self):
		s = self.seed
		return '{}[{}]{x}.{}'.format(
			s.fn_stem,
			s.bitlen,
			self.ext,
			x='-α' if g.debug_utf8 else '')

	def _choose_seedlen(self,ok_lens):

		from ..term import get_char
		def choose_len():
			prompt = self.choose_seedlen_prompt
			while True:
				r = get_char('\r'+prompt)
				if is_int(r) and 1 <= int(r) <= len(ok_lens):
					break
			msg_r(('\r','\n')[g.test_suite] + ' '*len(prompt) + '\r')
			return ok_lens[int(r)-1]

		msg('{} {}'.format(
			blue(f'{capfirst(self.base_type or self.type)} type:'),
			yellow(self.mn_type)
		))

		while True:
			usr_len = choose_len()
			prompt = self.choose_seedlen_confirm.format(usr_len)
			if keypress_confirm(prompt,default_yes=True,no_nl=not g.test_suite):
				return usr_len