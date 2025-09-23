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

from mmgen.util2 import get_keccak

from . import HTTPD

class EtherscanServer(HTTPD):
	name = 'etherscan server'
	port = 28800
	content_type = 'text/html'

	def make_response_body(self, method, environ):
		match method:
			case 'GET':
				target = 'form'
			case 'POST':
				target = 'result'
				length = int(environ.get('CONTENT_LENGTH', '0'))
				qs = environ['wsgi.input'].read(length).decode()
				tx = [s for s in qs.split('&') if 'RawTx=' in s][0].split('=')[1]
				keccak_256 = get_keccak()
				txid = '0x' + keccak_256(bytes.fromhex(tx[2:])).hexdigest()

		with open(f'test/ref/ethereum/etherscan-{target}.html') as fh:
			text = fh.read()

		return (text if method == 'GET' else text.format(txid=txid)).encode()
