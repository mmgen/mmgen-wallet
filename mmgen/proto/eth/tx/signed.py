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
base_proto.ethereum.tx.signed: Ethereum signed transaction class
"""

import mmgen.tx.signed as TxBase
from .completed import Completed,TokenCompleted
from ..contract import Token
from ....obj import Str,CoinTxID,ETHNonce,HexStr
from ....addr import CoinAddr,TokenAddr
from ....amt import ETHAmt

class Signed(Completed,TxBase.Signed):

	desc = 'signed transaction'

	def parse_txfile_serialized_data(self):
		from ..pyethereum.transactions import Transaction
		from .. import rlp
		etx = rlp.decode(bytes.fromhex(self.serialized),Transaction)
		d = etx.to_dict() # ==> hex values have '0x' prefix, 0 is '0x'
		for k in ('sender','to','data'):
			if k in d:
				d[k] = d[k].replace('0x','',1)
		o = {
			'from':     CoinAddr(self.proto,d['sender']),
			# NB: for token, 'to' is token address
			'to':       CoinAddr(self.proto,d['to']) if d['to'] else Str(''),
			'amt':      ETHAmt(d['value'],'wei'),
			'gasPrice': ETHAmt(d['gasprice'],'wei'),
			'startGas': ETHAmt(d['startgas'],'wei'),
			'nonce':    ETHNonce(d['nonce']),
			'data':     HexStr(d['data']) }
		if o['data'] and not o['to']: # token- or contract-creating transaction
			# NB: could be a non-token contract address:
			o['token_addr'] = TokenAddr(self.proto,etx.creates.hex())
			self.disable_fee_check = True
		txid = CoinTxID(etx.hash.hex())
		assert txid == self.coin_txid,"txid in tx.serialized doesn't match value in MMGen transaction file"
		self.tx_gas = o['startGas'] # approximate, but better than nothing
		self.txobj = o
		return d # 'token_addr','decimals' required by Token subclass

class TokenSigned(TokenCompleted,Signed):
	desc = 'signed transaction'

	def parse_txfile_serialized_data(self):
		raise NotImplementedError(
			'Signed transaction files cannot be parsed offline, because tracking wallet is required!')
