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
		return self.proto.coin_amt(int(abs_fee.toWei() // self.gas.toWei()), from_unit='wei')

	# given rel fee (gasPrice) in wei, return absolute fee using self.gas (Ethereum-only method)
	def fee_gasPrice2abs(self, rel_fee):
		assert isinstance(rel_fee, int), f'{rel_fee!r}: incorrect type for fee estimate (not an integer)'
		return self.proto.coin_amt(rel_fee * self.gas.toWei(), from_unit='wei')

	def is_replaceable(self):
		return True

	# used for testing only:
	async def get_receipt(self, txid):
		rx = await self.rpc.call('eth_getTransactionReceipt', '0x'+txid) # -> null if pending
		if not rx:
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

	def check_serialized_integrity(self): # TODO
		return True

class TokenBase(Base):
	dfl_gas = 52000
	contract_desc = 'token contract'
