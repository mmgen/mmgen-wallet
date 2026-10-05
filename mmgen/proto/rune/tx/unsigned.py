# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
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
			'fee':            None if d['fee'] is None else self.proto.coin_amt(d['fee']),
			'gas':            NonNegativeInt(d['gas']),
			'account_number': NonNegativeInt(d['account_number']),
			'sequence':       NonNegativeInt(d['sequence']),
			'chain_id':       d['chain_id']}

	async def do_sign(self, o, wif):
		parms = {
			'from_addr':      o['from'],
			'amt':            o['amt'],
			'gas_limit':      o['gas'],
			'account_number': o['account_number'],
			'sequence':       o['sequence'],
			'fee':            0 if o['fee'] is None else o['fee'].to_unit('atomic'),
			'wifkey':         wif}

		if self.is_swap:
			from .protobuf import swap_tx_parms as tx_parms
			add_parms = {'memo': self.swap_memo}
		else:
			from .protobuf import send_tx_parms as tx_parms
			add_parms = {'to_addr': o['to']}

		from .protobuf import build_tx
		tx = build_tx(self.cfg, self.proto, tx_parms(**(parms | add_parms)))
		self.serialized = bytes(tx).hex()
		self.coin_txid = CoinTxID(tx.txid)
		tx.verify_sig(self.cfg, self.proto, o['account_number'])

class AutomountUnsigned(TxBase.AutomountUnsigned, Unsigned):
	pass
