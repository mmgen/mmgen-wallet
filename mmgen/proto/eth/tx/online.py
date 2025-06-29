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
proto.eth.tx.online: Ethereum online signed transaction class
"""

from ....util import msg, die
from ....color import yellow, green, orange
from ....tx import online as TxBase
from .. import erigon_sleep
from .signed import Signed, TokenSigned

class OnlineSigned(Signed, TxBase.OnlineSigned):

	async def test_sendable(self, txhex):
		raise NotImplementedError('transaction testing not implemented for Ethereum')

	async def send_checks(self):
		self.check_correct_chain()
		if not self.disable_fee_check and (self.fee > self.proto.max_tx_fee):
			die(2, 'Transaction fee ({}) greater than {} max_tx_fee ({} {})!'.format(
				self.fee,
				self.proto.name,
				self.proto.max_tx_fee,
				self.proto.coin))
		await self.status.display()

	async def send_with_node(self, txhex):
		try:
			ret = await self.rpc.call('eth_sendRawTransaction', '0x' + txhex)
		except Exception as e:
			msg(orange('\n'+str(e)))
			die(2, f'Send of MMGen transaction {self.txid} failed')
		await erigon_sleep(self)
		return ret.removeprefix('0x')

	async def post_network_send(self, coin_txid):
		res = await self.get_receipt(coin_txid)
		if not res:
			if self.cfg.wait:
				msg('{} {} {}'.format(
					yellow('Send of'),
					coin_txid.hl(),
					yellow('failed? (failed to get receipt)')))
			return False
		msg(f'Gas sent: {res.gas_sent.hl()}\n'
			f'Gas used: {res.gas_used.hl()}')
		if res.status == 0:
			if res.gas_used == res.gas_sent:
				msg(yellow('All gas was used!'))
			msg('{} {} {}'.format(
				yellow('Send of'),
				coin_txid.hl(),
				yellow('failed (status=0)')))
			return False
		msg(f'Status: {green(str(res.status))}')
		if res.contract_addr:
			msg('Contract address: {}'.format(res.contract_addr.hl(0)))
		return True

class TokenOnlineSigned(TokenSigned, OnlineSigned):

	def parse_txfile_serialized_data(self):
		from ....addr import ContractAddr
		from ..contract import Token
		OnlineSigned.parse_txfile_serialized_data(self)
		o = self.txobj
		assert self.twctl.token == o['to']
		o['token_addr'] = ContractAddr(self.proto, o['to'])
		o['decimals']   = self.twctl.decimals
		t = Token(self.cfg, self.proto, o['token_addr'], decimals=o['decimals'])
		o['amt'] = t.transferdata2amt(o['data'])
		o['token_to'] = t.transferdata2sendaddr(o['data'])
		if self.is_swap:
			from .transaction import Transaction
			from .. import rlp
			etx = rlp.decode(bytes.fromhex(self.serialized2), Transaction)
			d = etx.to_dict()
			o['router_gas'] = d['startgas']

class Sent(TxBase.Sent, OnlineSigned):
	pass

class TokenSent(TxBase.Sent, TokenOnlineSigned):
	pass

class AutomountOnlineSigned(TxBase.AutomountOnlineSigned, OnlineSigned):
	pass

class AutomountSent(TxBase.AutomountSent, AutomountOnlineSigned):
	pass

class TokenAutomountOnlineSigned(TxBase.AutomountOnlineSigned, TokenOnlineSigned):
	pass

class TokenAutomountSent(TxBase.AutomountSent, TokenAutomountOnlineSigned):
	pass
