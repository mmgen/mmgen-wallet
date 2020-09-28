#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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

import base64,json,asyncio
from decimal import Decimal
from .common import *
from .obj import aInitMeta

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
		msg(fs if data == None else fs.format(pp_fmt(json.loads(data) if is_json else data)))

class json_encoder(json.JSONEncoder):
	def default(self,obj):
		if isinstance(obj,Decimal):
			return str(obj)
		else:
			return json.JSONEncoder.default(self,obj)

class RPCBackends:

	class aiohttp:

		def __init__(self,caller):
			self.caller = caller
			self.session = g.session
			self.url = caller.url
			self.timeout = caller.timeout
			if caller.auth_type == 'basic':
				import aiohttp
				self.auth = aiohttp.BasicAuth(*caller.auth,encoding='UTF-8')
			else:
				self.auth = None

		async def run(self,payload,timeout=None):
			dmsg_rpc('\n    RPC PAYLOAD data (aiohttp) ==>\n{}\n',payload)
			async with self.session.post(
				url     = self.url,
				auth    = self.auth,
				data    = json.dumps(payload,cls=json_encoder),
				timeout = timeout or self.timeout,
			) as res:
				return (await res.text(),res.status)

	class requests:

		def __init__(self,caller):
			self.url = caller.url
			self.timeout = caller.timeout
			import requests,urllib3
			urllib3.disable_warnings()
			self.session = requests.Session()
			self.session.headers = caller.http_hdrs
			if caller.auth_type:
				auth = 'HTTP' + caller.auth_type.capitalize() + 'Auth'
				self.session.auth = getattr(requests.auth,auth)(*caller.auth)

		async def run(self,payload,timeout=None):
			dmsg_rpc('\n    RPC PAYLOAD data (requests) ==>\n{}\n',payload)
			res = self.session.post(
				url = self.url,
				data = json.dumps(payload,cls=json_encoder),
				timeout = timeout or self.timeout,
				verify = False )
			return (res.content,res.status_code)

	class httplib:

		def __init__(self,caller):
			import http.client
			self.session = http.client.HTTPConnection(caller.host,caller.port,caller.timeout)
			self.http_hdrs = caller.http_hdrs
			self.host = caller.host
			self.port = caller.port
			if caller.auth_type == 'basic':
				auth_str = f'{caller.auth.user}:{caller.auth.passwd}'
				auth_str_b64 = 'Basic ' + base64.b64encode(auth_str.encode()).decode()
				self.http_hdrs.update({ 'Host': self.host, 'Authorization': auth_str_b64 })
				fs = '    RPC AUTHORIZATION data ==> raw: [{}]\n{:>31}enc: [{}]\n'
				dmsg_rpc(fs.format(auth_str,'',auth_str_b64))

		async def run(self,payload,timeout=None):
			dmsg_rpc('\n    RPC PAYLOAD data (httplib) ==>\n{}\n',payload)
			if timeout:
				import http.client
				s = http.client.HTTPConnection(self.host,self.port,timeout)
			else:
				s = self.session
			try:
				s.request(
					method  = 'POST',
					url     = '/',
					body    = json.dumps(payload,cls=json_encoder),
					headers = self.http_hdrs )
				r = s.getresponse() # => http.client.HTTPResponse instance
			except Exception as e:
				raise RPCFailure(str(e))
			return (r.read(),r.status)

	class curl:

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

			self.url = caller.url
			self.exec_opts = list(gen_opts()) + ['--silent']
			self.arg_max = 8192 # set way below system ARG_MAX, just to be safe
			self.timeout = caller.timeout

		async def run(self,payload,timeout=None):
			data = json.dumps(payload,cls=json_encoder)
			if len(data) > self.arg_max:
				return self.httplib(payload,timeout=timeout)
			dmsg_rpc('\n    RPC PAYLOAD data (curl) ==>\n{}\n',payload)
			exec_cmd = [
				'curl',
				'--proxy', '',
				'--connect-timeout', str(timeout or self.timeout),
				'--request', 'POST',
				'--write-out', '%{http_code}',
				'--data-binary', data
				] + self.exec_opts + [self.url]

			dmsg_rpc('    RPC curl exec data ==>\n{}\n',exec_cmd)

			from subprocess import run,PIPE
			res = run(exec_cmd,stdout=PIPE,check=True).stdout.decode()
			# res = run(exec_cmd,stdout=PIPE,check=True,text='UTF-8').stdout # Python 3.7+
			return (res[:-3],int(res[-3:]))

