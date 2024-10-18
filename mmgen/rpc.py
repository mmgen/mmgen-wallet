#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
rpc: Cryptocoin RPC library for the MMGen suite
"""

import sys, re, base64, json, asyncio, importlib
from decimal import Decimal
from collections import namedtuple

from .util import msg, ymsg, die, fmt, fmt_list, pp_fmt, oneshot_warning
from .base_obj import AsyncInit
from .obj import NonNegativeInt
from .objmethods import HiliteStr, InitErrors, MMGenObject

auth_data = namedtuple('rpc_auth_data', ['user', 'passwd'])

def dmsg_rpc(fs, data=None, is_json=False):
	msg(
		fs if data is None else
		fs.format(pp_fmt(json.loads(data) if is_json else data))
	)

def dmsg_rpc_backend(host_url, host_path, payload):
	msg(
		f'\n    RPC URL: {host_url}{host_path}' +
		'\n    RPC PAYLOAD data (httplib) ==>' +
		f'\n{pp_fmt(payload)}\n')

def noop(*args, **kwargs):
	pass

class IPPort(HiliteStr, InitErrors):
	color = 'yellow'
	width = 0
	trunc_ok = False
	min_len = 9  # 0.0.0.0:0
	max_len = 21 # 255.255.255.255:65535
	def __new__(cls, s):
		if isinstance(s, cls):
			return s
		try:
			m = re.fullmatch(r'{q}\.{q}\.{q}\.{q}:(\d{{1,10}})'.format(q=r'([0-9]{1,3})'), s)
			assert m is not None, f'{s!r}: invalid IP:HOST specifier'
			for e in m.groups():
				if len(e) != 1 and e[0] == '0':
					raise ValueError(f'{e}: leading zeroes not permitted in dotted decimal element or port number')
			res = [int(e) for e in m.groups()]
			for e in res[:4]:
				assert e <= 255, f'{e}: dotted decimal element > 255'
			assert res[4] <= 65535, f'{res[4]}: port number > 65535'
			me = str.__new__(cls, s)
			me.ip = '{}.{}.{}.{}'.format(*res)
			me.ip_num = sum(res[i] * (2 ** (-(i-3)*8)) for i in range(4))
			me.port = res[4]
			return me
		except Exception as e:
			return cls.init_fail(e, s)

class json_encoder(json.JSONEncoder):
	def default(self, o):
		if isinstance(o, Decimal):
			return str(o)
		else:
			return json.JSONEncoder.default(self, o)

class RPCBackends:

	class base:

		def __init__(self, caller):
			self.cfg            = caller.cfg
			self.host           = caller.host
			self.port           = caller.port
			self.proxy          = caller.proxy
			self.host_url       = caller.host_url
			self.timeout        = caller.timeout
			self.http_hdrs      = caller.http_hdrs
			self.name           = type(self).__name__
			self.caller         = caller

	class aiohttp(base, metaclass=AsyncInit):
		"""
		Contrary to the requests library, aiohttp won’t read environment variables by
		default.  But you can do so by passing trust_env=True into aiohttp.ClientSession
		constructor to honor HTTP_PROXY, HTTPS_PROXY, WS_PROXY or WSS_PROXY environment
		variables (all are case insensitive).
		"""

		def __del__(self):
			self.connector.close()
			self.session.detach()
			del self.session

		async def __init__(self, caller):
			super().__init__(caller)
			import aiohttp
			self.connector = aiohttp.TCPConnector(limit_per_host=self.cfg.aiohttp_rpc_queue_len)
			self.session = aiohttp.ClientSession(
				headers = {'Content-Type': 'application/json'},
				connector = self.connector,
			)
			if caller.auth_type == 'basic':
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
					'https': f'socks5h://{self.proxy}'
				})

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
				ymsg('Warning: Curl data payload length exceeded - falling back on httplib')
				return RPCBackends.httplib(self.caller).run(payload, timeout, host_path)
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
			from .color import set_vt100
			res = run(exec_cmd, stdout=PIPE, check=True, text=True).stdout
			set_vt100()
			return (res[:-3], int(res[-3:]))

class RPCClient(MMGenObject):

	auth_type = None
	has_auth_cookie = False
	network_proto = 'http'
	proxy = None

	def __init__(self, cfg, host, port, test_connection=True):

		self.cfg = cfg
		self.name = type(self).__name__

		# aiohttp workaround, and may speed up RPC performance overall on some systems:
		if sys.platform == 'win32' and host == 'localhost':
			host = '127.0.0.1'

		global dmsg_rpc, dmsg_rpc_backend
		if not self.cfg.debug_rpc:
			dmsg_rpc = dmsg_rpc_backend = noop

		dmsg_rpc(f'=== {self.name}.__init__() debug ===')
		dmsg_rpc(f'    cls [{self.name}] host [{host}] port [{port}]\n')

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
		self.timeout = self.cfg.http_timeout
		self.auth = None

	def _get_backend(self, backend):
		backend_id = backend or self.cfg.rpc_backend
		if backend_id == 'auto':
			return {
				'linux': RPCBackends.httplib,
				'darwin': RPCBackends.httplib,
				'win32': RPCBackends.requests
			}[sys.platform](self)
		else:
			return getattr(RPCBackends, backend_id)(self)

	def set_backend(self, backend=None):
		self.backend = self._get_backend(backend)

	async def set_backend_async(self, backend=None):
		ret = self._get_backend(backend)
		self.backend = (await ret) if type(ret).__name__ == 'coroutine' else ret

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
			host_path = self.make_host_path(wallet)
		))

	async def batch_call(self, method, param_list, timeout=None, wallet=None):
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

	async def gathered_call(self, method, args_list, timeout=None, wallet=None):
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

	def gathered_icall(self, method, args_list, timeout=None, wallet=None):
		return self.gathered_call(
			method,
			[getattr(self.call_sigs, method)(*a)[1:] for a in args_list],
			timeout = timeout,
			wallet = wallet)

	def process_http_resp(self, run_ret, batch=False, json_rpc=True):

		def float_parser(n):
			return n

		text, status = run_ret

		if status == 200:
			dmsg_rpc('    RPC RESPONSE data ==>\n{}\n', text, is_json=True)
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

	async def stop_daemon(self, quiet=False, silent=False):
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

	def start_daemon(self, silent=False):
		return self.daemon.start(silent=silent)

	async def restart_daemon(self, quiet=False, silent=False):
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

async def rpc_init(
		cfg,
		proto                 = None,
		backend               = None,
		daemon                = None,
		ignore_daemon_version = False,
		ignore_wallet         = False):

	proto = proto or cfg._proto

	if not 'rpc_init' in proto.mmcaps:
		die(1, f'rpc_init() not supported for {proto.name} protocol!')

	cls = getattr(
		importlib.import_module(f'mmgen.proto.{proto.base_proto_coin.lower()}.rpc'),
			proto.base_proto + 'RPCClient')

	from .daemon import CoinDaemon
	rpc = await cls(
		cfg           = cfg,
		proto         = proto,
		daemon        = daemon or CoinDaemon(cfg, proto=proto, test_suite=cfg.test_suite),
		backend       = backend or cfg.rpc_backend,
		ignore_wallet = ignore_wallet)

	if rpc.daemon_version > rpc.daemon.coind_version:
		rpc.handle_unsupported_daemon_version(
			proto.name,
			ignore_daemon_version or proto.ignore_daemon_version or cfg.ignore_daemon_version)

	if rpc.chain not in proto.chain_names:
		die('RPCChainMismatch', '\n' + fmt(f"""
			Protocol:           {proto.cls_name}
			Valid chain names:  {fmt_list(proto.chain_names, fmt='bare')}
			RPC client chain:   {rpc.chain}
			""", indent='  ').rstrip())

	rpc.blockcount = NonNegativeInt(rpc.blockcount)

	return rpc
