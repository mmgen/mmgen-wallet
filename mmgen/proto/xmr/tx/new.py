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

	async def create(self, cmd_args, **kwargs):
		self.is_sweep = not cmd_args
		self.sweep_spec = None
		return await super().create(cmd_args, **kwargs)

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

		if self.is_sweep:
			if not self.sweep_spec:
				from ....util import ymsg
				ymsg('No transaction operation specified. Exiting')
				return None
			from ....ui import item_chooser
			from ....color import pink
			op = item_chooser(
				self.cfg,
				'Choose the sweep operation type',
				('sweep', 'sweep_all'),
				lambda s: pink(s.upper())).item
			spec = self.sweep_spec
		else:
			op = 'transfer'
			i = self.inputs[0]
			o = self.outputs[0]
			spec = f'{i.idx}:{i.acct_idx}:{o.addr},{o.amt}'

		from ....xmrwallet import op as xmrwallet_op
		op = xmrwallet_op(
			op,
			self.cfg,
			None,
			None,
			spec = spec,
			compat_call = True)

		await op.restart_wallet_daemon()
		return await op.main()
