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
test.cmdtest_d.httpd: WSGI http server
"""

from wsgiref.simple_server import make_server, WSGIRequestHandler

from mmgen.util import msg
from mmgen.util2 import port_in_use

class SilentRequestHandler(WSGIRequestHandler):

	def log_request(self, code='-', size='-'):
		return None

class HTTPD:

	def __init__(self, cfg):
		self.cfg = cfg

	def start(self):

		if port_in_use(self.port):
			msg(f'\nPort {self.port} in use. Assuming {self.name} is running')
			return True

		self.httpd = make_server(
			'localhost',
			self.port,
			self.application,
			handler_class = SilentRequestHandler)

		import threading
		t = threading.Thread(target=self.httpd.serve_forever, name=f'{type(self).__name__} thread')
		t.daemon = True
		t.start()

	def stop(self):
		self.httpd.server_close()

	def application(self, environ, start_response):

		method = environ['REQUEST_METHOD']

		response_body = self.make_response_body(method, environ)

		status = '200 OK'
		response_headers = [
			('Content-Type', self.content_type),
			('Content-Length', str(len(response_body)))
		]

		start_response(status, response_headers)

		return [response_body]
