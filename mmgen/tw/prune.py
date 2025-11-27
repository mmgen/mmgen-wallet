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
tw.prune: Tracking wallet pruned listaddresses class for the MMGen suite
"""

from ..util import msg, msg_r, rmsg, ymsg
from ..color import red, green, gray, yellow
from ..obj import ListItemAttr
from .addresses import TwAddresses
from .view import CUR_HOME, ERASE_ALL

class TwAddressesPrune(TwAddresses):

	mod_subpath = 'tw.prune'

	class TwAddress(TwAddresses.TwAddress):
		valid_attrs = TwAddresses.TwAddress.valid_attrs | {'tag'}
		tag = ListItemAttr(bool, typeconv=False, reassign_ok=True)

	async def __init__(self, *args, warn_used=False, **kwargs):
		self.warn_used = warn_used
		await super().__init__(*args, **kwargs)

	def gen_display(self, data, cw, fs, color, fmt_method):

		id_save = data[0].al_id
		yes, no = red('Yes '), green('No  ')

		for n, d in enumerate(data, 1):
			if id_save != d.al_id:
				id_save = d.al_id
				yield ''.ljust(self.term_width)
			yield (
				gray(fmt_method(n, d, cw, fs, False, 'Yes ', 'No  ')) if d.tag else
				fmt_method(n, d, cw, fs, True, yes, no))

	def do_prune(self):

		def gen():
			for n, d in enumerate(self.data, 1):
				if d.tag:
					pruned.append(n)
					if d.amt:
						rmsg(f'Warning: pruned address {d.twmmid.addr} has a balance!')
					elif self.warn_used and d.is_used:
						ymsg(f'Warning: pruned address {d.twmmid.addr} is used!')
				else:
					yield d

		pruned = []
		self.reverse = False
		self.sort_data('twmmid')
		self.data = list(gen())

		return pruned

	class action(TwAddresses.action):

		def get_addrnums(self, parent, desc):
			prompt = f'Enter a range or space-separated list of addresses to {desc}: '
			from ..ui import line_input
			msg('')
			while True:
				reply = line_input(parent.cfg, prompt).strip()
				if reply:
					from ..addrlist import AddrIdxList
					from ..obj import get_obj
					selected = get_obj(AddrIdxList, fmt_str=','.join(reply.split()))
					if selected:
						if selected[-1] <= len(parent.disp_data):
							return selected
						msg(f'Address number must be <= {len(parent.disp_data)}')
				else:
					return []

		def query_user(self, desc, addrnum, e):

			from collections import namedtuple
			md = namedtuple('mdata', ['wmsg', 'prompt'])
			m = {
				'amt': md(
					red('Address #{a} ({b}) has a balance of {c}!'.format(
						a = addrnum,
						b = e.twmmid.addr,
						c = e.amt.hl3(color=False, unit=True))),
					'[p]rune anyway, [P]rune all with balance, [s]kip, [S]kip all with balance: '),
				'used': md(
					yellow('Address #{a} ({b}) is used!'.format(
						a = addrnum,
						b = e.twmmid.addr)),
					'[p]rune anyway, [P]rune all used, [s]kip, [S]kip all used: ')}

			from ..term import get_char
			valid_res = 'pPsS'
			msg(m[desc].wmsg)

			while True:
				res = get_char(m[desc].prompt, immed_chars=valid_res)
				if res in valid_res:
					msg('')
					return {
						#     auto,  prune
						'p': (False, True),
						'P': (True,  True),
						's': (False, False),
						'S': (True,  False),
					}[res]
				else:
					msg('\nInvalid keypress')

		async def a_prune(self, parent):

			def do_entry(desc, n, addrnum, e):
				if auto[desc]:
					return False
				else:
					auto[desc], prune = self.query_user(desc, addrnum, e)
					dfl[desc] = auto[desc] and prune
					skip_all_used = auto['used'] and not dfl['used']
					if auto[desc]: # we’ve switched to auto mode, so go back and fix up all previous entries
						for idx in addrnums[:n]:
							e = parent.disp_data[idx-1]
							if skip_all_used and e.is_used:
								e.tag = False
							elif desc == 'amt' and e.amt:
								e.tag = prune
							elif desc == 'used' and (e.is_used and not e.amt):
								e.tag = prune
					# skipping all used addrs implies skipping all addrs with balances
					if skip_all_used:
						auto['amt'] = True
						dfl['amt'] = False
					return prune

			addrnums = self.get_addrnums(parent, 'prune')

			dfl  = {'amt': False, 'used': False}  # default prune policy for given property (has amt, is used)
			auto = {'amt': False,  'used': False} # whether to ask the user, or apply default policy automatically

			for n, addrnum in enumerate(addrnums):
				e = parent.disp_data[addrnum-1]
				if e.amt and not dfl['amt']:
					e.tag = do_entry('amt', n, addrnum, e)
				elif parent.warn_used and (e.is_used and not e.amt) and not dfl['used']:
					e.tag = do_entry('used', n, addrnum, e)
				else:
					e.tag = True

			if parent.scroll:
				msg_r(CUR_HOME + ERASE_ALL)

		async def a_unprune(self, parent):
			for addrnum in self.get_addrnums(parent, 'unprune'):
				parent.disp_data[addrnum-1].tag = False

			if parent.scroll:
				msg_r(CUR_HOME + ERASE_ALL)

		async def a_clear_prune_list(self, parent):
			for d in parent.data:
				d.tag = False