from collections import namedtuple
auth_data = namedtuple('rpc_auth_data',['user','passwd'])

class RPCClient(MMGenObject):

	auth_type = None
	has_auth_cookie = False
	network_proto = 'http'
	host_path = ''

	def __init__(self,host,port):

		dmsg_rpc('=== {}.__init__() debug ==='.format(type(self).__name__))
		dmsg_rpc(f'    cls [{type(self).__name__}] host [{host}] port [{port}]\n')

		import socket
		try:
			socket.create_connection((host,port),timeout=1).close()
		except:
			raise SocketError(f'Unable to connect to {host}:{port}')

		self.http_hdrs = { 'Content-Type': 'application/json' }
		self.url = f'{self.network_proto}://{host}:{port}{self.host_path}'
		self.host = host
		self.port = port
		self.timeout = g.http_timeout
		self.auth = None

	def set_backend(self,backend=None):
		bn = backend or opt.rpc_backend
		if bn == 'auto':
			self.backend = {'linux':RPCBackends.httplib,'win':RPCBackends.curl}[g.platform](self)
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

	# positional params are passed to the daemon, kwargs to the backend
	# 'timeout' is currently the only supported kwarg

	async def call(self,method,*params,**kwargs):
		"""
		default call: call with param list unrolled, exactly as with cli
		"""
		if method == g.rpc_fail_on_command:
			method = 'badcommand_' + method
		return await self.process_http_resp(self.backend.run(
			payload = {'id': 1, 'jsonrpc': '2.0', 'method': method, 'params': params },
			**kwargs
		))

	async def batch_call(self,method,param_list,**kwargs):
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
			**kwargs
		),batch=True)

	async def gathered_call(self,method,args_list,**kwargs):
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
						**kwargs
					)) for n,(method,params)  in enumerate(cmd_list[cur_pos:chunk_size+cur_pos],1)]
			ret.extend(await asyncio.gather(*tasks))
			cur_pos += chunk_size

		return ret

	async def process_http_resp(self,coro,batch=False):
		text,status = await coro
		if status == 200:
			dmsg_rpc('    RPC RESPONSE data ==>\n{}\n',text,is_json=True)
			if batch:
				return [r['result'] for r in json.loads(text,parse_float=Decimal,encoding='UTF-8')]
			else:
				try:
					return json.loads(text,parse_float=Decimal,encoding='UTF-8')['result']
				except:
					raise RPCFailure(json.loads(text)['error']['message'])
		else:
			import http
			s = http.HTTPStatus(status)
			m = ''
			if text:
				try: m = ': ' + json.loads(text)['error']['message']
				except:
					try: m = f': {text.decode()}'
					except: m = f': {text}'
			raise RPCFailure(f'{s.value} {s.name}{m}')

