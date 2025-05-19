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
tx.bump: transaction bump class
"""

from .new_swap import NewSwap
from .completed import Completed
from ..util import msg, ymsg, is_int, die
from ..color import orange, pink

class Bump(Completed, NewSwap):
	desc = 'fee-bumped transaction'
	ext  = 'rawtx'
	bump_output_idx = None
	is_bump = True

	def __init__(self, *, check_sent, new_outputs, **kwargs):

		super().__init__(**kwargs)

		self.new_outputs = new_outputs
		self.orig_rel_fee = self.get_orig_rel_fee()

		if new_outputs:
			if self.is_swap:
				self.is_swap = False
				for attr in self.swap_attrs:
					setattr(self, attr, None)
			self.outputs = self.OutputList(self)
			self.cfg = kwargs['cfg'] # must use current cfg opts, not those from orig_tx
		elif self.is_swap and self.is_token:
			die(1,
				orange('Fee-bumping of token swap transactions currently not supported.\n') +
				orange('To bump the transaction, supply new outputs on the command line'))

		if not self.is_replaceable():
			die(1, f'Transaction {self.txid} is not replaceable')

		# If sending, require original tx to be sent
		if check_sent and not self.coin_txid:
			die(1, f'Transaction {self.txid!r} was not broadcast to the network')

		self.coin_txid = ''
		self.sent_timestamp = None

	async def get_inputs(self, outputs_sum):
		return True

	def check_bumped_fee_ok(self, abs_fee):
		from ..amt import RelFeeAmt
		orig = RelFeeAmt(self.orig_rel_fee)
		new = RelFeeAmt(self.fee_abs2rel(abs_fee))
		if new <= orig:
			fs = 'New fee ({b!s} {d}) <= original fee ({a!s} {d})\nPlease choose a higher fee'
			ymsg(fs.format(a=orig, b=new, d=self.rel_fee_disp))
			return False
		return True

	async def create_feebump(self, silent):

		from ..rpc import rpc_init
		self.rpc = await rpc_init(self.cfg, self.proto)

		msg('Creating replacement transaction')

		self.check_sufficient_funds_for_bump()

		output_idx = self.choose_output()

		await self.set_gas(force=True)

		if not silent:
			msg('Minimum fee for new transaction: {} {} ({} {})'.format(
				self.min_fee.hl(),
				self.proto.coin,
				pink(self.fee_abs2rel(self.min_fee)),
				self.rel_fee_disp))

		if self.is_swap:
			self.recv_proto = self.check_swap_memo().proto
			self.swap_cfg = self.swap_proto_mod.SwapCfg(self.cfg)
			fee_hint = await self.update_vault_output(self.send_amt)
		else:
			fee_hint = None

		self.usr_fee = self.get_usr_fee_interactive(
			fee = self.cfg.fee or fee_hint,
			desc = 'User-selected' if self.cfg.fee else 'Recommended' if fee_hint else None)

		self.bump_fee(output_idx, self.usr_fee)

		assert self.fee <= self.proto.max_tx_fee

		if not self.cfg.yes:
			self.add_comment()   # edits an existing comment

		await self.create_serialized()

		self.add_timestamp()
		self.add_blockcount()

		self.cfg._util.qmsg('Fee successfully increased')

	def check_sufficient_funds_for_bump(self):
		if not [o.amt for o in self.outputs if o.amt >= self.min_fee]:
			die(1,
				'Transaction cannot be bumped.\n' +
				f'All outputs contain less than the minimum fee ({self.min_fee} {self.coin})')

	def choose_output(self):

		def check_sufficient_funds(o_amt):
			if o_amt < self.min_fee:
				msg(f'Minimum fee ({self.min_fee} {self.coin}) is greater than output amount ({o_amt} {self.coin})')
				return False
			return True

		if len(self.nondata_outputs) == 1:
			if check_sufficient_funds(self.nondata_outputs[0].amt):
				self.bump_output_idx = 0
				return 0
			else:
				die(1, 'Insufficient funds to bump transaction')

		init_reply = self.cfg.output_to_reduce
		chg_idx = self.chg_idx

		while True:
			if init_reply is None:
				from ..ui import line_input
				m = 'Choose an output to deduct the fee from (Hit ENTER for the change output): '
				reply = line_input(self.cfg, m) or 'c'
			else:
				reply, init_reply = init_reply, None
			if chg_idx is None and not is_int(reply):
				msg('Output must be an integer')
			elif chg_idx is not None and not is_int(reply) and reply != 'c':
				msg("Output must be an integer, or 'c' for the change output")
			else:
				idx = chg_idx if reply == 'c' else (int(reply) - 1)
				if idx < 0 or idx >= len(self.outputs):
					msg(f'Output must be in the range 1-{len(self.outputs)}')
				else:
					o_amt = self.outputs[idx].amt
					cm = ' (change output)' if chg_idx == idx else ''
					prompt = f'Fee will be deducted from output {idx+1}{cm} ({o_amt} {self.coin})'
					if check_sufficient_funds(o_amt):
						if self.cfg.yes:
							msg(prompt)
						else:
							from ..ui import keypress_confirm
							if not keypress_confirm(self.cfg, prompt+'.  OK?', default_yes=True):
								continue
						self.bump_output_idx = idx
						return idx
