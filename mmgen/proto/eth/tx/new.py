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
proto.eth.tx.new: Ethereum new transaction class
"""

import json

from ....tx import new as TxBase
from ....obj import Int, ETHNonce, MMGenTxID, HexStr
from ....util import msg, is_int, is_hex_str, make_chksum_6, suf, die
from ....tw.ctl import TwCtl
from ....addr import is_mmgen_id, is_coin_addr
from ..contract import Token
from .base import Base, TokenBase

class New(Base, TxBase.New):
	desc = 'transaction'
	fee_fail_fs = 'Network fee estimation failed'
	no_chg_msg = 'Warning: Transaction leaves account with zero balance'
	usr_fee_prompt = 'Enter transaction fee or gas price: '
	msg_insufficient_funds = 'Account balance insufficient to fund this transaction ({} {} needed)'

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)

		if self.cfg.gas:
			self.gas = self.start_gas = self.proto.coin_amt(int(self.cfg.gas), from_unit='wei')
		else:
			self.gas = self.proto.coin_amt(self.dfl_gas, from_unit='wei')
			self.start_gas = self.proto.coin_amt(self.dfl_start_gas, from_unit='wei')

		if self.cfg.contract_data:
			m = "'--contract-data' option may not be used with token transaction"
			assert 'Token' not in self.name, m
			with open(self.cfg.contract_data) as fp:
				self.usr_contract_data = HexStr(fp.read().strip())
			self.disable_fee_check = True

	async def get_nonce(self):
		return ETHNonce(int(
			await self.rpc.call('eth_getTransactionCount', '0x'+self.inputs[0].addr, 'pending'), 16))

	async def make_txobj(self): # called by create_serialized()
		self.txobj = {
			'from': self.inputs[0].addr,
			'to':   self.outputs[0].addr if self.outputs else None,
			'amt':  self.outputs[0].amt if self.outputs else self.proto.coin_amt('0'),
			'gasPrice': self.fee_abs2gas(self.usr_fee),
			'startGas': self.start_gas,
			'nonce': await self.get_nonce(),
			'chainId': self.rpc.chainID,
			'data':  self.usr_contract_data,
		}

	# Instead of serializing tx data as with BTC, just create a JSON dump.
	# This complicates things but means we avoid using the rlp library to deserialize the data,
	# thus removing an attack vector
	async def create_serialized(self, locktime=None, bump=None):
		assert len(self.inputs) == 1, 'Transaction has more than one input!'
		o_num = len(self.outputs)
		o_ok = 0 if self.usr_contract_data else 1
		assert o_num == o_ok, f'Transaction has {o_num} output{suf(o_num)} (should have {o_ok})'
		await self.make_txobj()
		odict = {k:v if v is None else str(v) for k, v in self.txobj.items() if k != 'token_to'}
		self.serialized = json.dumps(odict)
		self.update_txid()

	def update_txid(self):
		assert not is_hex_str(self.serialized), (
			'update_txid() must be called only when self.serialized is not hex data')
		self.txid = MMGenTxID(make_chksum_6(self.serialized).upper())

	async def process_cmd_args(self, cmd_args, ad_f, ad_w):

		lc = len(cmd_args)

		if lc == 0 and self.usr_contract_data and 'Token' not in self.name:
			return

		if lc != 1:
			die(1, f'{lc} output{suf(lc)} specified, but Ethereum transactions must have exactly one')

		arg = self.parse_cmd_arg(cmd_args[0], ad_f, ad_w)

		self.add_output(
			coinaddr = arg.coin_addr,
			amt      = self.proto.coin_amt(arg.amt or '0'),
			is_chg   = not arg.amt)

	def select_unspent(self, unspent):
		from ....ui import line_input
		while True:
			reply = line_input(self.cfg, 'Enter an account to spend from: ').strip()
			if reply:
				if not is_int(reply):
					msg('Account number must be an integer')
				elif int(reply) < 1:
					msg('Account number must be >= 1')
				elif int(reply) > len(unspent):
					msg(f'Account number must be <= {len(unspent)}')
				else:
					return [int(reply)]

	@property
	def network_estimated_fee_label(self):
		return 'Network-estimated'

	# get rel_fee (gas price) from network, return in native wei
	async def get_rel_fee_from_network(self):
		return Int(await self.rpc.call('eth_gasPrice'), 16), 'eth_gasPrice'

	def check_fee(self):
		if not self.disable_fee_check:
			assert self.usr_fee <= self.proto.max_tx_fee

	# given rel fee and units, return absolute fee using self.gas
	def fee_rel2abs(self, tx_size, units, amt_in_units, unit):
		return self.proto.coin_amt(amt_in_units, from_unit=units[unit]) * self.gas.toWei()

	# given fee estimate (gas price) in wei, return absolute fee, adjusting by self.cfg.fee_adjust
	def fee_est2abs(self, rel_fee, fe_type=None):
		ret = self.fee_gasPrice2abs(rel_fee) * self.cfg.fee_adjust
		if self.cfg.verbose:
			msg(f'Estimated fee: {ret} ETH')
		return ret

	def convert_and_check_fee(self, fee, desc):
		abs_fee = self.feespec2abs(fee, None)
		if abs_fee is False:
			return False
		elif not self.disable_fee_check and (abs_fee > self.proto.max_tx_fee):
			msg('{} {c}: {} fee too large (maximum fee: {} {c})'.format(
				abs_fee.hl(),
				desc,
				self.proto.max_tx_fee.hl(),
				c = self.proto.coin))
			return False
		else:
			return abs_fee

	def update_change_output(self, funds_left):
		if self.outputs and self.outputs[0].is_chg:
			self.update_output_amt(0, funds_left)

	async def get_input_addrs_from_cmdline(self):
		ret = []
		if self.cfg.inputs:
			data_root = (await TwCtl(self.cfg, self.proto)).data_root # must create new instance here
			errmsg = 'Address {!r} not in tracking wallet'
			for addr in self.cfg.inputs.split(','):
				if is_mmgen_id(self.proto, addr):
					for waddr in data_root:
						if data_root[waddr]['mmid'] == addr:
							ret.append(waddr)
							break
					else:
						die('UserAddressNotInWallet', errmsg.format(addr))
				elif is_coin_addr(self.proto, addr):
					if not addr in data_root:
						die('UserAddressNotInWallet', errmsg.format(addr))
					ret.append(addr)
				else:
					die(1, f'{addr!r}: not an MMGen ID or coin address')
		return ret

	def final_inputs_ok_msg(self, funds_left):
		chg = self.proto.coin_amt('0') if (self.outputs and self.outputs[0].is_chg) else funds_left
		return 'Transaction leaves {} {} in the sender’s account'.format(chg.hl(), self.proto.coin)

class TokenNew(TokenBase, New):
	desc = 'transaction'
	fee_is_approximate = True

	async def make_txobj(self): # called by create_serialized()
		await super().make_txobj()
		t = Token(self.cfg, self.proto, self.twctl.token, self.twctl.decimals)
		o = self.txobj
		o['token_addr'] = t.addr
		o['decimals'] = t.decimals
		o['token_to'] = o['to']
		o['data'] = t.create_data(o['token_to'], o['amt'])

	def update_change_output(self, funds_left):
		if self.outputs[0].is_chg:
			self.update_output_amt(0, self.inputs[0].amt)

	# token transaction, so check both eth and token balances
	# TODO: add test with insufficient funds
	async def precheck_sufficient_funds(self, inputs_sum, sel_unspent, outputs_sum):
		eth_bal = await self.twctl.get_eth_balance(sel_unspent[0].addr)
		if eth_bal == 0: # we don't know the fee yet
			msg('This account has no ether to pay for the transaction fee!')
			return False
		return await super().precheck_sufficient_funds(inputs_sum, sel_unspent, outputs_sum)

	async def get_funds_available(self, fee, outputs_sum):
		bal = await self.twctl.get_eth_balance(self.inputs[0].addr)
		return self._funds_available(bal >= fee, bal - fee if bal >= fee else fee - bal)

	def final_inputs_ok_msg(self, funds_left):
		token_bal = (
			self.proto.coin_amt('0') if self.outputs[0].is_chg
			else self.inputs[0].amt - self.outputs[0].amt
		)
		return "Transaction leaves ≈{} {} and {} {} in the sender's account".format(
			funds_left.hl(),
			self.proto.coin,
			token_bal.hl(),
			self.proto.dcoin
		)
