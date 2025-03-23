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
proto.eth.tx.completed: Ethereum completed transaction class
"""

from ....tx import completed as TxBase
from .base import Base, TokenBase

class Completed(Base, TxBase.Completed):
	fn_fee_unit = 'Mwei'

	def get_tx_usr_data(self):
		o = self.txobj
		if o['to'] and o['data']:
			return bytes.fromhex(o['data'])

	@property
	def send_amt(self):
		return self.outputs[0].amt if self.outputs else self.proto.coin_amt('0')

	@property
	def fee(self):
		return self.fee_gasPrice2abs(self.txobj['gasPrice'].toWei())

	@property
	def change(self):
		return self.sum_inputs() - self.send_amt - self.fee

	def check_txfile_hex_data(self):
		pass

	def check_sigs(self): # TODO
		from ....util import is_hex_str
		if is_hex_str(self.serialized):
			return True
		return False

	def check_pubkey_scripts(self):
		pass

	def get_serialized_locktime(self):
		return None # TODO

class TokenCompleted(TokenBase, Completed):

	@property
	def change(self):
		return self.sum_inputs() - self.send_amt
