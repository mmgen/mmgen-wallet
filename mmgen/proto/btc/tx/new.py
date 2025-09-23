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
proto.btc.tx.new: Bitcoin new transaction class
"""

from ....tx.new import New as TxNew
from ....obj import MMGenTxID
from ....util import msg, fmt, make_chksum_6, die, suf
from ....color import pink
from .base import Base

class New(Base, TxNew):
	usr_fee_prompt = 'Enter transaction fee: '
	fee_fail_fs = 'Network fee estimation for {c} confirmations failed ({t})'
	no_chg_msg = 'Warning: Change address will be deleted as transaction produces no change'
	msg_insufficient_funds = 'Selected outputs insufficient to fund this transaction ({} {} needed)'

	async def set_gas(self, *, to_addr=None, force=False):
		return None

	def process_data_output_arg(self, arg):
		if any(arg.startswith(pfx) for pfx in ('data:', 'hexdata:')):
			if hasattr(self, '_have_op_return_data'):
				die(1, 'Transaction may have at most one OP_RETURN data output!')
			self._have_op_return_data = True
			from .op_return_data import OpReturnData
			OpReturnData(self.proto, arg) # test data for validity
			return arg

	@property
	def relay_fee(self):
		kb_fee = self.proto.coin_amt(self.rpc.cached['networkinfo']['relayfee'])
		ret = kb_fee * self.estimate_size() / 1024
		self.cfg._util.vmsg(f'Relay fee: {kb_fee} {self.coin}/kB, for transaction: {ret} {self.coin}')
		return ret

	@property
	def network_estimated_fee_label(self):
		return 'Network-estimated ({}, {} conf{})'.format(
			self.cfg.fee_estimate_mode.upper(),
			pink(str(self.cfg.fee_estimate_confs)),
			suf(self.cfg.fee_estimate_confs))

	def warn_fee_estimate_fail(self, fe_type):
		if not hasattr(self, '_fee_estimate_fail_warning_shown'):
			msg(self.fee_fail_fs.format(
				c = self.cfg.fee_estimate_confs,
				t = fe_type))
			self._fee_estimate_fail_warning_shown = True

	def network_fee_to_unit_disp(self, net_fee):
		return '{} sat/byte'.format(net_fee.fee.to_unit('satoshi') // 1024)

	async def get_rel_fee_from_network(self):
		try:
			ret = await self.rpc.call(
				'estimatesmartfee',
				self.cfg.fee_estimate_confs,
				self.cfg.fee_estimate_mode.upper())
			fee_per_kb = self.proto.coin_amt(ret['feerate']) if 'feerate' in ret else None
			fe_type = 'estimatesmartfee'
		except:
			args = self.rpc.daemon.estimatefee_args(self.rpc)
			ret = await self.rpc.call('estimatefee', *args)
			fee_per_kb = self.proto.coin_amt(ret)
			fe_type = 'estimatefee'

		if fee_per_kb is None:
			self.warn_fee_estimate_fail(fe_type)

		return self._net_fee(fee_per_kb, fe_type)

	# given tx size, rel fee and units, return absolute fee
	def fee_rel2abs(self, tx_size, amt_in_units, unit):
		return self.proto.coin_amt(int(amt_in_units * tx_size), from_unit=unit)

	# given network fee estimate in BTC/kB, return absolute fee using estimated tx size
	def fee_est2abs(self, net_fee):
		tx_size = self.estimate_size()
		ret = self.proto.coin_amt('1') * (net_fee.fee * self.cfg.fee_adjust * tx_size / 1024)
		if self.cfg.verbose:
			msg(fmt(f"""
				{net_fee.type.upper()} fee for {self.cfg.fee_estimate_confs} confirmations: {net_fee.fee} {self.coin}/kB
				TX size (estimated): {tx_size} bytes
				Fee adjustment factor: {self.cfg.fee_adjust:.2f}
				Absolute fee (net_fee.fee * adj_factor * tx_size / 1024): {ret} {self.coin}
			""").strip())
		return ret

	def convert_and_check_fee(self, fee, desc):
		match self.feespec2abs(fee, self.estimate_size()): # abs_fee
			case None:
				raise ValueError(
					f'{fee}: cannot convert {self.rel_fee_desc} to {self.coin} '
					+ 'because transaction size is unknown')
			case False:
				msg(f'{fee!r}: invalid TX fee (not a {self.coin} amount or {self.rel_fee_desc} specification)')
			case x if x > self.proto.max_tx_fee:
				msg(f'{x} {self.coin}: {desc} fee too large (maximum fee: {self.proto.max_tx_fee} {self.coin})')
			case x if x < self.relay_fee:
				msg(f'{x} {self.coin}: {desc} fee too small (less than relay fee of {self.relay_fee} {self.coin})')
			case x:
				return x
		return False

	async def get_input_addrs_from_inputs_opt(self):
		# Bitcoin full node, call doesn't go to the network, so just call listunspent with addrs=[]
		return []

	def update_change_output(self, funds_left):
		if funds_left == 0: # TODO: test
			msg(self.no_chg_msg)
			self.outputs.pop(self.chg_idx)
		else:
			self.update_output_amt(self.chg_idx, funds_left)

	def check_fee(self):
		fee = self.sum_inputs() - self.sum_outputs()
		if fee > self.proto.max_tx_fee:
			c = self.proto.coin
			die('MaxFeeExceeded', f'Transaction fee of {fee} {c} too high! (> {self.proto.max_tx_fee} {c})')

	def final_inputs_ok_msg(self, funds_left):
		return 'Transaction produces {} {} in change'.format(funds_left.hl(), self.coin)

	def check_chg_addr_is_wallet_addr(self):
		if len(self.nondata_outputs) > 1 and not self.chg_output.mmid:
			self._non_wallet_addr_confirm('Change address is not an MMGen wallet address!')

	async def create_serialized(self, *, locktime=None):

		if not self.is_bump:
			# Set all sequence numbers to the same value, in conformity with the behavior of most modern wallets:
			do_rbf = self.proto.cap('rbf') and not self.cfg.no_rbf
			seqnum_val = self.proto.max_int - (2 if do_rbf else 1 if locktime else 0)
			for i in self.inputs:
				i.sequence = seqnum_val

		if not self.is_swap:
			self.inputs.sort_bip69()
			self.outputs.sort_bip69()

		inputs_list = [{
				'txid':     e.txid,
				'vout':     e.vout,
				'sequence': e.sequence
			} for e in self.inputs]

		outputs_dict = dict((e.addr, e.amt) if e.addr else ('data', e.data.hex()) for e in self.outputs)

		ret = await self.rpc.call('createrawtransaction', inputs_list, outputs_dict)

		if locktime and not self.is_bump:
			msg(f'Setting nLockTime to {self.info.strfmt_locktime(locktime)}!')
			assert isinstance(locktime, int), 'locktime value not an integer'
			self.locktime = locktime
			ret = ret[:-8] + bytes.fromhex(f'{locktime:08x}')[::-1].hex()

		# TxID is set only once!
		self.txid = MMGenTxID(make_chksum_6(bytes.fromhex(ret)).upper())

		self.update_serialized(ret)
