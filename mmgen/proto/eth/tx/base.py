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
proto.eth.tx.base: Ethereum base transaction class
"""

from collections import namedtuple

from ....tx.base import Base as TxBase
from ....obj import Int

class Base(TxBase):

	rel_fee_desc = 'gas price'
	rel_fee_disp = 'gas price in Gwei'
	txobj = None
	dfl_gas = 21000 # the startGas amt used in the transaction
	                # for simple sends with no data, startGas = 21000
	contract_desc = 'contract'
	usr_contract_data = b''
	disable_fee_check = False

	@property
	def nondata_outputs(self):
		return self.outputs

	def pretty_fmt_fee(self, fee):
		if fee < 10:
			return f'{fee:.3f}'.rstrip('0').rstrip('.')
		return str(int(fee))

	# given absolute fee in ETH, return gas price for display in selected unit
	def fee_abs2rel(self, abs_fee, *, to_unit='Gwei'):
		return self.pretty_fmt_fee(
			self.fee_abs2gasprice(abs_fee).to_unit(to_unit))

	# given absolute fee in ETH, return gas price in ETH
	def fee_abs2gasprice(self, abs_fee):
		return self.proto.coin_amt(int(abs_fee.toWei() // self.total_gas), from_unit='wei')

	# given rel fee (gasPrice) in wei, return absolute fee using self.total_gas
	def fee_gasPrice2abs(self, rel_fee):
		assert isinstance(rel_fee, int), f'{rel_fee!r}: incorrect type for fee estimate (not an integer)'
		return self.proto.coin_amt(rel_fee * self.total_gas, from_unit='wei')

	def is_replaceable(self):
		return True

	async def get_receipt(self, txid, *, receipt_only=False):
		import asyncio
		from ....util import msg, msg_r

		for n in range(60):
			rx = await self.rpc.call('eth_getTransactionReceipt', '0x'+txid) # -> null if pending
			if rx or not self.cfg.wait:
				break
			if n == 0:
				msg_r('Waiting for first confirmation..')
			await asyncio.sleep(1)
			msg_r('.')

		if rx:
			if n:
				msg('OK')
			if receipt_only:
				return rx
		else:
			if self.cfg.wait:
				msg('timeout exceeded!')
			return None

		tx = await self.rpc.call('eth_getTransactionByHash', '0x'+txid)
		return namedtuple('exec_status',
				['status', 'gas_sent', 'gas_used', 'gas_price', 'contract_addr', 'tx', 'rx'])(
			status        = Int(rx['status'], base=16), # zero is failure, non-zero success
			gas_sent      = Int(tx['gas'], base=16),
			gas_used      = Int(rx['gasUsed'], base=16),
			gas_price     = self.proto.coin_amt(Int(tx['gasPrice'], base=16), from_unit='wei'),
			contract_addr = self.proto.coin_addr(rx['contractAddress'][2:])
				if rx['contractAddress'] else None,
			tx = tx,
			rx = rx)

	def check_serialized_integrity(self):
		if self.signed:
			from .. import rlp
			o = self.txobj
			d = rlp.decode(bytes.fromhex(self.serialized))
			to_key = 'token_addr' if self.is_token else 'to'

			if o['nonce'] == 0:
				assert d[0] == b'', f'{d[0]}: invalid nonce in serialized data'
			else:
				assert int(d[0].hex(), 16) == o['nonce'], f'{d[0]}: invalid nonce in serialized data'
			if o.get(to_key):
				assert d[3].hex() == o[to_key], f'{d[3].hex()}: invalid ‘to’ address in serialized data'
			if not self.is_token:
				if o['amt']:
					assert int(d[4].hex(), 16) == o['amt'].toWei(), (
						f'{d[4].hex()}: invalid amt in serialized data')
				if self.is_swap:
					assert d[5] == self.swap_memo.encode(), (
						f'{d[5]}: invalid swap memo in serialized data')

class TokenBase(Base):
	dfl_gas = 75000
	dfl_router_gas = 150000
	contract_desc = 'token contract'

	def check_serialized_integrity(self):
		if self.signed:
			super().check_serialized_integrity()

			from .. import rlp
			from ....amt import TokenAmt
			d = rlp.decode(bytes.fromhex(self.serialized))
			o = self.txobj

			assert d[4] == b'', f'{d[4]}: non-empty amount field in token transaction in serialized data'

			data = d[5].hex()
			assert data[:8] == ('095ea7b3' if self.is_swap else 'a9059cbb'), (
				f'{data[:8]}: invalid MethodID for op ‘{self.token_op}’ in serialized data')
			assert data[32:72] == o['token_to'], (
				f'{data[32:72]}: invalid ‘token_to‘ address in serialized data')
			assert TokenAmt(
					int(data[72:], 16),
					decimals = o['decimals'],
					from_unit = 'atomic') == o['amt'], (
				f'{data[72:]}: invalid amt in serialized data')

			if self.is_swap:
				d = rlp.decode(bytes.fromhex(self.serialized2))
				data = d[5].hex()
				assert data[:8] == '44bc937b', (
					f'{data[:8]}: invalid MethodID in router TX serialized data')
				assert data[32:72] == self.token_vault_addr, (
					f'{data[32:72]}: invalid vault address in router TX serialized data')

				memo = bytes.fromhex(data[392:])[:len(self.swap_memo)]
				assert memo == self.swap_memo.encode(), (
					f'{memo}: invalid swap memo in router TX serialized data')
				assert TokenAmt(
						int(data[136:200], 16),
						decimals = o['decimals'],
						from_unit = 'atomic') == o['amt'], (
					f'{data[136:200]}: invalid amt in router TX serialized data')
