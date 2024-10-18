#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.eth.tx.signed: Ethereum signed transaction class
"""

from ....tx import signed as TxBase
from ....obj import CoinTxID, ETHNonce, HexStr
from ....addr import CoinAddr, TokenAddr
from .completed import Completed, TokenCompleted

class Signed(Completed, TxBase.Signed):

	desc = 'signed transaction'

	def parse_txfile_serialized_data(self):
		from ..pyethereum.transactions import Transaction
		from .. import rlp
		etx = rlp.decode(bytes.fromhex(self.serialized), Transaction)
		d = etx.to_dict() # ==> hex values have '0x' prefix, 0 is '0x'
		for k in ('sender', 'to', 'data'):
			if k in d:
				d[k] = d[k].replace('0x', '', 1)
		o = {
			'from':     CoinAddr(self.proto, d['sender']),
			# NB: for token, 'to' is token address
			'to':       CoinAddr(self.proto, d['to']) if d['to'] else None,
			'amt':      self.proto.coin_amt(d['value'], from_unit='wei'),
			'gasPrice': self.proto.coin_amt(d['gasprice'], from_unit='wei'),
			'startGas': self.proto.coin_amt(d['startgas'], from_unit='wei'),
			'nonce':    ETHNonce(d['nonce']),
			'data':     HexStr(d['data']) }
		if o['data'] and not o['to']: # token- or contract-creating transaction
			# NB: could be a non-token contract address:
			o['token_addr'] = TokenAddr(self.proto, etx.creates.hex())
			self.disable_fee_check = True
		txid = CoinTxID(etx.hash.hex())
		assert txid == self.coin_txid, "txid in tx.serialized doesn't match value in MMGen transaction file"
		self.gas = o['startGas'] # approximate, but better than nothing
		self.txobj = o
		return d # 'token_addr', 'decimals' required by Token subclass

class TokenSigned(TokenCompleted, Signed):
	desc = 'signed transaction'

	def parse_txfile_serialized_data(self):
		raise NotImplementedError(
			'Signed transaction files cannot be parsed offline, because tracking wallet is required!')

class AutomountSigned(TxBase.AutomountSigned, Signed):
	pass

class TokenAutomountSigned(TxBase.AutomountSigned, TokenSigned):
	pass
