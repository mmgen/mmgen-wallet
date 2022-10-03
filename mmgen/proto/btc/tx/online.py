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
proto.btc.tx.online: Bitcoin online signed transaction class
"""

import mmgen.tx.online as TxBase
from .signed import Signed
from ....globalvars import *
from ....util import msg,ymsg,rmsg

class OnlineSigned(Signed,TxBase.OnlineSigned):

	async def send(self,prompt_user=True,exit_on_fail=False):

		self.check_correct_chain()

		if not g.bogus_send:
			if self.has_segwit_outputs() and not self.rpc.info('segwit_is_active'):
				die(2,'Transaction has Segwit outputs, but this blockchain does not support Segwit'
						+ ' at the current height')

		if self.fee > self.proto.max_tx_fee:
			die(2,'Transaction fee ({}) greater than {} max_tx_fee ({} {})!'.format(
				self.fee,
				self.proto.name,
				self.proto.max_tx_fee,
				self.proto.coin ))

		await self.status.display()

		if prompt_user:
			self.confirm_send()

		if g.bogus_send:
			ret = None
		else:
			try:
				ret = await self.rpc.call('sendrawtransaction',self.serialized)
			except Exception as e:
				errmsg = str(e)
				ret = False

		if ret == False: # TODO: test send errors
			if errmsg.count('Signature must use SIGHASH_FORKID'):
				m = ('The Aug. 1 2017 UAHF has activated on this chain.\n'
					+ 'Re-run the script with the --coin=bch option.' )
			elif errmsg.count('Illegal use of SIGHASH_FORKID'):
				m  = ('The Aug. 1 2017 UAHF is not yet active on this chain.\n'
					+ 'Re-run the script without the --coin=bch option.' )
			elif errmsg.count('64: non-final'):
				m = "Transaction with nLockTime {!r} can't be included in this block!".format(
					self.strfmt_locktime(self.get_serialized_locktime()) )
			else:
				m = errmsg
			ymsg(m)
			rmsg(f'Send of MMGen transaction {self.txid} failed')
			if exit_on_fail:
				sys.exit(1)
			return False
		else:
			if g.bogus_send:
				m = 'BOGUS transaction NOT sent: {}'
			else:
				m = 'Transaction sent: {}'
				assert ret == self.coin_txid, 'txid mismatch (after sending)'
			msg(m.format(self.coin_txid.hl()))
			self.add_timestamp()
			self.add_blockcount()
			self.desc = 'sent transaction'
			return True

	def print_contract_addr(self):
		pass
