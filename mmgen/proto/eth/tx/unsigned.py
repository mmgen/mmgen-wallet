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
proto.eth.tx.unsigned: Ethereum unsigned transaction class
"""

import json

from ....tx import unsigned as TxBase
from ....util import msg, msg_r
from ....obj import CoinTxID, ETHNonce, Int, HexStr
from ....addr import CoinAddr, TokenAddr
from ..contract import Token
from .completed import Completed, TokenCompleted

class Unsigned(Completed, TxBase.Unsigned):
	desc = 'unsigned transaction'

	def parse_txfile_serialized_data(self):
		d = json.loads(self.serialized)
		o = {
			'from':     CoinAddr(self.proto, d['from']),
			# NB: for token, 'to' is sendto address
			'to':       CoinAddr(self.proto, d['to']) if d['to'] else None,
			'amt':      self.proto.coin_amt(d['amt']),
			'gasPrice': self.proto.coin_amt(d['gasPrice']),
			'startGas': self.proto.coin_amt(d['startGas']),
			'nonce':    ETHNonce(d['nonce']),
			'chainId':  None if d['chainId'] == 'None' else Int(d['chainId']),
			'data':     HexStr(d['data'])}
		self.gas = o['startGas'] # approximate, but better than nothing
		self.txobj = o
		return d # 'token_addr', 'decimals' required by Token subclass

	async def do_sign(self, wif):
		o = self.txobj
		o_conv = {
			'to':       bytes.fromhex(o['to'] or ''),
			'startgas': o['startGas'].toWei(),
			'gasprice': o['gasPrice'].toWei(),
			'value':    o['amt'].toWei() if o['amt'] else 0,
			'nonce':    o['nonce'],
			'data':     bytes.fromhex(o['data'])}

		from ..pyethereum.transactions import Transaction
		etx = Transaction(**o_conv).sign(wif, o['chainId'])
		assert etx.sender.hex() == o['from'], (
			'Sender address recovered from signature does not match true sender')

		from .. import rlp
		self.serialized = rlp.encode(etx).hex()
		self.coin_txid = CoinTxID(etx.hash.hex())

		if o['data']:
			if o['to']:
				assert self.txobj['token_addr'] == TokenAddr(self.proto, etx.creates.hex()), 'Token address mismatch'
			else: # token- or contract-creating transaction
				self.txobj['token_addr'] = TokenAddr(self.proto, etx.creates.hex())

	async def sign(self, tx_num_str, keys): # return TX object or False; don't exit or raise exception

		from ....exception import TransactionChainMismatch
		try:
			self.check_correct_chain()
		except TransactionChainMismatch:
			return False

		msg_r(f'Signing transaction{tx_num_str}...')

		try:
			await self.do_sign(keys[0].sec.wif)
			msg('OK')
			from ....tx import SignedTX
			return await SignedTX(cfg=self.cfg, data=self.__dict__, automount=self.automount)
		except Exception as e:
			msg(f'{e}: transaction signing failed!')
			return False

class TokenUnsigned(TokenCompleted, Unsigned):
	desc = 'unsigned transaction'

	def parse_txfile_serialized_data(self):
		d = Unsigned.parse_txfile_serialized_data(self)
		o = self.txobj
		o['token_addr'] = TokenAddr(self.proto, d['token_addr'])
		o['decimals'] = Int(d['decimals'])
		t = Token(self.cfg, self.proto, o['token_addr'], o['decimals'])
		o['data'] = t.create_data(o['to'], o['amt'])
		o['token_to'] = t.transferdata2sendaddr(o['data'])

	async def do_sign(self, wif):
		o = self.txobj
		t = Token(self.cfg, self.proto, o['token_addr'], o['decimals'])
		tx_in = t.make_tx_in(
				to_addr   = o['to'],
				amt       = o['amt'],
				start_gas = self.start_gas,
				gasPrice  = o['gasPrice'],
				nonce     = o['nonce'])
		(self.serialized, self.coin_txid) = await t.txsign(tx_in, wif, o['from'], chain_id=o['chainId'])

class AutomountUnsigned(TxBase.AutomountUnsigned, Unsigned):
	pass

class TokenAutomountUnsigned(TxBase.AutomountUnsigned, TokenUnsigned):
	pass
