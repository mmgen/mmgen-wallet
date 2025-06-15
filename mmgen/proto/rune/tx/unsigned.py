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
proto.rune.tx.unsigned: THORChain unsigned transaction class
"""

from ....tx import unsigned as TxBase
from ....obj import CoinTxID, NonNegativeInt
from ....addr import CoinAddr

from ...vm.tx.unsigned import Unsigned as VmUnsigned

from .completed import Completed

class Unsigned(VmUnsigned, Completed, TxBase.Unsigned):

	def parse_txfile_serialized_data(self):
		d = self.serialized
		self.txobj = {
			'from':           CoinAddr(self.proto, d['from']),
			'to':             CoinAddr(self.proto, d['to']) if d['to'] else None,
			'amt':            self.proto.coin_amt(d['amt']),
			'gas':            NonNegativeInt(d['gas']),
			'account_number': NonNegativeInt(d['account_number']),
			'sequence':       NonNegativeInt(d['sequence']),
			'chain_id':       d['chain_id']}

	async def do_sign(self, o, wif):
		if self.is_swap:
			from .protobuf import swap_tx_parms, build_swap_tx as build_tx
			parms = swap_tx_parms(
				o['from'],
				o['amt'],
				o['gas'],
				o['account_number'],
				o['sequence'],
				self.swap_memo,
				wifkey = wif)
		else:
			from .protobuf import send_tx_parms, build_tx
			parms = send_tx_parms(
				o['from'],
				o['to'],
				o['amt'],
				o['gas'],
				o['account_number'],
				o['sequence'],
				wifkey = wif)

		tx = build_tx(self.cfg, self.proto, parms)
		self.serialized = bytes(tx).hex()
		self.coin_txid = CoinTxID(tx.txid)
		tx.verify_sig(self.proto, o['account_number'])

class AutomountUnsigned(TxBase.AutomountUnsigned, Unsigned):
	pass
