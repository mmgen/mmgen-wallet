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
proto.btc.tx.new: Bitcoin new transaction class
"""

import mmgen.tx.new as TxBase
from .base import Base
from ....opts import opt
from ....obj import HexStr,MMGenTxID
from ....util import msg,dmsg,vmsg,make_chksum_6,die

class New(Base,TxBase.New):
	usr_fee_prompt = 'Enter transaction fee: '
	fee_fail_fs = 'Network fee estimation for {c} confirmations failed ({t})'
	no_chg_msg = 'Warning: Change address will be deleted as transaction produces no change'

	@property
	def relay_fee(self):
		kb_fee = self.proto.coin_amt(self.rpc.cached['networkinfo']['relayfee'])
		ret = kb_fee * self.estimate_size() / 1024
		vmsg('Relay fee: {} {c}/kB, for transaction: {} {c}'.format(kb_fee,ret,c=self.coin))
		return ret

	async def get_rel_fee_from_network(self):
		try:
			ret = await self.rpc.call('estimatesmartfee',opt.fee_estimate_confs,opt.fee_estimate_mode.upper())
			fee_per_kb = ret['feerate'] if 'feerate' in ret else -2
			fe_type = 'estimatesmartfee'
		except:
			args = self.rpc.daemon.estimatefee_args(self.rpc)
			fee_per_kb = await self.rpc.call('estimatefee',*args)
			fe_type = 'estimatefee'

		return fee_per_kb,fe_type

	# given tx size, rel fee and units, return absolute fee
	def fee_rel2abs(self,tx_size,units,amt,unit):
		if tx_size:
			return self.proto.coin_amt(amt * tx_size * getattr(self.proto.coin_amt,units[unit]))
		else:
			return None

	# given network fee estimate in BTC/kB, return absolute fee using estimated tx size
	def fee_est2abs(self,fee_per_kb,fe_type=None):
		from decimal import Decimal
		tx_size = self.estimate_size()
		ret = self.proto.coin_amt(
			fee_per_kb * Decimal(opt.tx_fee_adj) * tx_size / 1024,
			from_decimal = True )
		if opt.verbose:
			msg(fmt(f"""
				{fe_type.upper()} fee for {opt.fee_estimate_confs} confirmations: {fee_per_kb} {self.coin}/kB
				TX size (estimated): {tx_size} bytes
				Fee adjustment factor: {opt.tx_fee_adj:.2f}
				Absolute fee (fee_per_kb * adj_factor * tx_size / 1024): {ret} {self.coin}
			""").strip())
		return ret

	def convert_and_check_fee(self,tx_fee,desc):
		abs_fee = self.feespec2abs(tx_fee,self.estimate_size())
		if abs_fee == None:
			raise ValueError(f'{tx_fee}: cannot convert {self.rel_fee_desc} to {self.coin}'
								+ ' because transaction size is unknown')
		if abs_fee == False:
			err = f'{tx_fee!r}: invalid TX fee (not a {self.coin} amount or {self.rel_fee_desc} specification)'
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

	def update_change_output(self,funds_left):
		if funds_left == 0: # TODO: test
			msg(self.no_chg_msg)
			self.outputs.pop(self.chg_idx)
		else:
			self.update_output_amt(
				self.chg_idx,
				self.proto.coin_amt(funds_left) )

	def check_fee(self):
		fee = self.sum_inputs() - self.sum_outputs()
		if fee > self.proto.max_tx_fee:
			c = self.proto.coin
			die( 'MaxFeeExceeded', f'Transaction fee of {fee} {c} too high! (> {self.proto.max_tx_fee} {c})' )

	def final_inputs_ok_msg(self,funds_left):
		return 'Transaction produces {} {} in change'.format(
			self.proto.coin_amt(funds_left).hl(),
			self.coin
		)

	async def create_serialized(self,locktime=None,bump=None):

		if not bump:
			self.inputs.sort_bip69()
			# do this only after inputs are sorted
			if opt.rbf:
				self.inputs[0].sequence = self.proto.max_int - 2 # handles the nLockTime case too
			elif locktime:
				self.inputs[0].sequence = self.proto.max_int - 1

		self.outputs.sort_bip69()

		inputs_list = [
			{'txid':e.txid,'vout':e.vout,'sequence':e.sequence} if n == 0 and e.sequence else
			{'txid':e.txid,'vout':e.vout}
				for n,e in enumerate(self.inputs) ]

		outputs_dict = {e.addr:e.amt for e in self.outputs}

		ret = await self.rpc.call( 'createrawtransaction', inputs_list, outputs_dict )

		if locktime and not bump:
			msg(f'Setting nLockTime to {self.strfmt_locktime(locktime)}!')
			assert isinstance(locktime,int), 'locktime value not an integer'
			self.locktime = locktime
			ret = ret[:-8] + bytes.fromhex('{:08x}'.format(locktime))[::-1].hex()

		# TxID is set only once!
		self.txid = MMGenTxID(make_chksum_6(bytes.fromhex(ret)).upper())

		self.update_serialized(ret)
