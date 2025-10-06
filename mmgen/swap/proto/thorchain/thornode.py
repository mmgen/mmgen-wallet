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
swap.proto.thorchain.thornode: THORChain swap protocol network query ops
"""

import time, json
from collections import namedtuple

from ....protocol import init_proto
from ....amt import UniAmt
from ....http import HTTPClient

_gd = namedtuple('gas_unit_data', ['code', 'disp'])
gas_unit_data = {
	'satsperbyte': _gd('s', 'sat/byte'),
	'gwei':        _gd('G', 'Gwei'),
}

class ThornodeSwapClient(HTTPClient):

	http_hdrs = {'Content-Type': 'application/json'}
	timeout = 5

	def __init__(self, tx, *, network_proto=None, host=None):
		rune_proto = init_proto(tx.cfg, 'rune', network=tx.cfg._proto.network)
		for k, v in rune_proto.rpc_swap_params.items():
			setattr(self, k, v)
		super().__init__(tx.cfg, network_proto=network_proto, host=host)

class Thornode:

	def __init__(self, tx, amt):
		self.tx = tx
		self.in_amt = UniAmt(f'{amt:.8f}')
		self.rpc = ThornodeSwapClient(tx)

	def get_quote(self, swap_cfg):

		def get_data(send, recv, amt):
			get_str = (
				'/thorchain/quote/swap?'
				f'from_asset={send}&'
				f'to_asset={recv}&'
				f'amount={amt}&'
				f'streaming_interval={swap_cfg.stream_interval}')
			data = json.loads(self.rpc.get(path=get_str))
			if not 'expiry' in data:
				from ....util import pp_fmt, die
				die(2, pp_fmt(data))
			return data

		if (
				(self.tx.proto.tokensym or self.tx.recv_asset.tokensym)
				and not self.tx.send_asset.chain == 'THOR'): # token swap
			in_data = get_data(
				self.tx.send_asset.full_name,
				'THOR.RUNE',
				self.in_amt.to_unit('satoshi'))
			if self.tx.proto.network != 'regtest':
				time.sleep(1.1) # ninerealms max request rate 1/sec
			out_data = get_data(
				'THOR.RUNE',
				self.tx.recv_asset.full_name,
				in_data['expected_amount_out'])
			self.data = in_data | {
				'expected_amount_out': out_data['expected_amount_out'],
				'fees': out_data['fees'],
				'expiry': min(in_data['expiry'], out_data['expiry'])}
		else:
			self.data = get_data(
				self.tx.send_asset.full_name,
				self.tx.recv_asset.full_name,
				self.in_amt.to_unit('satoshi'))

	async def format_quote(self, trade_limit, *, deduct_est_fee=False):
		from ....util import make_timestr, ymsg
		from ....util2 import format_elapsed_hr
		from ....color import blue, green, cyan, pink, orange, redbg, yelbg, grnbg
		from . import name

		d = self.data
		tx = self.tx
		in_coin = tx.send_asset.short_name
		out_coin = tx.recv_asset.short_name
		in_amt = self.in_amt
		out_amt = UniAmt(int(d['expected_amount_out']), from_unit='satoshi')
		if tx.proto.has_usr_fee:
			gas_unit = d['gas_rate_units']

		if trade_limit:
			from . import ExpInt4
			tl_int = ExpInt4(trade_limit.to_unit('satoshi'))
			tl_uniamt = UniAmt(tl_int.trunc, from_unit='satoshi')
			ratio = float(tl_uniamt / out_amt)
			direction = 'ABOVE' if ratio > 1 else 'below'
			mcolor, lblcolor = (
				(redbg, redbg) if (ratio < 0.93 or ratio > 0.999) else
				(yelbg, yelbg) if ratio < 0.97 else
				(green, grnbg))
			trade_limit_disp = f"""
  {lblcolor('Trade limit:')}                   {tl_uniamt.hl()} {out_coin} """ + mcolor(
				f'({abs(1 - ratio) * 100:0.2f}% {direction} expected amount)')
			tx_size_adj = len(tl_int.enc) - 1
			if tx.proto.is_evm:
				tx.adj_gas_with_extra_data_len(len(tl_int.enc) - 1) # one-shot method, no-op if repeated
		else:
			trade_limit_disp = ''
			tx_size_adj = 0

		def get_estimated_fee():
			return tx.feespec2abs(
				fee_arg = d['recommended_gas_rate'] + gas_unit_data[gas_unit].code,
				tx_size = None if tx.proto.is_vm else tx.estimate_size() + tx_size_adj)

		_amount_in_label = 'Amount in:'
		if deduct_est_fee:
			if not tx.proto.has_usr_fee:
				in_amt -= tx.usr_fee
				out_amt *= (in_amt / self.in_amt)
				_amount_in_label = 'Amount in:'
			elif gas_unit in gas_unit_data:
				in_amt -= UniAmt(f'{get_estimated_fee():.8f}')
				out_amt *= (in_amt / self.in_amt)
				_amount_in_label = 'Amount in (estimated):'
			else:
				ymsg(f'Warning: unknown gas unit ‘{gas_unit}’, cannot estimate fee')

		min_in_amt = UniAmt(int(d['recommended_min_amount_in']), from_unit='satoshi')
		elapsed_disp = format_elapsed_hr(d['expiry'], future_msg='from now')
		fees = d['fees']
		fees_t = UniAmt(int(fees['total']), from_unit='satoshi')
		fees_pct_disp = str(fees['total_bps'] / 100) + '%'
		slip_pct_disp = str(fees['slippage_bps'] / 100) + '%'
		hdr = f'SWAP QUOTE (source: {self.rpc.host})'

		vault_info = '' if tx.send_asset.chain == 'THOR' else """
  Vault address:                 {}""".format(cyan(self.inbound_address))

		fee_info = '' if not tx.proto.has_usr_fee else """
  Recommended fee:               {} {}
  Network-estimated fee:         {} (from node)""".format(
			pink(d['recommended_gas_rate']),
			pink(_.disp if (_ := gas_unit_data.get(gas_unit)) else gas_unit),
			await self.tx.network_fee_disp())

		return f"""
{cyan(hdr)}
  Protocol:                      {blue(name)}
  Direction:                     {orange(f'{tx.send_asset.name} => {tx.recv_asset.name}')}{vault_info}
  Quote expires:                 {pink(elapsed_disp)} [{make_timestr(d['expiry'])}]
  {_amount_in_label:<22}         {in_amt.hl()} {in_coin}
  Expected amount out:           {out_amt.hl()} {out_coin}{trade_limit_disp}
  Rate:                          {(out_amt / in_amt).hl()} {out_coin}/{in_coin}
  Reverse rate:                  {(in_amt / out_amt).hl()} {in_coin}/{out_coin}
  Recommended minimum in amount: {min_in_amt.hl()} {in_coin}{fee_info}
  Fees:
    Total:    {fees_t.hl()} {out_coin} ({pink(fees_pct_disp)})
    Slippage: {pink(slip_pct_disp)}
"""

	@property
	def inbound_address(self):
		addr = self.data['inbound_address']
		return addr.removeprefix('0x') if self.tx.proto.is_evm else addr

	@property
	def router(self):
		return self.data['router'].lower().removeprefix('0x')

	@property
	def rel_fee_hint(self):
		if self.tx.proto.has_usr_fee:
			gas_unit = self.data['gas_rate_units']
			if gas_unit in gas_unit_data:
				return self.data['recommended_gas_rate'] + gas_unit_data[gas_unit].code

	def __str__(self):
		from pprint import pformat
		return pformat(self.data)
