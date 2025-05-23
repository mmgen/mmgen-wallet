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
rpc.backends.httplib: httplib RPC backend for the MMGen Project
"""

import json, base64

from ...util import die

from ..util import dmsg_rpc, dmsg_rpc_backend, json_encoder

from .base import base

class httplib(base):
	"""
	Ignores *_PROXY environment vars
	"""
	def __del__(self):
		self.session.close()

	def __init__(self, caller):
		super().__init__(caller)
		import http.client
		self.session = http.client.HTTPConnection(caller.host, caller.port, caller.timeout)
		if caller.auth_type == 'basic':
			auth_str = f'{caller.auth.user}:{caller.auth.passwd}'
			auth_str_b64 = 'Basic ' + base64.b64encode(auth_str.encode()).decode()
			self.http_hdrs.update({'Host': self.host, 'Authorization': auth_str_b64})
			dmsg_rpc(f'    RPC AUTHORIZATION data ==> raw: [{auth_str}]\n{"":>31}enc: [{auth_str_b64}]\n')

	async def run(self, payload, timeout, host_path):
		dmsg_rpc_backend(self.host_url, host_path, payload)

		if timeout:
			import http.client
			s = http.client.HTTPConnection(self.host, self.port, timeout)
		else:
			s = self.session

		try:
			s.request(
				method  = 'POST',
				url     = host_path,
				body    = json.dumps(payload, cls=json_encoder),
				headers = self.http_hdrs)
			r = s.getresponse() # => http.client.HTTPResponse instance
		except Exception as e:
			die('RPCFailure', str(e))

		if timeout:
			ret = (r.read(), r.status)
			s.close()
			return ret
		else:
			return (r.read(), r.status)