class BitcoinRPCClient(RPCClient,metaclass=aInitMeta):

	auth_type = 'basic'
	has_auth_cookie = True

	def __init__(self,*args,**kwargs):
		pass

	async def __ainit__(self,proto,daemon,backend):

		self.proto = proto
		self.daemon = daemon

		super().__init__(
			host = 'localhost' if g.test_suite else (g.rpc_host or 'localhost'),
			port = daemon.rpc_port )

		self.set_auth() # set_auth() requires cookie, so must be called after __init__() tests daemon is listening
		self.set_backend(backend) # backend requires self.auth

		if g.bob or g.alice:
			from .regtest import MMGenRegtest
			MMGenRegtest(self.proto.coin).switch_user(('alice','bob')[g.bob],quiet=True)

		self.cached = {}
		(
			self.cached['networkinfo'],
			self.blockcount,
			self.cached['blockchaininfo'],
			block0
		) = await self.gathered_call(None, (
				('getnetworkinfo',()),
				('getblockcount',()),
				('getblockchaininfo',()),
				('getblockhash',(0,)),
			))
		self.daemon_version = self.cached['networkinfo']['version']
		self.chain = self.cached['blockchaininfo']['chain']

		tip = await self.call('getblockhash',self.blockcount)
		self.cur_date = (await self.call('getblockheader',tip))['time']
		if self.chain != 'regtest':
			self.chain += 'net'
		assert self.chain in self.proto.networks

		async def check_chainfork_mismatch(block0):
			try:
				if block0 != self.proto.block0:
					raise ValueError(f'Invalid Genesis block for {self.proto.cls_name} protocol')
				for fork in self.proto.forks:
					if fork.height == None or self.blockcount < fork.height:
						break
					if fork.hash != await self.call('getblockhash',fork.height):
						die(3,f'Bad block hash at fork block {fork.height}. Is this the {fork.name} chain?')
			except Exception as e:
				die(2,'{!s}\n{c!r} requested, but this is not the {c} chain!'.format(e,c=self.proto.coin))

		if self.chain == 'mainnet': # skip this for testnet, as Genesis block may change
			await check_chainfork_mismatch(block0)

		self.caps = ('full_node',)
		for func,cap in (
			('setlabel','label_api'),
			('signrawtransactionwithkey','sign_with_key') ):
			if len((await self.call('help',func)).split('\n')) > 3:
				self.caps += (cap,)

	def get_daemon_cfg_fn(self):
		# Use dirname() to remove 'bob' or 'alice' component
		return os.path.join(
			(os.path.dirname(g.data_dir) if self.proto.regtest else self.daemon.datadir),
			self.daemon.cfg_file )

	def get_daemon_auth_cookie_fn(self):
		return os.path.join( self.daemon.datadir, self.daemon.data_subdir, '.cookie' )

	def get_daemon_cfg_options(self,req_keys):

		fn = self.get_daemon_cfg_fn()
		try:
			lines = get_lines_from_file(fn,'',silent=not opt.verbose)
		except:
			vmsg(f'Warning: {fn!r} does not exist or is unreadable')
			return dict((k,None) for k in req_keys)

		def gen():
			for key in req_keys:
				val = None
				for l in lines:
					if l.startswith(key):
						res = l.split('=',1)
						if len(res) == 2 and not ' ' in res[1].strip():
							val = res[1].strip()
				yield (key,val)

		return dict(gen())

	def get_daemon_auth_cookie(self):
		fn = self.get_daemon_auth_cookie_fn()
		return get_lines_from_file(fn,'')[0] if file_is_readable(fn) else ''

	def info(self,info_id):

		def segwit_is_active():
			d = self.cached['blockchaininfo']
			if d['chain'] == 'regtest':
				return True

			try:
				if d['softforks']['segwit']['active'] == True:
					return True
			except:
				pass

			try:
				if d['bip9_softforks']['segwit']['status'] == 'active':
					return True
			except:
				pass

			if g.test_suite:
				return True

			return False

		return locals()[info_id]()

	rpcmethods = (
		'backupwallet',
		'createrawtransaction',
		'decoderawtransaction',
		'disconnectnode',
		'estimatefee',
		'estimatesmartfee',
		'getaddressesbyaccount',
		'getaddressesbylabel',
		'getblock',
		'getblockchaininfo',
		'getblockcount',
		'getblockhash',
		'getblockheader',
		'getblockstats', # mmgen-node-tools
		'getmempoolinfo',
		'getmempoolentry',
		'getnettotals',
		'getnetworkinfo',
		'getpeerinfo',
		'getrawmempool',
		'getmempoolentry',
		'getrawtransaction',
		'gettransaction',
		'importaddress',
		'listaccounts',
		'listlabels',
		'listunspent',
		'setlabel',
		'sendrawtransaction',
		'signrawtransaction',
		'signrawtransactionwithkey', # method new to Core v0.17.0
		'validateaddress',
		'walletpassphrase',
	)

