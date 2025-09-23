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
test.cmdtest_d.httpd.thornode.rpc: Thornode RPC HTTP server
"""

import re, json
from wsgiref.util import request_uri

from . import ThornodeServer

class ThornodeRPCServer(ThornodeServer):
	port = 18800
	name = 'thornode RPC server'

	def make_response_body(self, method, environ):

		class responses:

			def get_balance(m, length):
				return [
					{'denom': 'foocoin', 'amount': 321321321321},
					{'denom': 'rune',    'amount': 987654321321},
					{'denom': 'barcoin', 'amount': 123123123123}]

			def get_account_info(m, length):
				return {
					'value': {
						'address': m[1],
						'pub_key': 'PubKeySecp256k1{0000}',
						'account_number': '1234',
						'sequence': '333444'}}

			def get_tx_info(m, length):
				txid = environ['wsgi.input'].read(length).decode().removeprefix('hash=0x').upper()
				return {
					'hash': txid,
					'height': '21298600',
					'index': 2,
					'tx_result': {
						'gas_used': '173222',
						'events': [],
						'codespace': ''
					},
					'tx': 'MHgwMGZvb2Jhcg=='}

			def check_tx(m, length):
				return {
					'code': 0,
					'data': '',
					'log': '',
					'info': '',
					'gas_wanted': '-1',
					'gas_used': '53774',
					'events': [],
					'codespace': ''}

			def broadcast_tx_sync(m, length):
				txhex = environ['wsgi.input'].read(length).decode().removeprefix('tx=0x').upper()
				res = {'code': 0, 'codespace': '', 'data': '', 'log': ''}
				if txhex.startswith('0A540A52'):
					res.update({'hash': '14463C716CF08A814868DB779156BCD85A1DF8EE49E924900A74482E9DEE132D'})
				elif txhex.startswith('0AC1010A'):
					res.update({'hash': '17F9411E48542C0DCA4D40A0DD4A1795DE6D5791A873A27CBBDC1031FE8D1BC5'})
				return res

		pat_info = (
			('get_balance',       'GET',  r'/bank/balances/(\S+)'),
			('get_account_info',  'GET',  r'/auth/accounts/(\S+)'),
			('get_tx_info',       'POST', r'/tx$'),
			('check_tx',          'POST', r'/check_tx$'),
			('broadcast_tx_sync', 'POST', r'/broadcast_tx_sync$'))

		req_str = request_uri(environ)

		for name, method_chk, pat in pat_info:
			if m := re.search(pat, req_str):
				assert method == method_chk
				length = int(environ.get('CONTENT_LENGTH', '0')) if method == 'POST' else None
				res = getattr(responses, name)(m, length)
				return json.dumps({'result': res}).encode()

		raise ValueError(f'‘{req_str}’: malformed query path')
