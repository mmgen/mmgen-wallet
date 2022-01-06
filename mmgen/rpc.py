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

import base64,json,asyncio
from decimal import Decimal
from .common import *
from .obj import AsyncInit

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

	class aiohttp(base):

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

		def __init__(self,caller):
			super().__init__(caller)
			import requests,urllib3
			urllib3.disable_warnings()
			self.session = requests.Session()
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
				raise RPCFailure(str(e))
			return (r.read(),r.status)

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
			res = run(exec_cmd,stdout=PIPE,check=True).stdout.decode()
			# res = run(exec_cmd,stdout=PIPE,check=True,text='UTF-8').stdout # Python 3.7+
			return (res[:-3],int(res[-3:]))

from collections import namedtuple
auth_data = namedtuple('rpc_auth_data',['user','passwd'])

class CallSigs:

	class Bitcoin:

		class bitcoin_core:

			@classmethod
			def createwallet(cls,wallet_name,no_keys=True,blank=True,passphrase='',load_on_startup=True):
				"""
				Quirk: when --datadir is specified (even if standard), wallet is created directly in
				datadir, otherwise in datadir/wallets
				"""
				return (
					'createwallet',
					wallet_name,    # 1. wallet_name
					no_keys,        # 2. disable_private_keys
					blank,          # 3. blank (no keys or seed)
					passphrase,     # 4. passphrase (empty string for non-encrypted)
					False,          # 5. avoid_reuse (track address reuse)
					False,          # 6. descriptors (native descriptor wallet)
					load_on_startup # 7. load_on_startup
				)

		class litecoin_core(bitcoin_core):

			@classmethod
			def createwallet(cls,wallet_name,no_keys=True,blank=True,passphrase='',load_on_startup=True):
				return (
					'createwallet',
					wallet_name,    # 1. wallet_name
					no_keys,        # 2. disable_private_keys
					blank,          # 3. blank (no keys or seed)
				)

		class bitcoin_cash_node(litecoin_core): pass

	class Ethereum: pass

class RPCClient(MMGenObject):

	json_rpc = True
	auth_type = None
	has_auth_cookie = False
	network_proto = 'http'
	host_path = ''
	proxy = None

	def __init__(self,host,port,test_connection=True):

		dmsg_rpc(f'=== {type(self).__name__}.__init__() debug ===')
		dmsg_rpc(f'    cls [{type(self).__name__}] host [{host}] port [{port}]\n')

		if test_connection:
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

	@staticmethod
	def make_host_path(foo):
		return ''

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
					raise RPCFailure(m)
		else:
			import http
			m,s = ( '', http.HTTPStatus(status) )
			if text:
				try:
					m = json.loads(text)['error']['message']
				except:
					try: m = text.decode()
					except: m = text
			raise RPCFailure(f'{s.value} {s.name}: {m}')

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

class BitcoinRPCClient(RPCClient,metaclass=AsyncInit):

	auth_type = 'basic'
	has_auth_cookie = True

	async def __init__(self,proto,daemon,backend):

		self.proto = proto
		self.daemon = daemon
		self.call_sigs = getattr(getattr(CallSigs,proto.base_proto),daemon.id,None)

		super().__init__(
			host = 'localhost' if g.test_suite else (g.rpc_host or 'localhost'),
			port = daemon.rpc_port )

		self.set_auth() # set_auth() requires cookie, so must be called after __init__() tests daemon is listening
		self.set_backend(backend) # backend requires self.auth

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
		self.daemon_version_str = self.cached['networkinfo']['subversion']
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

		if not self.chain == 'regtest':
			await self.check_tracking_wallet()

	async def check_tracking_wallet(self,wallet_checked=[]):
		if not wallet_checked:
			wallets = await self.call('listwallets')
			if len(wallets) == 0:
				wname = self.daemon.tracking_wallet_name
				await self.icall('createwallet',wallet_name=wname)
				ymsg(f'Created {self.daemon.coind_name} wallet {wname!r}')
			elif len(wallets) > 1: # support only one loaded wallet for now
				rdie(2,f'ERROR: more than one {self.daemon.coind_name} wallet loaded: {wallets}')
			wallet_checked.append(True)

	def get_daemon_cfg_fn(self):
		# Use dirname() to remove 'bob' or 'alice' component
		return os.path.join(
			(os.path.dirname(g.data_dir) if self.proto.regtest else self.daemon.datadir),
			self.daemon.cfg_file )

	def get_daemon_auth_cookie_fn(self):
		return os.path.join(self.daemon.network_datadir,'.cookie')

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
		return get_lines_from_file(fn,'')[0] if os.access(fn,os.R_OK) else ''

	@staticmethod
	def make_host_path(wallet):
		return (
			'/wallet/{}'.format('bob' if g.bob else 'alice') if (g.bob or g.alice) else
			'/wallet/{}'.format(wallet) if wallet else '/'
		)

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

