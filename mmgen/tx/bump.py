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
tx.bump: transaction bump class
"""

from .new import New
from .completed import Completed
from ..opts import opt
from ..util import line_input,is_int,keypress_confirm

class Bump(Completed,New):
	desc = 'fee-bumped transaction'
	ext  = 'rawtx'
	bump_output_idx = None

	def __init__(self,send,*args,**kwargs):

		super().__init__(*args,**kwargs)

		if not self.is_replaceable():
			die(1,f'Transaction {self.txid} is not replaceable')

		# If sending, require original tx to be sent
		if send and not self.coin_txid:
			die(1,'Transaction {self.txid!r} was not broadcast to the network')

		self.coin_txid = ''

	def check_sufficient_funds_for_bump(self):
		if not [o.amt for o in self.outputs if o.amt >= self.min_fee]:
			die(1,
				'Transaction cannot be bumped.\n' +
				f'All outputs contain less than the minimum fee ({self.min_fee} {self.coin})')

	def choose_output(self):
		chg_idx = self.get_chg_output_idx()
		init_reply = opt.output_to_reduce

		def check_sufficient_funds(o_amt):
			if o_amt < self.min_fee:
				msg(f'Minimum fee ({self.min_fee} {self.coin}) is greater than output amount ({o_amt} {self.coin})')
				return False
			return True

		if len(self.outputs) == 1:
			if check_sufficient_funds(self.outputs[0].amt):
				self.bump_output_idx = 0
				return 0
			else:
				die(1,'Insufficient funds to bump transaction')

		while True:
			if init_reply == None:
				m = 'Choose an output to deduct the fee from (Hit ENTER for the change output): '
				reply = line_input(m) or 'c'
			else:
				reply,init_reply = init_reply,None
			if chg_idx == None and not is_int(reply):
				msg('Output must be an integer')
			elif chg_idx != None and not is_int(reply) and reply != 'c':
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
						if opt.yes or keypress_confirm(prompt+'.  OK?',default_yes=True):
							if opt.yes:
								msg(prompt)
							self.bump_output_idx = idx
							return idx