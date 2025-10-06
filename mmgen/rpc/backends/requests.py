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
rpc.backends.requests: requests RPC backend for the MMGen Project
"""

import json

from ..util import dmsg_rpc_backend, json_encoder

from .base import base

class requests(base):

	def __del__(self):
		self.session.close()

	def __init__(self, caller):
		super().__init__(caller)
		import requests, urllib3
		urllib3.disable_warnings()
		self.session = requests.Session()
		self.session.trust_env = False # ignore *_PROXY environment vars
		self.session.headers = caller.http_hdrs
		if caller.auth_type:
			auth = 'HTTP' + caller.auth_type.capitalize() + 'Auth'
			self.session.auth = getattr(requests.auth, auth)(*caller.auth)
		if self.proxy: # used only by XMR for now: requires pysocks package
			self.session.proxies.update({
				'http':  f'socks5h://{self.proxy}',
				'https': f'socks5h://{self.proxy}'})

	async def run(self, *args, **kwargs):
		return self.run_noasync(*args, **kwargs)

	def run_noasync(self, payload, timeout, host_path):
		dmsg_rpc_backend(self.host_url, host_path, payload)
		res = self.session.post(
			url     = self.host_url + host_path,
			data    = json.dumps(payload, cls=json_encoder),
			timeout = timeout or self.timeout,
			verify  = False)
		return (res.content, res.status_code)
