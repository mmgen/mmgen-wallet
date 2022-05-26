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
wallet.dieroll: dieroll wallet class
"""

import time
from ..globalvars import g
from ..opts import opt
from ..util import msg,msg_r,die,fmt,block_format,remove_whitespace,keypress_confirm
from ..seed import Seed
from ..baseconv import baseconv
from .unenc import wallet

class wallet(wallet):

	stdin_ok = True
	desc = 'base6d die roll seed data'
	conv_cls = baseconv
	wl_id = 'b6d'
	mn_type = 'base6d'
	choose_seedlen_prompt = 'Choose a seed length: 1) 128 bits, 2) 192 bits, 3) 256 bits: '
	choose_seedlen_confirm = 'Seed length of {} bits chosen. OK?'
	user_entropy_prompt = 'Would you like to provide some additional entropy from the keyboard?'
	interactive_input = False

	def _format(self):
		d = baseconv('b6d').frombytes(self.seed.data,pad='seed',tostr=True) + '\n'
		self.fmt_data = block_format(d,gw=5,cols=5)

	def _deformat(self):

		d = remove_whitespace(self.fmt_data)
		bc = baseconv('b6d')
		rmap = bc.seedlen_map_rev

		if not len(d) in rmap:
			die( 'SeedLengthError', '{!r}: invalid length for {} (must be one of {})'.format(
				len(d),
				self.desc,
				list(rmap) ))

		# truncate seed to correct length, discarding high bits
		seed_len = rmap[len(d)]
		seed_bytes = bc.tobytes( d, pad='seed' )[-seed_len:]

		if self.interactive_input and opt.usr_randchars:
			if keypress_confirm(self.user_entropy_prompt):
				from ..crypto import add_user_random
				seed_bytes = add_user_random(
					rand_bytes = seed_bytes,
					desc       = 'gathered from your die rolls' )
				self.desc += ' plus user-supplied entropy'

		self.seed = Seed(seed_bytes)
		self.ssdata.hexseed = seed_bytes.hex()

		self.check_usr_seed_len()
		return True

	def _get_data_from_user(self,desc):

		if not g.stdin_tty:
			return get_data_from_user(desc)

		bc = baseconv('b6d')

		seed_bitlen = self._choose_seedlen([ n*8 for n in sorted(bc.seedlen_map) ])
		nDierolls = bc.seedlen_map[seed_bitlen // 8]

		message = """
			For a {sb}-bit seed you must roll the die {nd} times.  After each die roll,
			enter the result on the keyboard as a digit.  If you make an invalid entry,
			you'll be prompted to re-enter it.
		"""
		msg('\n'+fmt(message.strip()).format(sb=seed_bitlen,nd=nDierolls)+'\n')

		CUR_HIDE = '\033[?25l'
		CUR_SHOW = '\033[?25h'
		cr = '\n' if g.test_suite else '\r'
		prompt_fs = f'\b\b\b   {cr}Enter die roll #{{}}: {CUR_SHOW}'
		clear_line = '' if g.test_suite else '\r' + ' ' * 25
		invalid_msg = CUR_HIDE + cr + 'Invalid entry' + ' ' * 11

		from ..term import get_char
		def get_digit(n):
			p = prompt_fs
			while True:
				time.sleep(g.short_disp_timeout)
				ch = get_char(p.format(n),num_chars=1)
				if ch in bc.digits:
					msg_r(CUR_HIDE + ' OK')
					return ch
				else:
					msg_r(invalid_msg)
					sleep = g.err_disp_timeout
					p = clear_line + prompt_fs

		dierolls,n = [],1
		while len(dierolls) < nDierolls:
			dierolls.append(get_digit(n))
			n += 1

		msg('Die rolls successfully entered' + CUR_SHOW)
		self.interactive_input = True

		return ''.join(dierolls)
