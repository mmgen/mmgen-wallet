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
proto.eth.tx.online: Ethereum online signed transaction class
"""

from ....util import msg, die
from ....color import orange
from ....tx import online as TxBase
from .. import erigon_sleep
from .signed import Signed, TokenSigned

class OnlineSigned(Signed, TxBase.OnlineSigned):

	async def send(self, prompt_user=True):

		self.check_correct_chain()

		if not self.disable_fee_check and (self.fee > self.proto.max_tx_fee):
			die(2, 'Transaction fee ({}) greater than {} max_tx_fee ({} {})!'.format(
				self.fee,
				self.proto.name,
				self.proto.max_tx_fee,
				self.proto.coin))

		await self.status.display()

		if prompt_user:
			self.confirm_send()

		if self.cfg.bogus_send:
			m = 'BOGUS transaction NOT sent: {}'
		else:
			try:
				ret = await self.rpc.call('eth_sendRawTransaction', '0x'+self.serialized)
			except Exception as e:
				msg(orange('\n'+str(e)))
				die(2, f'Send of MMGen transaction {self.txid} failed')
			m = 'Transaction sent: {}'
			assert ret == '0x'+self.coin_txid, 'txid mismatch (after sending)'
			await erigon_sleep(self)

		msg(m.format(self.coin_txid.hl()))
		self.add_sent_timestamp()
		self.add_blockcount()

		return True

	def print_contract_addr(self):
		if 'token_addr' in self.txobj:
			msg('Contract address: {}'.format(self.txobj['token_addr'].hl(0)))

class TokenOnlineSigned(TokenSigned, OnlineSigned):

	def parse_txfile_serialized_data(self):
		from ....addr import TokenAddr
		from ..contract import Token
		OnlineSigned.parse_txfile_serialized_data(self)
		o = self.txobj
		assert self.twctl.token == o['to']
		o['token_addr'] = TokenAddr(self.proto, o['to'])
		o['decimals']   = self.twctl.decimals
		t = Token(self.cfg, self.proto, o['token_addr'], o['decimals'])
		o['amt'] = t.transferdata2amt(o['data'])
		o['token_to'] = t.transferdata2sendaddr(o['data'])

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
