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
rpc.backends.curl: curl RPC backend for the MMGen Project
"""

import json

from ...util import ymsg

from ..util import dmsg_rpc, dmsg_rpc_backend, json_encoder

from .base import base

class curl(base):

	def __init__(self, caller):

		def gen_opts():
			for k, v in caller.http_hdrs.items():
				yield from ('--header', f'{k}: {v}')
			if caller.auth_type:
				# Authentication with curl is insecure, as it exposes the user's credentials
				# via the command line.  Use for testing only.
				yield from ('--user', f'{caller.auth.user}:{caller.auth.passwd}')
			if caller.auth_type == 'digest':
				yield '--digest'
			if caller.network_proto == 'https' and caller.verify_server is False:
				yield '--insecure'

		super().__init__(caller)
		self.exec_opts = list(gen_opts()) + ['--silent']
		self.arg_max = 8192 # set way below system ARG_MAX, just to be safe

	async def run(self, payload, timeout, host_path):
		data = json.dumps(payload, cls=json_encoder)
		if len(data) > self.arg_max:
			from .httplib import httplib
			ymsg('Warning: Curl data payload length exceeded - falling back on httplib')
			return httplib(self.caller).run(payload, timeout, host_path)
		dmsg_rpc_backend(self.host_url, host_path, payload)
		exec_cmd = [
			'curl',
			'--proxy', f'socks5h://{self.proxy}' if self.proxy else '',
			'--connect-timeout', str(timeout or self.timeout),
			'--write-out', '%{http_code}',
			'--data-binary', data
			] + self.exec_opts + [self.host_url + host_path]

		dmsg_rpc('    RPC curl exec data ==>\n{}\n', exec_cmd)

		from subprocess import run, PIPE
		from ...color import set_vt100
		res = run(exec_cmd, stdout=PIPE, check=True, text=True).stdout
		set_vt100()
		return (res[:-3], int(res[-3:]))