class EthereumRPCClient(RPCClient,metaclass=AsyncInit):

	async def __init__(self,proto,daemon,backend):
		self.proto = proto
		self.daemon = daemon
		self.call_sigs = getattr(getattr(CallSigs,proto.base_proto),daemon.id,None)

		super().__init__(
			host = 'localhost' if g.test_suite else (g.rpc_host or 'localhost'),
			port = daemon.rpc_port )

		self.set_backend(backend)

		vi,bh,ci = await self.gathered_call(None, (
				('web3_clientVersion',()),
				('eth_getBlockByNumber',('latest',False)),
				('eth_chainId',()),
			))

		import re
		vip = re.match(self.daemon.version_pat,vi,re.ASCII)
		if not vip:
			ydie(1,fmt(f"""
			Aborting on daemon mismatch:
			  Requested daemon: {self.daemon.id}
			  Running daemon:   {vi}
			""",strip_char='\t').rstrip())

		self.daemon_version = int('{:d}{:03d}{:03d}'.format(*[int(e) for e in vip.groups()]))
		self.daemon_version_str = '{}.{}.{}'.format(*vip.groups())
		self.daemon_version_info = vi

		self.blockcount = int(bh['number'],16)
		self.cur_date = int(bh['timestamp'],16)

		self.caps = ()
		from .obj import Int
		if self.daemon.id in ('parity','openethereum'):
			if (await self.call('parity_nodeKind'))['capability'] == 'full':
				self.caps += ('full_node',)
			self.chainID = None if ci == None else Int(ci,16) # parity/oe return chainID only for dev chain
			self.chain = (await self.call('parity_chain')).replace(' ','_').replace('_testnet','')
		elif self.daemon.id in ('geth','erigon'):
			if self.daemon.network == 'mainnet':
				daemon_warning(self.daemon.id)
			self.caps += ('full_node',)
			self.chainID = Int(ci,16)
			self.chain = self.proto.chain_ids[self.chainID]

	rpcmethods = (
		'eth_blockNumber',
		'eth_call',
		# Returns the EIP155 chain ID used for transaction signing at the current best block.
		# Parity: Null is returned if not available, ID not required in transactions
		# Erigon: always returns ID, requires ID in transactions
		'eth_chainId',
		'eth_gasPrice',
		'eth_getBalance',
		'eth_getCode',
		'eth_getTransactionCount',
		'eth_getTransactionReceipt',
		'eth_sendRawTransaction',
		'parity_chain',
		'parity_nodeKind',
		'parity_pendingTransactions',
		'txpool_content',
	)

class MoneroRPCClient(RPCClient):

	auth_type = None
	network_proto = 'https'
	host_path = '/json_rpc'
	verify_server = False

	def __init__(self,host,port,user,passwd,test_connection=True,proxy=None,daemon=None):
		if proxy is not None:
			from .obj import IPPort
			self.proxy = IPPort(proxy)
			test_connection = False
			if host.endswith('.onion'):
				self.network_proto = 'http'
		super().__init__(host,port,test_connection)
		if self.auth_type:
			self.auth = auth_data(user,passwd)
		if True:
			self.set_backend('requests')
		else: # insecure, for debugging only
			self.set_backend('curl')
			self.backend.exec_opts.remove('--silent')
			self.backend.exec_opts.append('--verbose')
		self.daemon = daemon

	async def call(self,method,*params,**kwargs):
		assert params == (), f'{type(self).__name__}.call() accepts keyword arguments only'
		return await self.process_http_resp(self.backend.run(
			payload = {'id': 0, 'jsonrpc': '2.0', 'method': method, 'params': kwargs },
			timeout = 3600, # allow enough time to sync ≈1,000,000 blocks
			wallet = None
		))

	rpcmethods = ( 'get_info', )

