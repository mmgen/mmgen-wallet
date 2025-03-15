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
proto.btc.tx.online: Bitcoin online signed transaction class
"""

from ....tx import online as TxBase
from ....util import msg, ymsg, die
from ....color import orange
from .signed import Signed

class OnlineSigned(Signed, TxBase.OnlineSigned):

	async def send_checks(self):

		self.check_correct_chain()

		if not self.cfg.bogus_send:
			if self.has_segwit_outputs() and not self.rpc.info('segwit_is_active'):
				die(2, 'Transaction has Segwit outputs, but this blockchain does not support Segwit'
						+ ' at the current height')

		if self.fee > self.proto.max_tx_fee:
			die(2, 'Transaction fee ({}) greater than {} max_tx_fee ({} {})!'.format(
				self.fee,
				self.proto.name,
				self.proto.max_tx_fee,
				self.proto.coin))

		await self.status.display()

	async def test_sendable(self):

		await self.send_checks()

		res = await self.rpc.call('testmempoolaccept', (self.serialized,))
		ret = res[0]

		if ret['allowed']:
			from ....obj import CoinTxID
			msg('TxID: {}'.format(CoinTxID(ret['txid']).hl()))
			msg('Transaction can be sent')
			return True
		else:
			ymsg('Transaction cannot be sent')
			msg(ret['reject-reason'])
			return False

	async def send(self, *, prompt_user=True):

		await self.send_checks()

		if prompt_user:
			self.confirm_send()

		if self.cfg.bogus_send:
			m = 'BOGUS transaction NOT sent: {}'
		else:
			m = 'Transaction sent: {}'
			try:
				ret = await self.rpc.call('sendrawtransaction', self.serialized)
			except Exception as e:
				errmsg = str(e)
				nl = '\n'
				if errmsg.count('Signature must use SIGHASH_FORKID'):
					m = (
						'The Aug. 1 2017 UAHF has activated on this chain.\n'
						'Re-run the script with the --coin=bch option.')
				elif errmsg.count('Illegal use of SIGHASH_FORKID'):
					m  = (
						'The Aug. 1 2017 UAHF is not yet active on this chain.\n'
						'Re-run the script without the --coin=bch option.')
				elif errmsg.count('non-final'):
					m = "Transaction with nLockTime {!r} can’t be included in this block!".format(
						self.info.strfmt_locktime(self.get_serialized_locktime()))
				else:
					m, nl = ('', '')
				msg(orange('\n'+errmsg))
				die(2, f'{m}{nl}Send of MMGen transaction {self.txid} failed')
			else:
				assert ret == self.coin_txid, 'txid mismatch (after sending)'

		msg(m.format(self.coin_txid.hl()))
		self.add_sent_timestamp()
		self.add_blockcount()
		return True

	def post_write(self):
		pass

class Sent(TxBase.Sent, OnlineSigned):
	pass

class AutomountOnlineSigned(TxBase.AutomountOnlineSigned, OnlineSigned):
	pass

class AutomountSent(TxBase.AutomountSent, AutomountOnlineSigned):
	pass
