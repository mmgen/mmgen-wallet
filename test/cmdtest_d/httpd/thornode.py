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

import re, json
from wsgiref.util import request_uri

from . import HTTPD

class ThornodeServer(HTTPD):
	name = 'thornode server'
	port = 18800
	content_type = 'application/json'
	request_pat = r'/bank/balances/(\S+)'

	def make_response_body(self, method, environ):
		req_str = request_uri(environ)
		m = re.search(self.request_pat, req_str)
		assert m[1], f'‘{req_str}’: malformed query path'
		data = {
			'result': [
				{'denom': 'foocoin', 'amount': 321321321321},
				{'denom': 'rune',    'amount': 987654321321},
				{'denom': 'barcoin', 'amount': 123123123123},
			]}
		return json.dumps(data).encode()