class MoneroRPCClientRaw(MoneroRPCClient):

	json_rpc = False
	host_path = '/'

	async def call(self,method,*params,**kwargs):
		assert params == (), f'{type(self).__name__}.call() accepts keyword arguments only'
		return await self.process_http_resp(self.backend.run(
			payload = kwargs,
			timeout = self.timeout,
			wallet = method
		))

	@staticmethod
	def make_host_path(arg):
		return arg

	async def do_stop_daemon(self,silent=False):
		return await self.call('stop_daemon')

	rpcmethods = ( 'get_height', 'send_raw_transaction', 'stop_daemon' )

class MoneroWalletRPCClient(MoneroRPCClient):

	auth_type = 'digest'

	def __init__(self,daemon,test_connection=True):

		RPCClient.__init__(
			self,
			daemon.host,
			daemon.rpc_port,
			test_connection = test_connection )

		self.daemon = daemon
		self.auth = auth_data(daemon.user,daemon.passwd)
		self.set_backend('requests')

	rpcmethods = (
		'get_version',
		'get_height',    # sync height of the open wallet
		'get_balance',   # account_index=0, address_indices=[]
		'create_wallet', # filename, password, language="English"
		'open_wallet',   # filename, password
		'close_wallet',
		# filename,password,seed (restore_height,language,seed_offset,autosave_current)
		'restore_deterministic_wallet',
		'refresh',       # start_height
	)

	async def do_stop_daemon(self,silent=False):
		"""
		NB: the 'stop_wallet' RPC call closes the open wallet before shutting down the daemon,
		returning an error if no wallet is open
		"""
		return await self.call('stop_wallet')

class daemon_warning(oneshot_warning_group):

	class geth:
		color = 'yellow'
		message = 'Geth has not been tested on mainnet.  You may experience problems.'

	class erigon:
		color = 'red'
		message = 'Erigon support is EXPERIMENTAL.  Use at your own risk!!!'

	class version:
		color = 'yellow'
		message = 'ignoring unsupported {} daemon version at user request'

def handle_unsupported_daemon_version(rpc,name,warn_only):
	if warn_only:
		daemon_warning('version',div=name,fmt_args=[rpc.daemon.coind_name])
	else:
		name = rpc.daemon.coind_name
		rdie(1,'\n'+fmt(f"""
			The running {name} daemon has version {rpc.daemon_version_str}.
			This version of MMGen is tested only on {name} v{rpc.daemon.coind_version_str} and below.

			To avoid this error, downgrade your daemon to a supported version.

			Alternatively, you may invoke the command with the --ignore-daemon-version
			option, in which case you proceed at your own risk.
			""",indent='    '))

async def rpc_init(proto,backend=None,daemon=None,ignore_daemon_version=False):

	if not 'rpc' in proto.mmcaps:
		die(1,f'Coin daemon operations not supported for {proto.name} protocol!')

	from .daemon import CoinDaemon
	rpc = await {
		'Bitcoin': BitcoinRPCClient,
		'Ethereum': EthereumRPCClient,
	}[proto.base_proto](
		proto   = proto,
		daemon  = daemon or CoinDaemon(proto=proto,test_suite=g.test_suite),
		backend = backend or opt.rpc_backend )

	if rpc.daemon_version > rpc.daemon.coind_version:
		handle_unsupported_daemon_version(
			rpc,
			proto.name,
			ignore_daemon_version or proto.ignore_daemon_version or g.ignore_daemon_version )

	if rpc.chain not in proto.chain_names:
		raise RPCChainMismatch('\n'+fmt(f"""
			Protocol:           {proto.cls_name}
			Valid chain names:  {fmt_list(proto.chain_names,fmt='bare')}
			RPC client chain:   {rpc.chain}
			""",indent='  ').rstrip())

	return rpc