class EthereumRPCClient(RPCClient,metaclass=aInitMeta):

	def __init__(self,*args,**kwargs):
		pass

	async def __ainit__(self,proto,daemon,backend):
		self.proto = proto
		self.daemon = daemon

		super().__init__(
			host = 'localhost' if g.test_suite else (g.rpc_host or 'localhost'),
			port = daemon.rpc_port )

		self.set_backend(backend)

		self.blockcount = int(await self.call('eth_blockNumber'),16)

		vi,bh,ch,nk = await self.gathered_call(None, (
				('parity_versionInfo',()),
				('parity_getBlockHeaderByNumber',()),
				('parity_chain',()),
				('parity_nodeKind',()),
			))

		self.daemon_version = vi['version']
		self.cur_date = int(bh['timestamp'],16)
		self.chain = ch.replace(' ','_')
		self.caps = ('full_node',) if nk['capability'] == 'full' else ()

		try:
			await self.call('eth_chainId')
			self.caps += ('eth_chainId',)
		except RPCFailure:
			pass

	rpcmethods = (
		'eth_accounts',
		'eth_blockNumber',
		'eth_call',
		# Returns the EIP155 chain ID used for transaction signing at the current best block.
		# Null is returned if not available.
		'eth_chainId',
		'eth_gasPrice',
		'eth_getBalance',
		'eth_getBlockByHash',
		'eth_getCode',
		'eth_getTransactionByHash',
		'eth_getTransactionReceipt',
		'eth_protocolVersion',
		'eth_sendRawTransaction',
		'eth_signTransaction',
		'eth_syncing',
		'net_listening',
		'net_peerCount',
		'net_version',
		'parity_chain',
		'parity_chainId', # superseded by eth_chainId
		'parity_chainStatus',
		'parity_composeTransaction',
		'parity_gasCeilTarget',
		'parity_gasFloorTarget',
		'parity_getBlockHeaderByNumber',
		'parity_localTransactions',
		'parity_minGasPrice',
		'parity_mode',
		'parity_netPeers',
		'parity_nextNonce',
		'parity_nodeKind',
		'parity_nodeName',
		'parity_pendingTransactions',
		'parity_pendingTransactionsStats',
		'parity_versionInfo',
	)

class MoneroWalletRPCClient(RPCClient):

	auth_type = 'digest'
	network_proto = 'https'
	host_path = '/json_rpc'
	verify_server = False

	def __init__(self,host,port,user,passwd):
		super().__init__(host,port)
		self.auth = auth_data(user,passwd)
		self.timeout = 3600 # allow enough time to sync ≈1,000,000 blocks
		if True:
			self.set_backend('requests')
		else: # insecure, for debugging only
			self.set_backend('curl')
			self.backend.exec_opts.remove('--silent')
			self.backend.exec_opts.append('--verbose')

	async def call(self,method,*params,**kwargs):
		assert params == (), f'{type(self).__name__}.call() accepts keyword arguments only'
		return await self.process_http_resp(self.backend.run(
			payload = {'id': 0, 'jsonrpc': '2.0', 'method': method, 'params': kwargs },
		))

	rpcmethods = (
		'get_version',
		'get_height',    # sync height of the open wallet
		'get_balance',   # account_index=0, address_indices=[]
		'create_wallet', # filename, password, language="English"
		'open_wallet',   # filename, password
		'close_wallet',
		'restore_deterministic_wallet', # name,password,seed (restore_height,language,seed_offset,autosave_current)
		'refresh',       # start_height
	)

async def rpc_init(proto,backend=None):

	if not 'rpc' in proto.mmcaps:
		die(1,f'Coin daemon operations not supported for {proto.name} protocol!')

	from .daemon import CoinDaemon
	rpc = await {
		'Bitcoin': BitcoinRPCClient,
		'Ethereum': EthereumRPCClient,
	}[proto.base_proto](
		proto   = proto,
		daemon  = CoinDaemon(proto=proto,test_suite=g.test_suite),
		backend = backend or opt.rpc_backend )

	if proto.chain_name != rpc.chain:
		raise RPCChainMismatch(
			'{} protocol chain is {}, but coin daemon chain is {}'.format(
				proto.cls_name,
				proto.chain_name.upper(),
				rpc.chain.upper() ))

	if g.bogus_wallet_data:
		rpc.blockcount = 1000000

	return rpc
