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
proto.eth.tx.base: Ethereum base transaction class
"""

from collections import namedtuple

import mmgen.tx.base as TxBase
from ....amt import ETHAmt
from ....obj import HexStr,Int
from ....util import dmsg

class Base(TxBase.Base):

	rel_fee_desc = 'gas price'
	rel_fee_disp = 'gas price in Gwei'
	txobj  = None # ""
	tx_gas = ETHAmt(21000,'wei')    # an approximate number, used for fee estimation purposes
	start_gas = ETHAmt(21000,'wei') # the actual startgas amt used in the transaction
									# for simple sends with no data, tx_gas = start_gas = 21000
	contract_desc = 'contract'
	usr_contract_data = HexStr('')
	disable_fee_check = False

	# given absolute fee in ETH, return gas price in Gwei using tx_gas
	def fee_abs2rel(self,abs_fee,to_unit='Gwei'):
		ret = ETHAmt(int(abs_fee.toWei() // self.tx_gas.toWei()),'wei')
		dmsg(f'fee_abs2rel() ==> {ret} ETH')
		return ret if to_unit == 'eth' else ret.to_unit(to_unit,show_decimal=True)

	# given rel fee (gasPrice) in wei, return absolute fee using tx_gas (Ethereum-only method)
	def fee_gasPrice2abs(self,rel_fee):
		assert isinstance(rel_fee,int), f'{rel_fee!r}: incorrect type for fee estimate (not an integer)'
		return ETHAmt(rel_fee * self.tx_gas.toWei(),'wei')

	def is_replaceable(self):
		return True

	async def get_receipt(self,txid,silent=False):
		rx = await self.rpc.call('eth_getTransactionReceipt','0x'+txid) # -> null if pending
		if not rx:
			return None
		tx = await self.rpc.call('eth_getTransactionByHash','0x'+txid)
		return namedtuple('exec_status',['status','gas_sent','gas_used','gas_price','contract_addr','tx','rx'])(
			status        = Int(rx['status'],16), # zero is failure, non-zero success
			gas_sent      = Int(tx['gas'],16),
			gas_used      = Int(rx['gasUsed'],16),
			gas_price     = ETHAmt(int(tx['gasPrice'],16),from_unit='wei'),
			contract_addr = self.proto.coin_addr(rx['contractAddress'][2:]) if rx['contractAddress'] else None,
			tx            = tx,
			rx            = rx,
		)

	def check_serialized_integrity(self): # TODO
		return True

class TokenBase(Base):
	tx_gas = ETHAmt(52000,'wei')
	start_gas = ETHAmt(60000,'wei')
	contract_desc = 'token contract'
