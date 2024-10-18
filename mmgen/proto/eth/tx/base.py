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
proto.eth.tx.base: Ethereum base transaction class
"""

from collections import namedtuple

from ....tx import base as TxBase
from ....obj import HexStr, Int

class Base(TxBase.Base):

	rel_fee_desc = 'gas price'
	rel_fee_disp = 'gas price in Gwei'
	txobj  = None # ""
	dfl_gas = 21000               # an approximate number, used for fee estimation purposes
	dfl_start_gas = 21000         # the actual startgas amt used in the transaction
	                              # for simple sends with no data, gas = start_gas = 21000
	contract_desc = 'contract'
	usr_contract_data = HexStr('')
	disable_fee_check = False

	def pretty_fmt_fee(self, fee):
		if fee < 1:
			ret = f'{fee:.8f}'.rstrip('0')
			return ret + '0' if ret.endswith('.') else ret
		return str(int(fee))

	# given absolute fee in ETH, return gas price for display in selected unit
	def fee_abs2rel(self, abs_fee, to_unit='Gwei'):
		return self.pretty_fmt_fee(
			self.fee_abs2gas(abs_fee).to_unit(to_unit))

	# given absolute fee in ETH, return gas price in ETH
	def fee_abs2gas(self, abs_fee):
		return self.proto.coin_amt(int(abs_fee.toWei() // self.gas.toWei()), from_unit='wei')

	# given rel fee (gasPrice) in wei, return absolute fee using self.gas (Ethereum-only method)
	def fee_gasPrice2abs(self, rel_fee):
		assert isinstance(rel_fee, int), f'{rel_fee!r}: incorrect type for fee estimate (not an integer)'
		return self.proto.coin_amt(rel_fee * self.gas.toWei(), from_unit='wei')

	def is_replaceable(self):
		return True

	async def get_receipt(self, txid):
		rx = await self.rpc.call('eth_getTransactionReceipt', '0x'+txid) # -> null if pending
		if not rx:
			return None
		tx = await self.rpc.call('eth_getTransactionByHash', '0x'+txid)
		return namedtuple('exec_status',
				['status', 'gas_sent', 'gas_used', 'gas_price', 'contract_addr', 'tx', 'rx'])(
			status        = Int(rx['status'], 16), # zero is failure, non-zero success
			gas_sent      = Int(tx['gas'], 16),
			gas_used      = Int(rx['gasUsed'], 16),
			gas_price     = self.proto.coin_amt(int(tx['gasPrice'], 16), from_unit='wei'),
			contract_addr = self.proto.coin_addr(rx['contractAddress'][2:]) if rx['contractAddress'] else None,
			tx            = tx,
			rx            = rx,
		)

	def check_serialized_integrity(self): # TODO
		return True

class TokenBase(Base):
	dfl_gas = 52000
	dfl_start_gas = 60000
	contract_desc = 'token contract'
