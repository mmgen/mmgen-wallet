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

	def process_swap_options(self):
		if s := self.cfg.trade_limit:
			self.usr_trade_limit = (
				1 - float(s[:-1]) / 100 if s.endswith('%') else
				self.recv_proto.coin_amt(self.cfg.trade_limit))
		else:
			self.usr_trade_limit = None

	def update_vault_output(self, amt, *, deduct_est_fee=False):
		sp = self.swap_proto_mod
		c = sp.rpc_client(self, amt)

		from ..util import msg
		from ..term import get_char

		def get_trade_limit():
			if type(self.usr_trade_limit) is self.recv_proto.coin_amt:
				return self.usr_trade_limit
			elif type(self.usr_trade_limit) is float:
				return (
					self.recv_proto.coin_amt(int(c.data['expected_amount_out']), from_unit='satoshi')
					* self.usr_trade_limit)

		while True:
			self.cfg._util.qmsg(f'Retrieving data from {c.rpc.host}...')
			c.get_quote()
			trade_limit = get_trade_limit()
			self.cfg._util.qmsg('OK')
			msg(c.format_quote(trade_limit, self.usr_trade_limit, deduct_est_fee=deduct_est_fee))
			ch = get_char('Press ‘r’ to refresh quote, any other key to continue: ')
			msg('')
			if ch not in 'Rr':
				break

		self.swap_quote_expiry = c.data['expiry']
		self.update_vault_addr(c.inbound_address)
		self.update_data_output(trade_limit)
		return c.rel_fee_hint
