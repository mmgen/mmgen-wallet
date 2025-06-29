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
proto.eth.tx.unsigned: Ethereum unsigned transaction class
"""

import json

from ....tx import unsigned as TxBase
from ....obj import CoinTxID, ETHNonce, Int, HexStr
from ....addr import CoinAddr, ContractAddr

from ...vm.tx.unsigned import Unsigned as VmUnsigned

from ..contract import Token, THORChainRouterContract

from .completed import Completed, TokenCompleted

class Unsigned(VmUnsigned, Completed, TxBase.Unsigned):

	def parse_txfile_serialized_data(self):
		d = self.serialized if isinstance(self.serialized, dict) else json.loads(self.serialized)
		o = {
			'from':     CoinAddr(self.proto, d['from']),
			# NB: for token, 'to' is sendto address
			'to':       CoinAddr(self.proto, d['to']) if d['to'] else None,
			'amt':      self.proto.coin_amt(d['amt']),
			'gasPrice': self.proto.coin_amt(d['gasPrice']),
			'startGas': (
				self.proto.coin_amt(d['startGas']).toWei() if '.' in d['startGas'] # for backward compat
				else int(d['startGas'])),
			'nonce':    ETHNonce(d['nonce']),
			'chainId':  None if d['chainId'] == 'None' else Int(d['chainId']),
			'data':     HexStr(d['data'])}
		self.txobj = o
		return d # 'token_addr', 'decimals' required by Token subclass

	async def do_sign(self, o, wif):
		o_conv = {
			'to':       bytes.fromhex(o['to'] or ''),
			'startgas': o['startGas'],
			'gasprice': o['gasPrice'].toWei(),
			'value':    o['amt'].toWei() if o['amt'] else 0,
			'nonce':    o['nonce'],
			'data':     self.swap_memo.encode() if self.is_swap else bytes.fromhex(o['data'])}

		from .transaction import Transaction
		etx = Transaction(**o_conv).sign(wif, o['chainId'])
		assert etx.sender.hex() == o['from'], (
			'Sender address recovered from signature does not match true sender')

		from .. import rlp
		self.serialized = rlp.encode(etx).hex()
		self.coin_txid = CoinTxID(etx.hash.hex())

		if o['data']: # contract-creating transaction
			if o['to']:
				if not self.is_swap:
					raise ValueError('contract-creating transaction cannot have to-address')
			else:
				self.txobj['token_addr'] = ContractAddr(self.proto, etx.creates.hex())

class TokenUnsigned(TokenCompleted, Unsigned):
	desc = 'unsigned transaction'

	def parse_txfile_serialized_data(self):
		d = Unsigned.parse_txfile_serialized_data(self)
		o = self.txobj
		o['token_addr'] = ContractAddr(self.proto, d['token_addr'])
		o['decimals'] = Int(d['decimals'])
		o['token_to'] = o['to']
		if self.is_swap:
			o['expiry'] = Int(d['expiry'])
			o['router_gas'] = Int(d['router_gas'])

	async def do_sign(self, o, wif):
		t = Token(self.cfg, self.proto, o['token_addr'], decimals=o['decimals'])
		tdata = t.create_transfer_data(o['to'], o['amt'], op=self.token_op)
		tx_in = t.make_tx_in(gas=o['startGas'], gasPrice=o['gasPrice'], nonce=o['nonce'], data=tdata)
		res = await t.txsign(tx_in, wif, o['from'], chain_id=o['chainId'])
		self.serialized = res.txhex
		self.coin_txid = res.txid
		if self.is_swap:
			c = THORChainRouterContract(self.cfg, self.proto, o['to'], decimals=o['decimals'])
			cdata = c.create_deposit_with_expiry_data(
				self.token_vault_addr,
				o['token_addr'],
				o['amt'],
				self.swap_memo.encode(),
				o['expiry'])
			tx_in = c.make_tx_in(
				gas = o['router_gas'],
				gasPrice = o['gasPrice'],
				nonce = o['nonce'] + 1,
				data = cdata)
			res = await t.txsign(tx_in, wif, o['from'], chain_id=o['chainId'])
			self.serialized2 = res.txhex
			self.coin_txid2 = res.txid

class AutomountUnsigned(TxBase.AutomountUnsigned, Unsigned):
	pass

class TokenAutomountUnsigned(TxBase.AutomountUnsigned, TokenUnsigned):
	pass
