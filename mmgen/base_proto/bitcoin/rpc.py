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
base_proto.bitcoin.rpc: Bitcoin base protocol RPC client class
"""

import os

from ...globalvars import g
from ...base_obj import AsyncInit
from ...util import ymsg,vmsg,die
from ...fileutil import get_lines_from_file
from ...rpc import RPCClient

class CallSigs:

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

		@classmethod
		def gettransaction(cls,txid,include_watchonly,verbose):
			return (
				'gettransaction',
				txid,               # 1. transaction id
				include_watchonly,  # 2. optional, default=true for watch-only wallets, otherwise false
				verbose,            # 3. optional, default=false -- include a `decoded` field containing
									#    the decoded transaction (equivalent to RPC decoderawtransaction)
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

		@classmethod
		def gettransaction(cls,txid,include_watchonly,verbose):
			return (
				'gettransaction',
				txid,               # 1. transaction id
				include_watchonly,  # 2. optional, default=true for watch-only wallets, otherwise false
			)

	class bitcoin_cash_node(litecoin_core):
		pass

class BitcoinRPCClient(RPCClient,metaclass=AsyncInit):

	auth_type = 'basic'
	has_auth_cookie = True

	async def __init__(self,proto,daemon,backend):

		self.proto = proto
		self.daemon = daemon
		self.call_sigs = getattr(CallSigs,daemon.id,None)

		super().__init__(
			host = 'localhost' if g.test_suite else (g.rpc_host or 'localhost'),
			port = daemon.rpc_port )

		self.set_auth() # set_auth() requires cookie, so must be called after __init__() tests daemon is listening
		self.set_backend(backend) # backend requires self.auth

		self.cached = {}

		self.caps = ('full_node',)
		for func,cap in (
			('setlabel','label_api'),
			('getdeploymentinfo','deployment_info'),
			('signrawtransactionwithkey','sign_with_key') ):
			if len((await self.call('help',func)).split('\n')) > 3:
				self.caps += (cap,)

		call_group = [
			('getblockcount',()),
			('getblockhash',(0,)),
			('getnetworkinfo',()),
			('getblockchaininfo',()),
		] + (
			[('getdeploymentinfo',())] if 'deployment_info' in self.caps else []
		)

		(
			self.blockcount,
			block0,
			self.cached['networkinfo'],
			self.cached['blockchaininfo'],
			self.cached['deploymentinfo'],
		) = (
			await self.gathered_call(None,tuple(call_group))
		) + (
			[] if 'deployment_info' in self.caps else [None]
		)

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
				die(4,f'ERROR: more than one {self.daemon.coind_name} wallet loaded: {wallets}')
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
		from ...opts import opt
		try:
			lines = get_lines_from_file(fn,'daemon config file',silent=not opt.verbose)
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
		return get_lines_from_file(fn,'cookie',quiet=True)[0] if os.access(fn,os.R_OK) else ''

	@staticmethod
	def make_host_path(wallet):
		return (
			'/wallet/{}'.format('bob' if g.bob else 'alice') if (g.bob or g.alice) else
			'/wallet/{}'.format(wallet) if wallet else '/'
		)

	def info(self,info_id):

		def segwit_is_active():

			if 'deployment_info' in self.caps:
				return (
					self.cached['deploymentinfo']['deployments']['segwit']['active']
					or ( g.test_suite and not os.getenv('MMGEN_TEST_SUITE_REGTEST') )
				)

			d = self.cached['blockchaininfo']

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
		'importaddress', # address (address or script) label rescan p2sh (Add P2SH version of the script)
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
