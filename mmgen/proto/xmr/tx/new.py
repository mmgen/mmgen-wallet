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
proto.xmr.tx.new: Monero new transaction class
"""

from ....tx.new import New as TxNew

from .base import Base

class New(Base, TxNew):

	async def get_input_addrs_from_inputs_opt(self):
		return [] # TODO

	async def set_gas(self):
		pass

	async def get_fee(self, fee, outputs_sum, start_fee_desc):
		return True

	def copy_inputs_from_tw(self, tw_unspent_data):
		self.inputs = tw_unspent_data

	def get_unspent_nums_from_user(self, accts_data):
		from ....util import msg, is_int
		from ....ui import line_input
		prompt = 'Enter an account number to spend from: '
		while True:
			if reply := line_input(self.cfg, prompt).strip():
				if is_int(reply) and 1 <= int(reply) <= len(accts_data):
					return [int(reply)]
				msg(f'Account number must be an integer between 1 and {len(accts_data)} inclusive')

	async def compat_create(self):
		from ....xmrwallet import op as xmrwallet_op
		i = self.inputs[0]
		o = self.outputs[0]
		op = xmrwallet_op(
			'transfer',
			self.cfg,
			None,
			None,
			spec = f'{i.idx}:{i.acct_idx}:{o.addr},{o.amt}',
			compat_call = True)
		await op.restart_wallet_daemon()
		return await op.main()
