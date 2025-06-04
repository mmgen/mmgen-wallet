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
	name = 'thornode RPC server'

	def make_response_body(self, method, environ):
		req_str = request_uri(environ)

		if re.search(r'/bank/balances/(\S+)', req_str):
			data = {
				'result': [
					{'denom': 'foocoin', 'amount': 321321321321},
					{'denom': 'rune',    'amount': 987654321321},
					{'denom': 'barcoin', 'amount': 123123123123},
				]}
		else:
			raise ValueError(f'‘{req_str}’: malformed query path')

		return json.dumps(data).encode()
