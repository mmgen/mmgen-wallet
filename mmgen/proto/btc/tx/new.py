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
proto.btc.tx.new: Bitcoin new transaction class
"""

from ....tx import new as TxBase
from ....obj import MMGenTxID
from ....util import msg, fmt, make_chksum_6, die, suf
from ....color import pink
from .base import Base

class New(Base, TxBase.New):
	usr_fee_prompt = 'Enter transaction fee: '
	fee_fail_fs = 'Network fee estimation for {c} confirmations failed ({t})'
	no_chg_msg = 'Warning: Change address will be deleted as transaction produces no change'

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

		return fee_per_kb, fe_type

	# given tx size, rel fee and units, return absolute fee
	def fee_rel2abs(self, tx_size, units, amt_in_units, unit):
		return self.proto.coin_amt(amt_in_units * tx_size, from_unit=units[unit])

	# given network fee estimate in BTC/kB, return absolute fee using estimated tx size
	def fee_est2abs(self, fee_per_kb, fe_type=None):
		from decimal import Decimal
		tx_size = self.estimate_size()
		ret = self.proto.coin_amt('1') * (fee_per_kb * self.cfg.fee_adjust * tx_size / 1024)
		if self.cfg.verbose:
			msg(fmt(f"""
				{fe_type.upper()} fee for {self.cfg.fee_estimate_confs} confirmations: {fee_per_kb} {self.coin}/kB
				TX size (estimated): {tx_size} bytes
				Fee adjustment factor: {self.cfg.fee_adjust:.2f}
				Absolute fee (fee_per_kb * adj_factor * tx_size / 1024): {ret} {self.coin}
			""").strip())
		return ret

	def convert_and_check_fee(self, fee, desc):
		abs_fee = self.feespec2abs(fee, self.estimate_size())
		if abs_fee is None:
			raise ValueError(f'{fee}: cannot convert {self.rel_fee_desc} to {self.coin}'
								+ ' because transaction size is unknown')
		if abs_fee is False:
			err = f'{fee!r}: invalid TX fee (not a {self.coin} amount or {self.rel_fee_desc} specification)'
		elif abs_fee > self.proto.max_tx_fee:
			err = f'{abs_fee} {self.coin}: {desc} fee too large (maximum fee: {self.proto.max_tx_fee} {self.coin})'
		elif abs_fee < self.relay_fee:
			err = f'{abs_fee} {self.coin}: {desc} fee too small (less than relay fee of {self.relay_fee} {self.coin})'
		else:
			return abs_fee
		msg(err)
		return False

	async def get_input_addrs_from_cmdline(self):
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

	async def create_serialized(self, locktime=None, bump=None):

		if not bump:
			self.inputs.sort_bip69()
			# Set all sequence numbers to the same value, in conformity with the behavior of most modern wallets:
			do_rbf = self.proto.cap('rbf') and not self.cfg.no_rbf
			seqnum_val = self.proto.max_int - (2 if do_rbf else 1 if locktime else 0)
			for i in self.inputs:
				i.sequence = seqnum_val

		self.outputs.sort_bip69()

		inputs_list = [{
				'txid':     e.txid,
				'vout':     e.vout,
				'sequence': e.sequence
			} for e in self.inputs]

		outputs_dict = {e.addr:e.amt for e in self.outputs}

		ret = await self.rpc.call('createrawtransaction', inputs_list, outputs_dict)

		if locktime and not bump:
			msg(f'Setting nLockTime to {self.info.strfmt_locktime(locktime)}!')
			assert isinstance(locktime, int), 'locktime value not an integer'
			self.locktime = locktime
			ret = ret[:-8] + bytes.fromhex(f'{locktime:08x}')[::-1].hex()

		# TxID is set only once!
		self.txid = MMGenTxID(make_chksum_6(bytes.fromhex(ret)).upper())

		self.update_serialized(ret)
