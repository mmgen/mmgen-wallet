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
xmrwallet.ops.label: Monero wallet ops for the MMGen Suite
"""

from ...color import pink, cyan, gray
from ...util import msg, ymsg, gmsg, die, make_timestr
from ...ui import keypress_confirm
from ...obj import TwComment
from ...addr import CoinAddr

from ..rpc import MoneroWalletRPC

from .spec import OpMixinSpec
from .wallet import OpWallet

class OpLabel(OpMixinSpec, OpWallet):
	spec_id  = 'label_spec'
	spec_key = ((1, 'source'),)
	opts     = ()
	wallet_offline = True

	async def main(self, add_timestr='ask', auto=False):

		if not self.compat_call:
			gmsg('\n{a} label for wallet {b}, account #{c}, address #{d}'.format(
				a = 'Setting' if self.label else 'Removing',
				b = self.source.idx,
				c = self.account,
				d = self.address_idx))

		h = MoneroWalletRPC(self, self.source)

		h.open_wallet('source')
		wallet_data = h.get_wallet_data(print=not auto)

		max_acct = len(wallet_data.accts_data['subaddress_accounts']) - 1
		if self.account > max_acct:
			die(2, f'{self.account}: requested account index out of bounds (>{max_acct})')

		ret = h.print_acct_addrs(wallet_data, self.account, silent=auto)

		if self.address_idx > len(ret) - 1:
			die(2, '{}: requested address index out of bounds (>{})'.format(
				self.address_idx,
				len(ret) - 1))

		addr = ret[self.address_idx]
		if self.label and add_timestr == 'ask':
			add_timestr = keypress_confirm(self.cfg, '\n  Add timestamp to label?')
		new_label = TwComment(
			(self.label + (f' [{make_timestr()}]' if add_timestr else '')) if self.label
			else '')

		if not auto:
			ca = CoinAddr(self.proto, addr['address'])
			from . import addr_width
			msg('\n  {a} {b}\n  {c} {d}\n  {e} {f}'.format(
					a = 'Address:       ',
					b = ca.hl(0) if self.cfg.full_address else ca.fmt(0, addr_width, color=True),
					c = 'Existing label:',
					d = pink(addr['label']) if addr['label'] else gray('[none]'),
					e = 'New label:     ',
					f = pink(new_label) if new_label else gray('[none]')))

		op = 'remove' if not new_label else 'update' if addr['label'] else 'set'

		if addr['label'] == new_label:
			ymsg('\nLabel is unchanged, operation cancelled')
		elif auto or keypress_confirm(self.cfg, f'  {op.capitalize()} label?'):
			h.set_label(self.account, self.address_idx, new_label)
			ret = h.print_acct_addrs(h.get_wallet_data(print=False), self.account)
			label_chk = ret[self.address_idx]['label']
			if label_chk != new_label:
				ymsg(f'Warning: new label {label_chk!r} does not match requested value!')
				return False
			else:
				msg(cyan('\nLabel successfully {}'.format('set' if op == 'set' else op+'d')))
				return new_label
		else:
			ymsg('\nOperation cancelled by user request')
