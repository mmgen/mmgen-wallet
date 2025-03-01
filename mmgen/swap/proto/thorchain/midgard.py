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
swap.proto.thorchain.midgard: THORChain swap protocol network query ops
"""

import json

class MidgardRPCClient:

	http_hdrs = {'Content-Type': 'application/json'}
	proto = 'https'
	host = 'thornode.ninerealms.com'
	verify = True
	timeout = 5

	def __init__(self, tx, proto=None, host=None):
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

	def get(self, path, timeout=None):
		return self.session.get(
			url     = self.proto + '://' + self.host + path,
			timeout = timeout or self.timeout,
			verify  = self.verify)

class Midgard:

	def __init__(self, tx, amt):
		self.tx = tx
		self.in_amt = amt
		self.rpc = MidgardRPCClient(tx)

	def get_quote(self):
		self.get_str = '/thorchain/quote/swap?from_asset={a}.{a}&to_asset={b}.{b}&amount={c}'.format(
			a = self.tx.send_proto.coin,
			b = self.tx.recv_proto.coin,
			c = self.in_amt.to_unit('satoshi'))
		self.result = self.rpc.get(self.get_str)
		self.data = json.loads(self.result.content)

	def format_quote(self):
		from ....util import make_timestr, pp_fmt, die
		from ....util2 import format_elapsed_hr
		from ....color import blue, cyan, pink, orange
		from . import name

		d = self.data
		if not 'expiry' in d:
			die(2, pp_fmt(d))
		tx = self.tx
		in_coin = tx.send_proto.coin
		out_coin = tx.recv_proto.coin
		out_amt = tx.recv_proto.coin_amt(int(d['expected_amount_out']), from_unit='satoshi')
		min_in_amt = tx.send_proto.coin_amt(int(d['recommended_min_amount_in']), from_unit='satoshi')
		gas_unit = {
			'satsperbyte': 'sat/byte',
		}.get(d['gas_rate_units'], d['gas_rate_units'])
		elapsed_disp = format_elapsed_hr(d['expiry'], future_msg='from now')
		fees = d['fees']
		fees_t = tx.recv_proto.coin_amt(int(fees['total']), from_unit='satoshi')
		fees_pct_disp = str(fees['total_bps'] / 100) + '%'
		slip_pct_disp = str(fees['slippage_bps'] / 100) + '%'
		hdr = f'SWAP QUOTE (source: {self.rpc.host})'
		return f"""
{cyan(hdr)}
  Protocol:                      {blue(name)}
  Direction:                     {orange(f'{in_coin} => {out_coin}')}
  Vault address:                 {cyan(d['inbound_address'])}
  Quote expires:                 {pink(elapsed_disp)} [{make_timestr(d['expiry'])}]
  Amount in:                     {self.in_amt.hl()} {in_coin}
  Expected amount out:           {out_amt.hl()} {out_coin}
  Rate:                          {(out_amt / self.in_amt).hl()} {out_coin}/{in_coin}
  Reverse rate:                  {(self.in_amt / out_amt).hl()} {in_coin}/{out_coin}
  Recommended minimum in amount: {min_in_amt.hl()} {in_coin}
  Recommended fee:               {pink(d['recommended_gas_rate'])} {pink(gas_unit)}
  Fees:
    Total:    {fees_t.hl()} {out_coin} ({pink(fees_pct_disp)})
    Slippage: {pink(slip_pct_disp)}
"""

	@property
	def inbound_address(self):
		return self.data['inbound_address']

	@property
	def rel_fee_hint(self):
		if self.data['gas_rate_units'] == 'satsperbyte':
			return f'{self.data["recommended_gas_rate"]}s'

	def __str__(self):
		from pprint import pformat
		return pformat(self.data)
