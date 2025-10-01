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
rpc.backends.aiohttp: aiohttp RPC backend for the MMGen Project
"""

import json

from ...base_obj import AsyncInit

from ..util import dmsg_rpc_backend, json_encoder

from .base import base

class aiohttp(base, metaclass=AsyncInit):
	"""
	Contrary to the requests library, aiohttp won’t read environment variables by
	default.  But you can do so by passing trust_env=True into aiohttp.ClientSession
	constructor to honor HTTP_PROXY, HTTPS_PROXY, WS_PROXY or WSS_PROXY environment
	variables (all are case insensitive).
	"""

	async def __init__(self, caller):
		super().__init__(caller)
		self.session = self.cfg.aiohttp_session
		if caller.auth_type == 'basic':
			import aiohttp
			self.auth = aiohttp.BasicAuth(*caller.auth, encoding='UTF-8')
		else:
			self.auth = None

	async def run(self, payload, timeout, host_path):
		dmsg_rpc_backend(self.host_url, host_path, payload)
		async with self.session.post(
			url     = self.host_url + host_path,
			auth    = self.auth,
			data    = json.dumps(payload, cls=json_encoder),
			timeout = timeout or self.timeout,
		) as res:
			return (await res.text(), res.status)
