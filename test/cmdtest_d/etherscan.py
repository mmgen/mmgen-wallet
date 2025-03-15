#!/usr/bin/env python3

from http.server import HTTPServer, CGIHTTPRequestHandler

from mmgen.util import msg
from mmgen.util2 import port_in_use

class handler(CGIHTTPRequestHandler):
	header = b'HTTP/1.1 200 OK\nContent-type: text/html\n\n'

	def do_response(self, target):
		with open(f'test/ref/ethereum/etherscan-{target}.html') as fh:
			text = fh.read()
		self.wfile.write(self.header + text.encode())

	def do_GET(self):
		return self.do_response('form')

	def do_POST(self):
		return self.do_response('result')

def run_etherscan_server(server_class=HTTPServer, handler_class=handler):

	if port_in_use(28800):
		msg('Port 28800 in use. Assuming etherscan server is running')
		return True

	msg('Etherscan server listening on port 28800')
	server_address = ('localhost', 28800)
	httpd = server_class(server_address, handler_class)
	httpd.serve_forever()
	msg('Etherscan server exiting')
