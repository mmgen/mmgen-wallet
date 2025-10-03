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
rpc.local: local RPC client class for the MMGen Project
"""

import sys, json, asyncio, importlib

from ..util import msg, die, fmt, oneshot_warning, isAsync

from . import util

class RPCClient:

	is_remote = False
	auth_type = None
	has_auth_cookie = False
	network_proto = 'http'
	proxy = None

	def __init__(self, cfg, host, port, *, test_connection=True):

		self.cfg = cfg
		self.name = type(self).__name__

		# aiohttp workaround, and may speed up RPC performance overall on some systems:
		if sys.platform == 'win32' and host == 'localhost':
			host = '127.0.0.1'

		if not self.cfg.debug_rpc:
			util.dmsg_rpc = util.dmsg_rpc_backend = util.noop

		util.dmsg_rpc(f'=== {self.name}.__init__() debug ===')
		util.dmsg_rpc(f'    cls [{self.name}] host [{host}] port [{port}]\n')

		if test_connection:
			import socket
			try:
				socket.create_connection((host, port), timeout=1).close()
			except:
				die('SocketError', f'Unable to connect to {host}:{port}')

		self.http_hdrs = {'Content-Type': 'application/json'}
		self.host_url = f'{self.network_proto}://{host}:{port}'
		self.host = host
		self.port = port
		self.timeout = self.cfg.http_timeout or 60
		self.auth = None

	def _get_backend_cls(self, backend):
		dfl_backends = {
			'linux': 'httplib',
			'darwin': 'httplib',
			'win32': 'requests'}
		def get_cls(backend_id):
			return getattr(importlib.import_module(f'mmgen.rpc.backends.{backend_id}'), backend_id)
		backend_id = backend or self.cfg.rpc_backend
		return get_cls(dfl_backends[sys.platform] if backend_id == 'auto' else backend_id)

	def set_backend(self, backend=None):
		self.backend = self._get_backend_cls(backend)(self)

	async def set_backend_async(self, backend=None):
		cls = self._get_backend_cls(backend)
		self.backend = await cls(self) if isAsync(cls.__init__) else cls(self)

	# Call family of methods - direct-to-daemon RPC call:
	# - positional params are passed to the daemon, 'timeout' and 'wallet' kwargs to the backend
	# - 'wallet' kwarg is used only by regtest

	async def call(self, method, *params, timeout=None, wallet=None):
		"""
		default call: call with param list unrolled, exactly as with cli
		"""
		return self.process_http_resp(await self.backend.run(
			payload = {'id': 1, 'jsonrpc': '2.0', 'method': method, 'params': params},
			timeout = timeout,
			host_path = self.make_host_path(wallet)))

	async def batch_call(self, method, param_list, *, timeout=None, wallet=None):
		"""
		Make a single call with a list of tuples as first argument
		For RPC calls that return a list of results
		"""
		return self.process_http_resp(await self.backend.run(
			payload = [{
				'id': n,
				'jsonrpc': '2.0',
				'method': method,
				'params': params} for n, params in enumerate(param_list, 1)],
			timeout = timeout,
			host_path = self.make_host_path(wallet)
		), batch=True)

	async def gathered_call(self, method, args_list, *, timeout=None, wallet=None):
		"""
		Perform multiple RPC calls, returning results in a list
		Can be called two ways:
		  1) method = methodname, args_list = [args_tuple1, args_tuple2,...]
		  2) method = None, args_list = [(methodname1, args_tuple1), (methodname2, args_tuple2), ...]
		"""
		cmd_list = args_list if method is None else tuple(zip([method] * len(args_list), args_list))

		cur_pos = 0
		chunk_size = 1024
		ret = []

		while cur_pos < len(cmd_list):
			tasks = [self.backend.run(
						payload = {'id': n, 'jsonrpc': '2.0', 'method': method, 'params': params},
						timeout = timeout,
						host_path = self.make_host_path(wallet)
					) for n, (method, params)  in enumerate(cmd_list[cur_pos:chunk_size+cur_pos], 1)]
			ret.extend(await asyncio.gather(*tasks))
			cur_pos += chunk_size

		return [self.process_http_resp(r) for r in ret]

	# Icall family of methods - indirect RPC call using CallSigs mechanism:
	# - 'timeout' and 'wallet' kwargs are passed to corresponding Call method
	# - remaining kwargs are passed to CallSigs method
	# - CallSigs method returns method and positional params for Call method

	def icall(self, method, **kwargs):
		timeout = kwargs.pop('timeout', None)
		wallet = kwargs.pop('wallet', None)
		return self.call(
			*getattr(self.call_sigs, method)(**kwargs),
			timeout = timeout,
			wallet = wallet)

	def gathered_icall(self, method, args_list, *, timeout=None, wallet=None):
		return self.gathered_call(
			method,
			[getattr(self.call_sigs, method)(*a)[1:] for a in args_list],
			timeout = timeout,
			wallet = wallet)

	def process_http_resp(self, run_ret, *, batch=False, json_rpc=True):

		def float_parser(n):
			return n

		text, status = run_ret

		if status == 200:
			util.dmsg_rpc('    RPC RESPONSE data ==>\n{}\n', text, is_json=True)
			m = None
			if batch:
				return [r['result'] for r in json.loads(text, parse_float=float_parser)]
			else:
				try:
					if json_rpc:
						ret = json.loads(text, parse_float=float_parser)['result']
						if isinstance(ret, list) and ret and type(ret[0]) == dict and 'success' in ret[0]:
							for res in ret:
								if not res['success']:
									m = str(res['error'])
									assert False
						return ret
					else:
						return json.loads(text, parse_float=float_parser)
				except:
					if not m:
						t = json.loads(text)
						try:
							m = t['error']['message']
						except:
							try:
								m = t['error']
							except:
								m = t
					die('RPCFailure', m)
		else:
			import http
			m, s = ('', http.HTTPStatus(status))
			if text:
				try:
					m = json.loads(text)['error']['message']
				except:
					try:
						m = text.decode()
					except:
						m = text
			die('RPCFailure', f'{s.value} {s.name}: {m}')

	async def stop_daemon(self, *, quiet=False, silent=False):
		if self.daemon.state == 'ready':
			if not (quiet or silent):
				msg(f'Stopping {self.daemon.desc} on port {self.daemon.bind_port}')
			ret = await self.do_stop_daemon(silent=silent)
			if self.daemon.wait:
				self.daemon.wait_for_state('stopped')
			return ret
		else:
			if not (quiet or silent):
				msg(f'{self.daemon.desc} on port {self.daemon.bind_port} not running')
			return True

	def start_daemon(self, *, silent=False):
		return self.daemon.start(silent=silent)

	async def restart_daemon(self, *, quiet=False, silent=False):
		await self.stop_daemon(quiet=quiet, silent=silent)
		return self.daemon.start(silent=silent)

	def handle_unsupported_daemon_version(self, name, warn_only):

		class daemon_version_warning(oneshot_warning):
			color = 'yellow'
			message = 'ignoring unsupported {} daemon version at user request'

		if warn_only:
			daemon_version_warning(div=name, fmt_args=[self.daemon.coind_name])
		else:
			name = self.daemon.coind_name
			die(2, '\n'+fmt(f"""
				The running {name} daemon has version {self.daemon_version_str}.
				This version of MMGen is tested only on {name} v{self.daemon.coind_version_str} and below.

				To avoid this error, downgrade your daemon to a supported version.

				Alternatively, you may invoke the command with the --ignore-daemon-version
				option, in which case you proceed at your own risk.
				""", indent='    '))
