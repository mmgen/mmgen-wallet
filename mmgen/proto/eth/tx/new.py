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
proto.eth.tx.new: Ethereum new transaction class
"""

from ....tx import new as TxBase
from ....obj import Int, ETHNonce, MMGenTxID
from ....util import msg, ymsg, is_int, is_hex_str, make_chksum_6, suf, die
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
	byte_cost = 68 # https://ethereum.stackexchange.com/questions/39401/
	               # how-do-you-calculate-gas-limit-for-transaction-with-data-in-ethereum

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)

		if self.cfg.contract_data:
			m = "'--contract-data' option may not be used with token transaction"
			assert 'Token' not in self.name, m
			with open(self.cfg.contract_data) as fp:
				self.usr_contract_data = bytes.fromhex(fp.read().strip())
			self.disable_fee_check = True

	async def get_gas_estimateGas(self, *, to_addr):
		return self.dfl_gas

	async def set_gas(self, *, to_addr=None, force=False):
		if force or to_addr or not hasattr(self, 'gas'):
			if is_int(self.cfg.gas):
				self.gas = int(self.cfg.gas)
			elif self.cfg.gas == 'fallback':
				self.gas = self.dfl_gas
			elif self.is_bump and not self.rpc.daemon.id == 'reth':
				self.gas = self.txobj['startGas']
			else:
				assert self.cfg.gas in ('auto', None), f'{self.cfg.gas}: invalid value for cfg.gas'
				self.gas = await self.get_gas_estimateGas(to_addr=to_addr)

	async def get_nonce(self):
		return ETHNonce(int(
			await self.rpc.call('eth_getTransactionCount', '0x'+self.inputs[0].addr, 'pending'), 16))

	async def make_txobj(self): # called by create_serialized()
		self.txobj = {
			'from': self.inputs[0].addr,
			'to':   self.outputs[0].addr if self.outputs else None,
			'amt':  self.outputs[0].amt if self.outputs else self.proto.coin_amt('0'),
			'gasPrice': self.fee_abs2gasprice(self.usr_fee),
			'startGas': self.gas,
			'nonce': await self.get_nonce(),
			'chainId': self.rpc.chainID,
			'data':  self.usr_contract_data.hex()}

	# Instead of serializing tx data as with BTC, just create a JSON dump.
	# This complicates things but means we avoid using the rlp library to deserialize the data,
	# thus removing an attack vector
	async def create_serialized(self, *, locktime=None):
		assert len(self.inputs) == 1, 'Transaction has more than one input!'
		o_num = len(self.outputs)
		o_ok = 0 if self.usr_contract_data else 1
		assert o_num == o_ok, f'Transaction has {o_num} output{suf(o_num)} (should have {o_ok})'
		await self.make_txobj()
		self.serialized = {k:v if v is None else str(v) for k, v in self.txobj.items() if k != 'token_to'}
		self.update_txid()

	def update_txid(self):
		import json
		assert not is_hex_str(self.serialized), (
			'update_txid() must be called only when self.serialized is not hex data')
		self.txid = MMGenTxID(make_chksum_6(json.dumps(self.serialized)).upper())

	def set_gas_with_data(self, data):
		if not self.is_token:
			self.gas = self.dfl_gas + self.byte_cost * len(data)

	# one-shot method
	def adj_gas_with_extra_data_len(self, extra_data_len):
		if not (self.is_token or hasattr(self, '_gas_adjusted')):
			self.gas += self.byte_cost * extra_data_len
			self._gas_adjusted = True

	async def process_cmdline_args(self, cmd_args, ad_f, ad_w):

		lc = len(cmd_args)

		if lc == 2 and self.is_swap:
			data_arg = cmd_args.pop()
			lc = 1
			assert data_arg.startswith('data:'), f'{data_arg}: invalid data arg (must start with "data:")'
			self.swap_memo = data_arg.removeprefix('data:')
			self.set_gas_with_data(self.swap_memo.encode())

		if lc == 0 and self.usr_contract_data and 'Token' not in self.name:
			return

		if lc != 1:
			die(1, f'{lc} output{suf(lc)} specified, but Ethereum transactions must have exactly one')

		a = self.parse_cmdline_arg(self.proto, cmd_args[0], ad_f, ad_w)

		self.add_output(
			coinaddr = None if a.is_vault else a.addr,
			amt      = self.proto.coin_amt(a.amt or '0'),
			is_chg   = not a.amt,
			is_vault = a.is_vault)

		self.add_mmaddrs_to_outputs(ad_f, ad_w)

	def get_unspent_nums_from_user(self, unspent):
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

	def network_fee_to_unit_disp(self, net_fee):
		return '{} Gwei'.format(self.pretty_fmt_fee(
			self.proto.coin_amt(net_fee.fee, from_unit='wei').to_unit('Gwei')))

	# get rel_fee (gas price) from network, return in native wei
	async def get_rel_fee_from_network(self):
		return self._net_fee(
			Int(await self.rpc.call('eth_gasPrice'), base=16),
			'eth_gasPrice')

	def check_chg_addr_is_wallet_addr(self):
		pass

	def check_fee(self):
		if not self.disable_fee_check:
			assert self.usr_fee <= self.proto.max_tx_fee

	@property
	def total_gas(self):
		return self.gas

	# given rel fee and units, return absolute fee using self.total_gas
	def fee_rel2abs(self, tx_size, amt_in_units, unit):
		return self.proto.coin_amt(int(amt_in_units * self.total_gas), from_unit=unit)

	# given fee estimate (gas price) in wei, return absolute fee, adjusting by self.cfg.fee_adjust
	def fee_est2abs(self, net_fee):
		ret = self.fee_gasPrice2abs(net_fee.fee) * self.cfg.fee_adjust
		if self.cfg.verbose:
			msg(f'Estimated fee: {net_fee.fee} ETH')
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

	async def get_input_addrs_from_inputs_opt(self):
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

	async def set_gas(self, *, to_addr=None, force=False):
		await super().set_gas(to_addr=to_addr, force=force)
		if self.is_swap and (force or not hasattr(self, 'router_gas')):
			self.router_gas = (
				int(self.cfg.router_gas) if self.cfg.router_gas else
				self.txobj['router_gas'] if self.txobj else
				self.dfl_router_gas)

	@property
	def total_gas(self):
		return self.gas + (self.router_gas if self.is_swap else 0)

	async def get_gas_estimateGas(self, *, to_addr=None):
		t = Token(
			self.cfg,
			self.proto,
			self.twctl.token,
			decimals = self.twctl.decimals,
			rpc = self.rpc)

		data = t.create_transfer_data(
			to_addr = to_addr or self.outputs[0].addr,
			amt = self.outputs[0].amt or await self.twctl.get_balance(self.inputs[0].addr),
			op = self.token_op)

		try:
			res = await t.do_call(
				f'{self.token_op}(address,uint256)',
				method = 'eth_estimateGas',
				from_addr = self.inputs[0].addr,
				data = data)
		except Exception as e:
			ymsg(
				'Unable to estimate gas limit via node. '
				'Please retry with --gas set to an integer value, or ‘fallback’ for a sane default')
			raise e

		return int(res, 16)

	async def make_txobj(self): # called by create_serialized()
		await super().make_txobj()
		t = Token(self.cfg, self.proto, self.twctl.token, decimals=self.twctl.decimals)
		o = self.txobj
		o['token_addr'] = t.addr
		o['decimals'] = t.decimals
		o['token_to'] = o['to']
		if self.is_swap:
			o['expiry'] = self.quote_data.data['expiry']
			o['router_gas'] = self.router_gas

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
