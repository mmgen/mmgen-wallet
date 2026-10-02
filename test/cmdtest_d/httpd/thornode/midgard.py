#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.cmdtest_d.httpd.thornode.midgard: Thornode Midgard HTTP server
"""

import re, json
from wsgiref.util import request_uri

from . import ThornodeServer

actions_info = {
	'actions': [{
			'date': '987654321',
			'height': '1234',
		},
	],
	'count': '1',
	'meta': {
		'nextPageToken': '123456789',
		'prevPageToken': '123456788'}}

health_info = {
	'database': True,
	'inSync': True,
	'scannerHeight': '987654321'}

class ThornodeMidgardServer(ThornodeServer):
	port = 19000
	name = 'thornode Midgard server'

	def make_response_body(self, method, environ):

		class responses:

			# pylint: disable=unsubscriptable-object

			def health(m):
				return health_info

			def actions(m):
				assert m[1] in ( # FIXME - for now, just check well-formedness of query string
					'?address=thor1abcdefg',
					'?txid=deadbeef',
					'?address=thor1abcdefg&txid=deadbeef')
				return actions_info

		pat_info = (
			('health',  r'/v2/health'),
			('actions', r'/v2/actions?(.*)'))

		req_str = request_uri(environ)

		for name, pat in pat_info:
			if m := re.search(pat, req_str):
				assert method == 'GET'
				res = getattr(responses, name)(m)
				return json.dumps({'result': res}).encode()

		raise ValueError(f'‘{req_str}’: malformed query path')
