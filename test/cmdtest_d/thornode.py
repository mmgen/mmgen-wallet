#!/usr/bin/env python3

import json, re, time
from http.server import HTTPServer, BaseHTTPRequestHandler

from mmgen.cfg import Config
from mmgen.util import msg, make_timestr

cfg = Config()

def make_inbound_addr(proto, mmtype):
	from mmgen.tool.coin import tool_cmd
	n = int(time.time()) // (60 * 60 * 24) # increments once every 24 hrs
	return tool_cmd(
		cfg     = cfg,
		cmdname = 'pubhash2addr',
		proto   = proto,
		mmtype  = mmtype).pubhash2addr(f'{n:040x}')

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

# https://thornode.ninerealms.com/thorchain/quote/swap?from_asset=BCH.BCH&to_asset=LTC.LTC&amount=1000000

sample_request = 'GET /thorchain/quote/swap?from_asset=BCH.BCH&to_asset=LTC.LTC&amount=1000000000 HTTP/1.1'

request_pat = r'/thorchain/quote/swap\?from_asset=(\S+)\.(\S+)&to_asset=(\S+)\.(\S+)&amount=(\d+) HTTP/'

prices = { 'BTC': 97000, 'LTC': 115, 'BCH': 330 }

def create_data(request_line):
	m = re.search(request_pat, request_line)
	try:
		_, send_coin, _, recv_coin, amt_atomic = m.groups()
	except Exception as e:
		msg(f'{type(e)}: {e}')
		return {}

	from mmgen.protocol import init_proto
	send_proto = init_proto(cfg, send_coin, network='regtest', need_amt=True)
	in_amt = send_proto.coin_amt(int(amt_atomic), from_unit='satoshi')
	out_amt = in_amt * (prices[send_coin] / prices[recv_coin])

	addr = make_inbound_addr(send_proto, send_proto.preferred_mmtypes[0])
	expiry = int(time.time()) + (10 * 60)
	return data_template | {
		'expected_amount_out': str(out_amt.to_unit('satoshi')),
		'expiry': expiry,
		'inbound_address': addr,
	}

class handler(BaseHTTPRequestHandler):
	header = b'HTTP/1.1 200 OK\nContent-type: application/json\n\n'

	def do_GET(self):
		# print(f'Thornode server received:\n  {self.requestline}')
		self.wfile.write(self.header + json.dumps(create_data(self.requestline)).encode())

def run_thornode_server(server_class=HTTPServer, handler_class=handler):
	print('Thornode server listening on port 18800')
	server_address = ('localhost', 18800)
	httpd = server_class(server_address, handler_class)
	httpd.serve_forever()
	print('Thornode server exiting')
