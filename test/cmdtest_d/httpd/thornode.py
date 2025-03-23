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
test.cmdtest_d.httpd.thornode: Thornode WSGI http server
"""

import time, re, json

from mmgen.cfg import Config
from mmgen.amt import UniAmt

from . import HTTPD

cfg = Config()

# https://thornode.ninerealms.com/thorchain/quote/swap?from_asset=BCH.BCH&to_asset=LTC.LTC&amount=1000000
sample_request = 'GET /thorchain/quote/swap?from_asset=BCH.BCH&to_asset=LTC.LTC&amount=1000000000'
request_pat = r'/thorchain/quote/swap\?from_asset=(\S+)\.(\S+)&to_asset=(\S+)\.(\S+)&amount=(\d+)'
prices = {'BTC': 97000, 'LTC': 115, 'BCH': 330, 'ETH': 2304}
gas_rate_units = {'ETH': 'gwei', 'BTC': 'satsperbyte'}
recommended_gas_rate = {'ETH': '1', 'BTC': '6'}

data_template = {
	'inbound_address': None,
	'inbound_confirmation_blocks': 4,
	'inbound_confirmation_seconds': 2400,
	'outbound_delay_blocks': 5,
	'outbound_delay_seconds': 30,
	'fees': {
		'asset': 'LTC.LTC',
		'affiliate': '0',
		'outbound': '878656',
		'liquidity': '8945012',
		'total': '9823668',
		'slippage_bps': 31,
		'total_bps': 34
	},
	'expiry': None,
	'warning': 'Do not cache this response. Do not send funds after the expiry.',
	'notes': 'First output should be to inbound_address, second output should be change back to self, third output should be OP_RETURN, limited to 80 bytes. Do not send below the dust threshold. Do not use exotic spend scripts, locks or address formats.',
	'dust_threshold': '10000',
	'recommended_min_amount_in': '1222064',
	'recommended_gas_rate': '6',
	'gas_rate_units': 'satsperbyte',
	'expected_amount_out': None,
	'max_streaming_quantity': 0,
	'streaming_swap_blocks': 0,
	'total_swap_seconds': 2430
}

def make_inbound_addr(proto, mmtype):
	from mmgen.tool.coin import tool_cmd
	n = int(time.time()) // (60 * 60 * 24) # increments once every 24 hrs
	ret = tool_cmd(
		cfg     = cfg,
		cmdname = 'pubhash2addr',
		proto   = proto,
		mmtype  = mmtype).pubhash2addr(f'{n:040x}')
	return '0x' + ret if proto.is_evm else ret

class ThornodeServer(HTTPD):
	name = 'thornode server'
	port = 18800
	content_type = 'application/json'

	def make_response_body(self, method, environ):
		from wsgiref.util import request_uri

		m = re.search(request_pat, request_uri(environ))
		_, send_coin, _, recv_coin, amt_atomic = m.groups()

		from mmgen.protocol import init_proto
		send_proto = init_proto(cfg, send_coin, network='regtest', need_amt=True)
		in_amt = UniAmt(int(amt_atomic), from_unit='satoshi')
		out_amt = in_amt * (prices[send_coin] / prices[recv_coin])

		addr = make_inbound_addr(send_proto, send_proto.preferred_mmtypes[0])
		data = data_template | {
			'expected_amount_out': str(out_amt.to_unit('satoshi')),
			'expiry': int(time.time()) + (10 * 60),
			'inbound_address': addr,
			'gas_rate_units': gas_rate_units[send_proto.base_proto_coin],
			'recommended_gas_rate': recommended_gas_rate[send_proto.base_proto_coin],
		}
		return json.dumps(data).encode()
