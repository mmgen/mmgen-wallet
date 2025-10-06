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
proto.btc.tx.unsigned: Bitcoin unsigned transaction class
"""

from ....tx import unsigned as TxBase
from ....obj import CoinTxID, MMGenDict
from ....util import msg, msg_r, ymsg, suf, die
from .completed import Completed

class Unsigned(Completed, TxBase.Unsigned):
	desc = 'unsigned transaction'

	# Return signed object or False. Don’t exit or raise exception:
	async def sign(self, keys, tx_num_str=''):

		from ....exception import TransactionChainMismatch
		try:
			self.check_correct_chain()
		except TransactionChainMismatch:
			return False

		if (self.has_segwit_inputs() or self.has_segwit_outputs()) and not self.proto.cap('segwit'):
			ymsg(f"TX has Segwit inputs or outputs, but {self.coin} doesn't support Segwit!")
			return False

		self.check_pubkey_scripts()

		self.cfg._util.qmsg(f'Passing {len(keys)} key{suf(keys)} to {self.rpc.daemon.exec_fn}')

		if self.has_segwit_inputs():
			from ....addrgen import KeyGenerator, AddrGenerator
			kg = KeyGenerator(self.cfg, self.proto, 'std')
			ag = AddrGenerator(self.cfg, self.proto, 'segwit')
			keydict = MMGenDict([(d.addr, d.sec) for d in keys])

		sig_data = []
		for d in self.inputs:
			e = {k: getattr(d, k) for k in ('txid', 'vout', 'scriptPubKey', 'amt')}
			e['amount'] = e['amt']
			del e['amt']
			if d.mmtype == 'S':
				e['redeemScript'] = ag.to_segwit_redeem_script(kg.gen_data(keydict[d.addr]))
			sig_data.append(e)

		msg_r(f'Signing transaction{tx_num_str}...')
		wifs = [d.sec.wif for d in keys]

		try:
			args = (
				('signrawtransaction',       self.serialized, sig_data, wifs, self.proto.sighash_type),
				('signrawtransactionwithkey', self.serialized, wifs, sig_data, self.proto.sighash_type)
			)['sign_with_key' in self.rpc.caps]
			ret = await self.rpc.call(*args)
		except Exception as e:
			ymsg(self.rpc.daemon.sigfail_errmsg(e))
			return False

		try:
			self.update_serialized(ret['hex'])
			from ....tx import SignedTX
			new = SignedTX(cfg=self.cfg, data=self.__dict__, automount=self.automount)
			tx_decoded = await self.rpc.call('decoderawtransaction', ret['hex'])
			new.compare_size_and_estimated_size(tx_decoded)
			new.coin_txid = CoinTxID(self.deserialized.txid)
			if not new.coin_txid == tx_decoded['txid']:
				die('BadMMGenTxID', 'txid mismatch (after signing)')
			msg('OK')
			return new
		except Exception as e:
			ymsg(f'\n{e.args[0]}')
			return False

class AutomountUnsigned(TxBase.AutomountUnsigned, Unsigned):
	pass
