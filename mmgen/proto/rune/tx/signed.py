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
proto.rune.tx.signed: THORChain signed transaction class
"""

from ....tx import signed as TxBase
from ....obj import CoinTxID, NonNegativeInt
from .completed import Completed

class Signed(Completed, TxBase.Signed):

	desc = 'signed transaction'

	def parse_txfile_serialized_data(self):
		from .protobuf import RuneTx
		tx = RuneTx.loads(bytes.fromhex(self.serialized))

		b = tx.body.messages[0].body
		i = tx.authInfo

		from_k, amt_k = ('signer', 'coins') if self.is_swap else ('fromAddress', 'amount')

		self.txobj = {
			'from':     self.proto.encode_addr_bech32x(getattr(b, from_k)),
			'to':       None if self.is_swap else self.proto.encode_addr_bech32x(b.toAddress),
			'amt':      self.proto.coin_amt(int(getattr(b, amt_k)[0].amount), from_unit='satoshi'),
			'gas':      NonNegativeInt(i.fee.gasLimit),
			'sequence': NonNegativeInt(i.signerInfos[0].sequence)}

		txid = CoinTxID(tx.txid)
		assert txid == self.coin_txid, 'serialized txid doesn’t match txid in MMGen transaction file'

class AutomountSigned(TxBase.AutomountSigned, Signed):
	pass
