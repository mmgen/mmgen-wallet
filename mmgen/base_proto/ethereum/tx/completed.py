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
base_proto.ethereum.tx.completed: Ethereum completed transaction class
"""

import mmgen.tx.completed as TxBase
from .base import Base,TokenBase

class Completed(Base,TxBase.Completed):
	fn_fee_unit = 'Mwei'

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

	def strfmt_locktime(self,locktime=None,terse=False):
		pass

	def get_serialized_locktime(self):
		return None # TODO

class TokenCompleted(TokenBase,Completed):

	@property
	def change(self):
		return self.sum_inputs() - self.send_amt
