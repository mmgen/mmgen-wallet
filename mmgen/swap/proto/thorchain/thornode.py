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

import json
from collections import namedtuple
from ....amt import UniAmt

_gd = namedtuple('gas_unit_data', ['code', 'disp'])
gas_unit_data = {
	'satsperbyte': _gd('s', 'sat/byte'),
	'gwei':        _gd('G', 'Gwei'),
}

class ThornodeRPCClient:

	http_hdrs = {'Content-Type': 'application/json'}
	proto = 'https'
	host = 'thornode.ninerealms.com'
	verify = True
	timeout = 5

	def __init__(self, tx, *, proto=None, host=None):
		self.cfg = tx.cfg
		if proto:
			self.proto = proto
		if host:
			self.host = host
		import requests
		self.session = requests.Session()
		self.session.trust_env = False # ignore *_PROXY environment vars
		self.session.headers = self.http_hdrs
		if self.cfg.proxy:
			self.session.proxies.update({
				'http':  f'socks5h://{self.cfg.proxy}',
				'https': f'socks5h://{self.cfg.proxy}'
			})

	def get(self, path, *, timeout=None):
		return self.session.get(
			url     = self.proto + '://' + self.host + path,
			timeout = timeout or self.timeout,
			verify  = self.verify)

class Thornode:

	def __init__(self, tx, amt):
		self.tx = tx
		self.in_amt = UniAmt(f'{amt:.8f}')
		self.rpc = ThornodeRPCClient(tx)

	def get_quote(self):
		self.get_str = '/thorchain/quote/swap?from_asset={a}.{a}&to_asset={b}.{b}&amount={c}'.format(
			a = self.tx.proto.coin,
			b = self.tx.recv_proto.coin,
			c = self.in_amt.to_unit('satoshi'))
		self.result = self.rpc.get(self.get_str)
		self.data = json.loads(self.result.content)
		if not 'expiry' in self.data:
			from ....util import pp_fmt, die
			die(2, pp_fmt(self.data))

	async def format_quote(self, trade_limit, usr_trade_limit, *, deduct_est_fee=False):
		from ....util import make_timestr, ymsg
		from ....util2 import format_elapsed_hr
		from ....color import blue, green, cyan, pink, orange, redbg, yelbg, grnbg
		from . import name

		d = self.data
		tx = self.tx
		in_coin = tx.proto.coin
		out_coin = tx.recv_proto.coin
		in_amt = self.in_amt
		out_amt = UniAmt(int(d['expected_amount_out']), from_unit='satoshi')
		gas_unit = d['gas_rate_units']

		if trade_limit:
			from . import ExpInt4
			e = ExpInt4(trade_limit.to_unit('satoshi'))
			tl_rounded = UniAmt(e.trunc, from_unit='satoshi')
			ratio = usr_trade_limit if type(usr_trade_limit) is float else float(tl_rounded / out_amt)
			direction = 'ABOVE' if ratio > 1 else 'below'
			mcolor, lblcolor = (
				(redbg, redbg) if (ratio < 0.93 or ratio > 0.999) else
				(yelbg, yelbg) if ratio < 0.97 else
				(green, grnbg))
			trade_limit_disp = f"""
  {lblcolor('Trade limit:')}                   {tl_rounded.hl()} {out_coin} """ + mcolor(
				f'({abs(1 - ratio) * 100:0.2f}% {direction} expected amount)')
			tx_size_adj = len(e.enc) - 1
			if tx.proto.is_evm:
				tx.adj_gas_with_extra_data_len(len(e.enc) - 1) # one-shot method, no-op if repeated
		else:
			trade_limit_disp = ''
			tx_size_adj = 0

		def get_estimated_fee():
			return tx.feespec2abs(
				fee_arg = d['recommended_gas_rate'] + gas_unit_data[gas_unit].code,
				tx_size = None if tx.proto.is_evm else tx.estimate_size() + tx_size_adj)

		_amount_in_label = 'Amount in:'
		if deduct_est_fee:
			if gas_unit in gas_unit_data:
				in_amt -= UniAmt(f'{get_estimated_fee():.8f}')
				out_amt *= (in_amt / self.in_amt)
				_amount_in_label = 'Amount in (estimated):'
			else:
				ymsg(f'Warning: unknown gas unit ‘{gas_unit}’, cannot estimate fee')

		min_in_amt = UniAmt(int(d['recommended_min_amount_in']), from_unit='satoshi')
		gas_unit_disp = _.disp if (_ := gas_unit_data.get(gas_unit)) else gas_unit
		elapsed_disp = format_elapsed_hr(d['expiry'], future_msg='from now')
		fees = d['fees']
		fees_t = UniAmt(int(fees['total']), from_unit='satoshi')
		fees_pct_disp = str(fees['total_bps'] / 100) + '%'
		slip_pct_disp = str(fees['slippage_bps'] / 100) + '%'
		hdr = f'SWAP QUOTE (source: {self.rpc.host})'

		return f"""
{cyan(hdr)}
  Protocol:                      {blue(name)}
  Direction:                     {orange(f'{in_coin} => {out_coin}')}
  Vault address:                 {cyan(self.inbound_address)}
  Quote expires:                 {pink(elapsed_disp)} [{make_timestr(d['expiry'])}]
  {_amount_in_label:<22}         {in_amt.hl()} {in_coin}
  Expected amount out:           {out_amt.hl()} {out_coin}{trade_limit_disp}
  Rate:                          {(out_amt / in_amt).hl()} {out_coin}/{in_coin}
  Reverse rate:                  {(in_amt / out_amt).hl()} {in_coin}/{out_coin}
  Recommended minimum in amount: {min_in_amt.hl()} {in_coin}
  Recommended fee:               {pink(d['recommended_gas_rate'])} {pink(gas_unit_disp)}
  Network-estimated fee:         {await self.tx.network_fee_disp()} (from node)
  Fees:
    Total:    {fees_t.hl()} {out_coin} ({pink(fees_pct_disp)})
    Slippage: {pink(slip_pct_disp)}
"""

	@property
	def inbound_address(self):
		addr = self.data['inbound_address']
		return addr.removeprefix('0x') if self.tx.proto.is_evm else addr

	@property
	def rel_fee_hint(self):
		gas_unit = self.data['gas_rate_units']
		if gas_unit in gas_unit_data:
			return self.data['recommended_gas_rate'] + gas_unit_data[gas_unit].code

	def __str__(self):
		from pprint import pformat
		return pformat(self.data)
