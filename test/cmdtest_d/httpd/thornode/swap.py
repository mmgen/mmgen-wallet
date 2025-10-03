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
test.cmdtest_d.httpd.thornode.swap: Thornode swap HTTP server
"""

import time, re, json
from wsgiref.util import request_uri

from mmgen.amt import UniAmt
from mmgen.protocol import init_proto

from ...include.common import eth_inbound_addr, thorchain_router_addr_file

from . import ThornodeServer

# https://thornode.ninerealms.com/thorchain/quote/swap?from_asset=BCH.BCH&to_asset=LTC.LTC&amount=1000000
prices = {'BTC': 97000, 'LTC': 115, 'BCH': 330, 'ETH': 2304, 'MM1': 0.998, 'RUNE': 1.4}
gas_rate_units = {'ETH': 'gwei', 'BTC': 'satsperbyte'}
recommended_gas_rate = {'ETH': '1', 'BTC': '6'}

data_template_from_rune = {
	'outbound_delay_blocks': 0,
	'outbound_delay_seconds': 0,
	'fees': {
		'asset': 'BTC.BTC',
		'affiliate': '0',
		'outbound': '1182',
		'liquidity': '110',
		'total': '1292',
		'slippage_bps': 7,
		'total_bps': 92
	},
	'warning': 'Do not cache this response. Do not send funds after the expiry.',
	'notes': 'Broadcast a MsgDeposit to the THORChain network with the appropriate memo. Do not use multi-in, multi-out transactions.',
	'max_streaming_quantity': 0,
	'streaming_swap_blocks': 0
}

data_template_to_rune = {
	'inbound_confirmation_blocks': 2,
	'inbound_confirmation_seconds': 24,
	'outbound_delay_blocks': 0,
	'outbound_delay_seconds': 0,
	'fees': {
		'asset': 'THOR.RUNE',
		'affiliate': '0',
		'outbound': '2000000',
		'liquidity': '684966',
		'total': '2684966',
		'slippage_bps': 8,
		'total_bps': 31
	},
	'router': '0xD37BbE5744D730a1d98d8DC97c42F0Ca46aD7146',
	'warning': 'Do not cache this response. Do not send funds after the expiry.',
	'notes': 'Base Asset: Send the inbound_address the asset with the memo encoded in hex in the data field. Tokens: First approve router to spend tokens from user: asset.approve(router, amount). Then call router.depositWithExpiry(inbound_address, asset, amount, memo, expiry). Asset is the token contract address. Amount should be in native asset decimals (eg 1e18 for most tokens). Do not swap to smart contract addresses.',
	'dust_threshold': '1',
	'recommended_gas_rate': '1',
	'max_streaming_quantity': 0,
	'streaming_swap_blocks': 0,
	'total_swap_seconds': 24
}

data_template_btc = {
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
	'warning': 'Do not cache this response. Do not send funds after the expiry.',
	'notes': 'First output should be to inbound_address, second output should be change back to self, third output should be OP_RETURN, limited to 80 bytes. Do not send below the dust threshold. Do not use exotic spend scripts, locks or address formats.',
	'dust_threshold': '10000',
	'max_streaming_quantity': 0,
	'streaming_swap_blocks': 0,
	'total_swap_seconds': 2430
}

data_template_eth = {
	'inbound_confirmation_blocks': 2,
	'inbound_confirmation_seconds': 24,
	'outbound_delay_blocks': 0,
	'outbound_delay_seconds': 0,
	'fees': {
		'asset': 'BTC.BTC',
		'affiliate': '0',
		'outbound': '1097',
		'liquidity': '77',
		'total': '1174',
		'slippage_bps': 15,
		'total_bps': 237
	},
	'router': '0xD37BbE5744D730a1d98d8DC97c42F0Ca46aD7146',
	'warning': 'Do not cache this response. Do not send funds after the expiry.',
	'notes': 'Base Asset: Send the inbound_address the asset with the memo encoded in hex in the data field. Tokens: First approve router to spend tokens from user: asset.approve(router, amount). Then call router.depositWithExpiry(inbound_address, asset, amount, memo, expiry). Asset is the token contract address. Amount should be in native asset decimals (eg 1e18 for most tokens). Do not swap to smart contract addresses.',
	'recommended_gas_rate': '1',
	'max_streaming_quantity': 0,
	'streaming_swap_blocks': 0,
	'total_swap_seconds': 24
}

def make_inbound_addr(cfg, proto, mmtype):
	if proto.is_evm:
		return '0x' + eth_inbound_addr # non-checksummed as per ninerealms thornode
	else:
		from mmgen.tool.coin import tool_cmd
		n = int(time.time()) // (60 * 60 * 24) # increments once every 24 hrs
		return tool_cmd(
			cfg     = cfg,
			cmdname = 'pubhash2addr',
			proto   = proto,
			mmtype  = mmtype).pubhash2addr(f'{n:040x}')

class ThornodeSwapServer(ThornodeServer):
	port = 18900
	name = 'thornode swap server'
	request_pat = r'/thorchain/quote/swap\?from_asset=(\S+)\.(\S+)&to_asset=(\S+)\.(\S+)&amount=(\d+)'

	def make_response_body(self, method, environ):

		m = re.search(self.request_pat, request_uri(environ))
		send_chain, send_asset, recv_chain, recv_asset, amt_atomic = m.groups()

		in_amt = UniAmt(int(amt_atomic), from_unit='satoshi')
		out_amt = in_amt * (prices[send_asset] / prices[recv_asset])

		data_template = (
			data_template_from_rune if send_asset == 'RUNE' else
			data_template_to_rune if recv_asset == 'RUNE' else
			data_template_eth if send_asset == 'ETH' else
			data_template_btc)

		data = data_template | {
			'recommended_min_amount_in': str(int(70 * 10**8 / prices[send_asset])), # $70
			'expected_amount_out': str(out_amt.to_unit('satoshi')),
			'expiry': int(time.time()) + (10 * 60),
		}

		if send_asset != 'RUNE':
			send_proto = init_proto(self.cfg, send_chain, network='regtest', need_amt=True)
			data.update({
				'inbound_address': make_inbound_addr(self.cfg, send_proto, send_proto.preferred_mmtypes[0]),
				'gas_rate_units': gas_rate_units[send_proto.base_proto_coin],
				'recommended_gas_rate': recommended_gas_rate[send_proto.base_proto_coin]
			})

		if send_asset == 'MM1':
			eth_proto = init_proto(self.cfg, 'eth', network='regtest')
			with open(thorchain_router_addr_file) as fh:
				raw_addr = fh.read().strip()
			data['router'] = '0x' + eth_proto.checksummed_addr(raw_addr)

		return json.dumps(data).encode()
