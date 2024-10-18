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
xmrwallet.ops.label: Monero wallet ops for the MMGen Suite
"""

from ...color import red, pink, cyan, gray
from ...util import msg, ymsg, gmsg, die, make_timestr
from ...ui import keypress_confirm
from ...addr import CoinAddr

from ..rpc import MoneroWalletRPC

from .spec import OpMixinSpec
from .wallet import OpWallet

class OpLabel(OpMixinSpec, OpWallet):
	spec_id  = 'label_spec'
	spec_key = ((1, 'source'),)
	opts     = ()
	wallet_offline = True

	async def main(self):

		gmsg('\n{a} label for wallet {b}, account #{c}, address #{d}'.format(
			a = 'Setting' if self.label else 'Removing',
			b = self.source.idx,
			c = self.account,
			d = self.address_idx
		))
		h = MoneroWalletRPC(self, self.source)

		h.open_wallet('source')
		wallet_data = h.get_wallet_data()

		max_acct = len(wallet_data.accts_data['subaddress_accounts']) - 1
		if self.account > max_acct:
			die(2, f'{self.account}: requested account index out of bounds (>{max_acct})')

		ret = h.print_acct_addrs(wallet_data, self.account)

		if self.address_idx > len(ret) - 1:
			die(2, '{}: requested address index out of bounds (>{})'.format(
				self.address_idx,
				len(ret) - 1))

		addr = ret[self.address_idx]
		new_label = f'{self.label} [{make_timestr()}]' if self.label else ''

		ca = CoinAddr(self.proto, addr['address'])
		from . import addr_width
		msg('\n  {a} {b}\n  {c} {d}\n  {e} {f}'.format(
				a = 'Address:       ',
				b = ca.hl(0) if self.cfg.full_address else ca.fmt(0, color=True, width=addr_width),
				c = 'Existing label:',
				d = pink(addr['label']) if addr['label'] else gray('[none]'),
				e = 'New label:     ',
				f = pink(new_label) if new_label else gray('[none]')))

		op = 'remove' if not new_label else 'update' if addr['label'] else 'set'

		if addr['label'] == new_label:
			ymsg('\nLabel is unchanged, operation cancelled')
		elif keypress_confirm(self.cfg, f'  {op.capitalize()} label?'):
			h.set_label(self.account, self.address_idx, new_label)
			ret = h.print_acct_addrs(h.get_wallet_data(print=False), self.account)
			label_chk = ret[self.address_idx]['label']
			if label_chk != new_label:
				ymsg(f'Warning: new label {label_chk!r} does not match requested value!')
				return False
			else:
				msg(cyan('\nLabel successfully {}'.format('set' if op == 'set' else op+'d')))
		else:
			ymsg('\nOperation cancelled by user request')
