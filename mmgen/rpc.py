#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
rpc.py:  Cryptocoin RPC library for the MMGen suite
"""

import base64,json,asyncio,importlib
from decimal import Decimal
from collections import namedtuple

from .common import *
from .objmethods import Hilite,InitErrors

auth_data = namedtuple('rpc_auth_data',['user','passwd'])

rpc_credentials_msg = '\n'+fmt("""
	Error: no {proto_name} RPC authentication method found

	RPC credentials must be supplied using one of the following methods:

	A) If daemon is local and running as same user as you:

	   - no credentials required, or matching rpcuser/rpcpassword and
	     rpc_user/rpc_password values in {cf_name}.conf and mmgen.cfg

	B) If daemon is running remotely or as different user:

	   - matching credentials in {cf_name}.conf and mmgen.cfg as described above

	The --rpc-user/--rpc-password options may be supplied on the MMGen command line.
	They override the corresponding values in mmgen.cfg. Set them to an empty string
	to use cookie authentication with a local server when the options are set
	in mmgen.cfg.

	For better security, rpcauth should be used in {cf_name}.conf instead of
	rpcuser/rpcpassword.

""",strip_char='\t')

def dmsg_rpc(fs,data=None,is_json=False):
	if g.debug_rpc:
		msg(
			fs if data == None else
			fs.format(pp_fmt(json.loads(data) if is_json else data))
		)

class IPPort(str,Hilite,InitErrors):
	color = 'yellow'
	width = 0
	trunc_ok = False
	min_len = 9  # 0.0.0.0:0
	max_len = 21 # 255.255.255.255:65535
	def __new__(cls,s):
		if type(s) == cls:
			return s
		try:
			m = re.fullmatch(r'{q}\.{q}\.{q}\.{q}:(\d{{1,10}})'.format(q=r'([0-9]{1,3})'),s)
			assert m is not None, f'{s!r}: invalid IP:HOST specifier'
			for e in m.groups():
				if len(e) != 1 and e[0] == '0':
					raise ValueError(f'{e}: leading zeroes not permitted in dotted decimal element or port number')
			res = [int(e) for e in m.groups()]
			for e in res[:4]:
				assert e <= 255, f'{e}: dotted decimal element > 255'
			assert res[4] <= 65535, f'{res[4]}: port number > 65535'
			me = str.__new__(cls,s)
			me.ip = '{}.{}.{}.{}'.format(*res)
			me.ip_num = sum( res[i] * ( 2 ** (-(i-3)*8) ) for i in range(4) )
			me.port = res[4]
			return me
		except Exception as e:
			return cls.init_fail(e,s)

class json_encoder(json.JSONEncoder):
	def default(self,obj):
		if isinstance(obj,Decimal):
			return str(obj)
		else:
			return json.JSONEncoder.default(self,obj)

class RPCBackends:

	class base:

		def __init__(self,caller):
			self.host           = caller.host
			self.port           = caller.port
			self.proxy          = caller.proxy
			self.url            = caller.url
			self.timeout        = caller.timeout
			self.http_hdrs      = caller.http_hdrs
			self.make_host_path = caller.make_host_path
			self.name           = type(self).__name__

	class aiohttp(base):
		"""
		Contrary to the requests library, aiohttp won’t read environment variables by
		default.  But you can do so by passing trust_env=True into aiohttp.ClientSession
		constructor to honor HTTP_PROXY, HTTPS_PROXY, WS_PROXY or WSS_PROXY environment
		variables (all are case insensitive).
		"""
		def __init__(self,caller):
			super().__init__(caller)
			self.session = g.session
			if caller.auth_type == 'basic':
				import aiohttp
				self.auth = aiohttp.BasicAuth(*caller.auth,encoding='UTF-8')
			else:
				self.auth = None

		async def run(self,payload,timeout,wallet):
			dmsg_rpc('\n    RPC PAYLOAD data (aiohttp) ==>\n{}\n',payload)
			async with self.session.post(
				url     = self.url + self.make_host_path(wallet),
				auth    = self.auth,
				data    = json.dumps(payload,cls=json_encoder),
				timeout = timeout or self.timeout,
			) as res:
				return (await res.text(),res.status)

	class requests(base):

		def __del__(self):
			self.session.close()

		def __init__(self,caller):
			super().__init__(caller)
			import requests,urllib3
			urllib3.disable_warnings()
			self.session = requests.Session()
			self.session.trust_env = False # ignore *_PROXY environment vars
			self.session.headers = caller.http_hdrs
			if caller.auth_type:
				auth = 'HTTP' + caller.auth_type.capitalize() + 'Auth'
				self.session.auth = getattr(requests.auth,auth)(*caller.auth)
			if self.proxy:
				self.session.proxies.update({
					'http':  f'socks5h://{self.proxy}',
					'https': f'socks5h://{self.proxy}'
				})

		async def run(self,payload,timeout,wallet):
			dmsg_rpc('\n    RPC PAYLOAD data (requests) ==>\n{}\n',payload)
			res = self.session.post(
				url     = self.url + self.make_host_path(wallet),
				data    = json.dumps(payload,cls=json_encoder),
				timeout = timeout or self.timeout,
				verify  = False )
			return (res.content,res.status_code)

	class httplib(base):
		"""
		Ignores *_PROXY environment vars
		"""
		def __del__(self):
			self.session.close()

		def __init__(self,caller):
			super().__init__(caller)
			import http.client
			self.session = http.client.HTTPConnection(caller.host,caller.port,caller.timeout)
			if caller.auth_type == 'basic':
				auth_str = f'{caller.auth.user}:{caller.auth.passwd}'
				auth_str_b64 = 'Basic ' + base64.b64encode(auth_str.encode()).decode()
				self.http_hdrs.update({ 'Host': self.host, 'Authorization': auth_str_b64 })
				dmsg_rpc('    RPC AUTHORIZATION data ==> raw: [{}]\n{:>31}enc: [{}]\n'.format(
					auth_str,
					'',
					auth_str_b64 ))

		async def run(self,payload,timeout,wallet):
			dmsg_rpc('\n    RPC PAYLOAD data (httplib) ==>\n{}\n',payload)

			if timeout:
				import http.client
				s = http.client.HTTPConnection(self.host,self.port,timeout)
			else:
				s = self.session

			try:
				s.request(
					method  = 'POST',
					url     = self.make_host_path(wallet),
					body    = json.dumps(payload,cls=json_encoder),
					headers = self.http_hdrs )
				r = s.getresponse() # => http.client.HTTPResponse instance
			except Exception as e:
				die( 'RPCFailure', str(e) )

			if timeout:
				ret = ( r.read(), r.status )
				s.close()
				return ret
			else:
				return ( r.read(), r.status )

	class curl(base):

		def __init__(self,caller):

			def gen_opts():
				for k,v in caller.http_hdrs.items():
					for s in ('--header',f'{k}: {v}'):
						yield s
				if caller.auth_type:
					"""
					Authentication with curl is insecure, as it exposes the user's credentials
					via the command line.  Use for testing only.
					"""
					for s in ('--user',f'{caller.auth.user}:{caller.auth.passwd}'):
						yield s
				if caller.auth_type == 'digest':
					yield '--digest'
				if caller.network_proto == 'https' and caller.verify_server == False:
					yield '--insecure'

			super().__init__(caller)
			self.exec_opts = list(gen_opts()) + ['--silent']
			self.arg_max = 8192 # set way below system ARG_MAX, just to be safe

		async def run(self,payload,timeout,wallet):
			data = json.dumps(payload,cls=json_encoder)
			if len(data) > self.arg_max:
				return self.httplib(payload,timeout=timeout)
			dmsg_rpc('\n    RPC PAYLOAD data (curl) ==>\n{}\n',payload)
			exec_cmd = [
				'curl',
				'--proxy', f'socks5h://{self.proxy}' if self.proxy else '',
				'--connect-timeout', str(timeout or self.timeout),
				'--write-out', '%{http_code}',
				'--data-binary', data
				] + self.exec_opts + [self.url + self.make_host_path(wallet)]

			dmsg_rpc('    RPC curl exec data ==>\n{}\n',exec_cmd)

			from subprocess import run,PIPE
			from .color import set_vt100
			res = run(exec_cmd,stdout=PIPE,check=True).stdout.decode()
			set_vt100()
			# res = run(exec_cmd,stdout=PIPE,check=True,text='UTF-8').stdout # Python 3.7+
			return (res[:-3],int(res[-3:]))

class RPCClient(MMGenObject):

	json_rpc = True
	auth_type = None
	has_auth_cookie = False
	network_proto = 'http'
	host_path = ''
	proxy = None

	def __init__(self,host,port,test_connection=True):

		# aiohttp workaround, and may speed up RPC performance overall on some systems:
		if g.platform == 'win' and host == 'localhost':
			host = '127.0.0.1'

		dmsg_rpc(f'=== {type(self).__name__}.__init__() debug ===')
		dmsg_rpc(f'    cls [{type(self).__name__}] host [{host}] port [{port}]\n')

		if test_connection:
			import socket
			try:
				socket.create_connection((host,port),timeout=1).close()
			except:
				die( 'SocketError', f'Unable to connect to {host}:{port}' )

		self.http_hdrs = { 'Content-Type': 'application/json' }
		self.url = f'{self.network_proto}://{host}:{port}{self.host_path}'
		self.host = host
		self.port = port
		self.timeout = g.http_timeout
		self.auth = None

	@staticmethod
	def make_host_path(foo):
		return ''

	def set_backend(self,backend=None):
		bn = backend or opt.rpc_backend
		if bn == 'auto':
			self.backend = {'linux':RPCBackends.httplib,'win':RPCBackends.requests}[g.platform](self)
		else:
			self.backend = getattr(RPCBackends,bn)(self)

	def set_auth(self):
		"""
		MMGen's credentials override coin daemon's
		"""
		if g.rpc_user:
			user,passwd = (g.rpc_user,g.rpc_password)
		else:
			user,passwd = self.get_daemon_cfg_options(('rpcuser','rpcpassword')).values()

		if not (user and passwd):
			user,passwd = (self.daemon.rpc_user,self.daemon.rpc_password)

		if user and passwd:
			self.auth = auth_data(user,passwd)
			return

		if self.has_auth_cookie:
			cookie = self.get_daemon_auth_cookie()
			if cookie:
				self.auth = auth_data(*cookie.split(':'))
				return

		die(1,rpc_credentials_msg.format(
			proto_name = self.proto.name,
			cf_name = (self.proto.is_fork_of or self.proto.name).lower(),
		))

	# Call family of methods - direct-to-daemon RPC call:
	# positional params are passed to the daemon, 'timeout' and 'wallet' kwargs to the backend

	async def call(self,method,*params,timeout=None,wallet=None):
		"""
		default call: call with param list unrolled, exactly as with cli
		"""
		return await self.process_http_resp(self.backend.run(
			payload = {'id': 1, 'jsonrpc': '2.0', 'method': method, 'params': params },
			timeout = timeout,
			wallet  = wallet
		))

	async def batch_call(self,method,param_list,timeout=None,wallet=None):
		"""
		Make a single call with a list of tuples as first argument
		For RPC calls that return a list of results
		"""
		return await self.process_http_resp(self.backend.run(
			payload = [{
				'id': n,
				'jsonrpc': '2.0',
				'method': method,
				'params': params } for n,params in enumerate(param_list,1) ],
			timeout = timeout,
			wallet  = wallet
		),batch=True)

	async def gathered_call(self,method,args_list,timeout=None,wallet=None):
		"""
		Perform multiple RPC calls, returning results in a list
		Can be called two ways:
		  1) method = methodname, args_list = [args_tuple1, args_tuple2,...]
		  2) method = None, args_list = [(methodname1,args_tuple1), (methodname2,args_tuple2), ...]
		"""
		cmd_list = args_list if method == None else tuple(zip([method] * len(args_list), args_list))

		cur_pos = 0
		chunk_size = 1024
		ret = []

		while cur_pos < len(cmd_list):
			tasks = [self.process_http_resp(self.backend.run(
						payload = {'id': n, 'jsonrpc': '2.0', 'method': method, 'params': params },
						timeout = timeout,
						wallet  = wallet
					)) for n,(method,params)  in enumerate(cmd_list[cur_pos:chunk_size+cur_pos],1)]
			ret.extend(await asyncio.gather(*tasks))
			cur_pos += chunk_size

		return ret

	# Icall family of methods - indirect RPC call using CallSigs mechanism:
	# - 'timeout' and 'wallet' kwargs are passed to corresponding Call method
	# - remaining kwargs are passed to CallSigs method
	# - CallSigs method returns method and positional params for Call method

	def icall(self,method,**kwargs):
		timeout = kwargs.pop('timeout',None)
		wallet = kwargs.pop('wallet',None)
		return self.call(
			*getattr(self.call_sigs,method)(**kwargs),
			timeout = timeout,
			wallet = wallet )

	def gathered_icall(self,method,args_list,timeout=None,wallet=None):
		return self.gathered_call(
			method,
			[getattr(self.call_sigs,method)(*a)[1:] for a in args_list],
			timeout = timeout,
			wallet = wallet )

	async def process_http_resp(self,coro,batch=False):
		text,status = await coro
		if status == 200:
			dmsg_rpc('    RPC RESPONSE data ==>\n{}\n',text,is_json=True)
			if batch:
				return [r['result'] for r in json.loads(text,parse_float=Decimal)]
			else:
				try:
					if self.json_rpc:
						return json.loads(text,parse_float=Decimal)['result']
					else:
						return json.loads(text,parse_float=Decimal)
				except:
					t = json.loads(text)
					try:
						m = t['error']['message']
					except:
						try: m = t['error']
						except: m = t
					die( 'RPCFailure', m )
		else:
			import http
			m,s = ( '', http.HTTPStatus(status) )
			if text:
				try:
					m = json.loads(text)['error']['message']
				except:
					try: m = text.decode()
					except: m = text
			die( 'RPCFailure', f'{s.value} {s.name}: {m}' )

	async def stop_daemon(self,quiet=False,silent=False):
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

	async def restart_daemon(self,quiet=False,silent=False):
		await self.stop_daemon(quiet=quiet,silent=silent)
		return self.daemon.start(silent=silent)

def handle_unsupported_daemon_version(rpc,name,warn_only):

	class daemon_version_warning(oneshot_warning):
		color = 'yellow'
		message = 'ignoring unsupported {} daemon version at user request'

	if warn_only:
		daemon_version_warning(div=name,fmt_args=[rpc.daemon.coind_name])
	else:
		name = rpc.daemon.coind_name
		die(2,'\n'+fmt(f"""
			The running {name} daemon has version {rpc.daemon_version_str}.
			This version of MMGen is tested only on {name} v{rpc.daemon.coind_version_str} and below.

			To avoid this error, downgrade your daemon to a supported version.

			Alternatively, you may invoke the command with the --ignore-daemon-version
			option, in which case you proceed at your own risk.
			""",indent='    '))

async def rpc_init(proto,backend=None,daemon=None,ignore_daemon_version=False):

	if not 'rpc' in proto.mmcaps:
		die(1,f'Coin daemon operations not supported for {proto.name} protocol!')


	cls = getattr(
		importlib.import_module(f'mmgen.base_proto.{proto.base_proto.lower()}.rpc'),
			proto.base_proto + 'RPCClient' )

	from .daemon import CoinDaemon
	rpc = await cls(
		proto   = proto,
		daemon  = daemon or CoinDaemon(proto=proto,test_suite=g.test_suite),
		backend = backend or opt.rpc_backend )

	if rpc.daemon_version > rpc.daemon.coind_version:
		handle_unsupported_daemon_version(
			rpc,
			proto.name,
			ignore_daemon_version or proto.ignore_daemon_version or g.ignore_daemon_version )

	if rpc.chain not in proto.chain_names:
		die( 'RPCChainMismatch', '\n' + fmt(f"""
			Protocol:           {proto.cls_name}
			Valid chain names:  {fmt_list(proto.chain_names,fmt='bare')}
			RPC client chain:   {rpc.chain}
			""",indent='  ').rstrip() )

	return rpc
