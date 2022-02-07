#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
base_proto.monero.rpc: Monero base protocol RPC client class
"""

from ...rpc import RPCClient,IPPort,auth_data

class MoneroRPCClient(RPCClient):

	auth_type = None
	network_proto = 'https'
	host_path = '/json_rpc'
	verify_server = False

	def __init__(self,host,port,user,passwd,test_connection=True,proxy=None,daemon=None):

		if proxy is not None:
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
