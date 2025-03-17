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
test.cmdtest_d.httpd.etherscan: Etherscan WSGI http server
"""

from . import HTTPD

class EtherscanServer(HTTPD):
	name = 'etherscan server'
	port = 28800
	content_type = 'text/html'

	def make_response_body(self, method, environ):
		targets = {'GET': 'form', 'POST': 'result'}
		with open(f'test/ref/ethereum/etherscan-{targets[method]}.html') as fh:
			return fh.read().encode()
