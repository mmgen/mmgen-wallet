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
tx.new_swap: new swap transaction class
"""

from .new import New

class NewSwap(New):
	desc = 'swap transaction'

	def __init__(self, *args, **kwargs):
		import importlib
		self.is_swap = True
		self.swap_proto = kwargs['cfg'].swap_proto
		self.swap_proto_mod = importlib.import_module(f'mmgen.swap.proto.{self.swap_proto}')
		New.__init__(self, *args, **kwargs)

	def update_vault_output(self, amt, *, deduct_est_fee=False):
		sp = self.swap_proto_mod
		c = sp.rpc_client(self, amt)

		from ..util import msg
		from ..term import get_char
		while True:
			self.cfg._util.qmsg(f'Retrieving data from {c.rpc.host}...')
			c.get_quote()
			self.cfg._util.qmsg('OK')
			msg(c.format_quote(deduct_est_fee=deduct_est_fee))
			ch = get_char('Press ‘r’ to refresh quote, any other key to continue: ')
			msg('')
			if ch not in 'Rr':
				break

		self.swap_quote_expiry = c.data['expiry']
		self.update_vault_addr(c.inbound_address)
		return c.rel_fee_hint
