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
proto.btc.rpc.local: Bitcoin base protocol local RPC client for the MMGen Project
"""

import os

from ....base_obj import AsyncInit
from ....obj import TrackingWalletName
from ....util import ymsg, die, fmt
from ....fileutil import get_lines_from_file
from ....rpc.local import RPCClient
from ....rpc.util import auth_data

no_credentials_errmsg = """
	Error: no {proto_name} RPC authentication method found

	RPC credentials must be supplied using one of the following methods:

	1) If daemon is local and running as same user as you:

	   - no credentials required, or matching rpcuser/rpcpassword and
	     rpc_user/rpc_password values in {cf_name}.conf and mmgen.cfg

	2) If daemon is running remotely or as different user:

	   - matching credentials in {cf_name}.conf and mmgen.cfg as described
	     above

	The --rpc-user/--rpc-password options may be supplied on the MMGen command
	line.  They override the corresponding values in mmgen.cfg. Set them to an
	empty string to use cookie authentication with a local server when the
	options are set in mmgen.cfg.

	For better security, rpcauth should be used in {cf_name}.conf instead of
	rpcuser/rpcpassword.
"""

class CallSigs:

	class bitcoin_core:

		def __init__(self, cfg, rpc):
			self.cfg = cfg
			self.rpc = rpc

		def createwallet(
				self,
				wallet_name,
				*,
				no_keys         = True,
				blank           = True,
				passphrase      = '',
				descriptors     = True,
				load_on_startup = True):
			"""
			Quirk: when --datadir is specified (even if standard), wallet is created directly in
			datadir, otherwise in datadir/wallets
			"""
			return (
				'createwallet',
				wallet_name,     # 1. wallet_name
				no_keys,         # 2. disable_private_keys
				blank,           # 3. blank (no keys or seed)
				passphrase,      # 4. passphrase (empty string for non-encrypted)
				False,           # 5. avoid_reuse (track address reuse)
				descriptors,     # 6. descriptors (native descriptor wallet)
				load_on_startup) # 7. load_on_startup

		# Get detailed information about in-wallet transaction <txid>
		# Arguments:
		# 1. txid                 (string, required) The transaction id
		# 2. include_watchonly    (boolean, optional, default=true for watch-only wallets, otherwise
		#                         false) Whether to include watch-only addresses in balance calculation
		#                         and details[]
		# 3. verbose              (boolean, optional, default=false) Whether to include a `decoded`
		#                         field containing the decoded transaction (equivalent to RPC
		#                         decoderawtransaction)
		def gettransaction(self, txid, include_watchonly, verbose):
			return (
				'gettransaction',
				txid,
				verbose
			) if 'descriptor_wallet_only' in self.rpc.caps else (
				'gettransaction',
				txid,
				include_watchonly,
				verbose)

		# List received transactions by label.
		# 1. minconf                      (numeric, optional, default=1) The minimum number of
		#                                 confirmations before payments are included.
		# 2. include_empty                (boolean, optional, default=false) Whether to include labels
		#                                 that haven't received any payments.
		# 3. include_watchonly            (boolean, optional, default=true for watch-only wallets,
		#                                 otherwise false) Whether to include watch-only addresses
		#                                 (see 'importaddress')
		# 4. include_immature_coinbase    (boolean, optional, default=false) Include immature coinbase
		#                                 transactions.
		def listreceivedbylabel(
				self,
				*,
				minconf = 1,
				include_empty = False,
				include_watchonly = True,
				include_immature_coinbase = False):
			return (
				'listreceivedbylabel',
				minconf,
				include_empty,
				include_immature_coinbase
			) if 'descriptor_wallet_only' in self.rpc.caps else (
				'listreceivedbylabel',
				minconf,
				include_empty,
				include_watchonly,
				include_immature_coinbase)

		# Get all transactions in blocks since block [blockhash], or all transactions if omitted.
		# 1. blockhash            (string, optional) If set, the block hash to list transactions since,
		#                         otherwise list all transactions.
		# 2. target_confirmations (numeric, optional, default=1) Return the nth block hash from the main
		#                         chain. e.g. 1 would mean the best block hash. Note: this is not used
		#                         as a filter, but only affects [lastblock] in the return value
		# 3. include_watchonly    (boolean, optional, default=true for watch-only wallets, otherwise
		#                         false) Include transactions to watch-only addresses
		# 4. include_removed      (boolean, optional, default=true) Show transactions that were removed
		#                         due to a reorg in the "removed" array (not guaranteed to work on
		#                         pruned nodes)
		def listsinceblock(
				self,
				*,
				blockhash = '',
				target_confirmations = 1,
				include_watchonly = True,
				include_removed = True):
			return (
				'listsinceblock',
				blockhash,
				target_confirmations,
				include_removed
			) if 'descriptor_wallet_only' in self.rpc.caps else (
				'listsinceblock',
				blockhash,
				target_confirmations,
				include_watchonly,
				include_removed)

	class litecoin_core(bitcoin_core):

		def createwallet(
				self,
				wallet_name,
				*,
				no_keys         = True,
				blank           = True,
				passphrase      = '',
				descriptors     = True,
				load_on_startup = True):
			return (
				'createwallet',
				wallet_name,    # 1. wallet_name
				no_keys,        # 2. disable_private_keys
				blank)          # 3. blank (no keys or seed)

		def gettransaction(self, txid, include_watchonly, verbose):
			return (
				'gettransaction',
				txid,               # 1. transaction id
				include_watchonly)  # 2. optional, default=true for watch-only wallets, otherwise false

		def listreceivedbylabel(
				self,
				*,
				minconf = 1,
				include_empty = False,
				include_watchonly = True,
				include_immature_coinbase = False):
			return (
				'listreceivedbylabel',
				minconf,
				include_empty,
				include_watchonly)

	class bitcoin_cash_node(litecoin_core):
		pass

class BitcoinRPCClient(RPCClient, metaclass=AsyncInit):

	auth_type = 'basic'
	has_auth_cookie = True
	wallet_path = '/'
	dfl_twname = 'mmgen-tracking-wallet'

	async def __init__(
			self,
			cfg,
			proto,
			*,
			daemon,
			backend,
			ignore_wallet):

		self.proto = proto
		self.daemon = daemon
		self.call_sigs = getattr(CallSigs, daemon.id)(cfg, self)
		self.twname = TrackingWalletName(cfg.test_user or proto.tw_name or cfg.tw_name or self.dfl_twname)

		super().__init__(
			cfg  = cfg,
			host = proto.rpc_host or cfg.rpc_host or 'localhost',
			port = daemon.rpc_port)

		self.set_auth()

		await self.set_backend_async(backend) # backend requires self.auth

		self.cached = {}

		self.caps = ('full_node',)
		for func, cap in (
			('setlabel', 'label_api'),
			('getdeploymentinfo', 'deployment_info'),
			('signrawtransactionwithkey', 'sign_with_key')):
			if len((await self.call('help', func)).split('\n')) > 3:
				self.caps += (cap,)

		call_group = [
			('getblockcount', ()),
			('getblockhash', (0,)),
			('getnetworkinfo', ()),
			('getblockchaininfo', ()),
		] + (
			[('getdeploymentinfo', ())] if 'deployment_info' in self.caps else []
		)

		(
			self.blockcount,
			block0,
			self.cached['networkinfo'],
			self.cached['blockchaininfo'],
			self.cached['deploymentinfo'],
		) = (
			await self.gathered_call(None, tuple(call_group))
		) + (
			[] if 'deployment_info' in self.caps else [None]
		)

		self.daemon_version = self.cached['networkinfo']['version']
		self.daemon_version_str = self.cached['networkinfo']['subversion']
		self.chain = self.cached['blockchaininfo']['chain']

		if self.daemon.id == 'bitcoin_core' and self.daemon_version >= 300000:
			self.caps += ('descriptor_wallet_only',)

		tip = await self.call('getblockhash', self.blockcount)
		self.cur_date = (await self.call('getblockheader', tip))['time']
		if self.chain != 'regtest':
			self.chain += 'net'
		assert self.chain in self.proto.networks

		async def check_chainfork_mismatch(block0):
			try:
				if block0 != self.proto.block0:
					raise ValueError(f'Invalid Genesis block for {self.proto.cls_name} protocol')
				for fork in self.proto.forks:
					if fork.height is None or self.blockcount < fork.height:
						break
					if fork.hash != await self.call('getblockhash', fork.height):
						die(3, f'Bad block hash at fork block {fork.height}. Is this the {fork.name} chain?')
			except Exception as e:
				die(2, '{!s}\n{c!r} requested, but this is not the {c} chain!'.format(e, c=self.proto.coin))

		if self.chain == 'mainnet': # skip this for testnet, as Genesis block may change
			await check_chainfork_mismatch(block0)

		if not ignore_wallet:
			await self.check_or_create_daemon_wallet()

		# for regtest, wallet_path must remain '/' until Carol’s user wallet has been created
		if self.chain != 'regtest' or cfg.test_user:
			self.wallet_path = f'/wallet/{self.twname}'

	@property
	async def walletinfo(self):
		if not hasattr(self, '_walletinfo'):
			self._walletinfo = await self.call('getwalletinfo')
		return self._walletinfo

	def set_auth(self):
		"""
		MMGen's credentials override coin daemon's
		"""
		if self.cfg.network == 'regtest':
			from ..regtest import MMGenRegtest
			user = MMGenRegtest.rpc_user
			passwd = MMGenRegtest.rpc_password
		else:
			user = (
				self.proto.rpc_user or self.cfg.rpc_user or self.get_daemon_cfg_option('rpcuser')
				or self.daemon.rpc_user)
			passwd = (
				self.proto.rpc_password or self.cfg.rpc_password or self.get_daemon_cfg_option('rpcpassword')
				or self.daemon.rpc_password)

		if user and passwd:
			self.auth = auth_data(user, passwd)
			return

		if self.has_auth_cookie:
			if cookie := self.get_daemon_auth_cookie():
				self.auth = auth_data(*cookie.split(':'))
				return

		die(1, '\n\n' + fmt(no_credentials_errmsg, strip_char='\t', indent='  ').format(
			proto_name = self.proto.name,
			cf_name = (self.proto.is_fork_of or self.proto.name).lower()))

	def make_host_path(self, wallet):
		return f'/wallet/{wallet}' if wallet else self.wallet_path

	@property
	async def tracking_wallet_exists(self):
		return self.twname in [i['name'] for i in (await self.call('listwalletdir'))['wallets']]

	async def check_or_create_daemon_wallet(self):

		if self.chain == 'regtest' and self.cfg.test_user != 'carol':
			return

		loaded_wnames = await self.call('listwallets')

		if self.twname not in loaded_wnames:
			wnames = [i['name'] for i in (await self.call('listwalletdir'))['wallets']]
			if self.twname in wnames:
				await self.call('loadwallet', self.twname)
			else:
				await self.icall('createwallet', wallet_name=self.twname)
				ymsg(f'Created {self.daemon.coind_name} wallet {self.twname!r}')

	def get_daemon_cfg_fn(self):
		# Use dirname() to remove 'bob' or 'alice' component
		return os.path.join(
			(os.path.dirname(self.cfg.data_dir) if self.proto.regtest else self.daemon.datadir),
			self.daemon.cfg_file)

	def get_daemon_cfg_option(self, req_key):
		return list(self.get_daemon_cfg_options([req_key]).values())[0]

	def get_daemon_cfg_options(self, req_keys):

		fn = self.get_daemon_cfg_fn()
		try:
			lines = get_lines_from_file(
				self.cfg, fn, desc='daemon config file', silent=not self.cfg.verbose)
		except:
			self.cfg._util.vmsg(f'Warning: {fn!r} does not exist or is unreadable')
			return dict((k, None) for k in req_keys)

		def gen():
			for key in req_keys:
				val = None
				for l in lines:
					if l.startswith(key):
						res = l.split('=', 1)
						if len(res) == 2 and not ' ' in res[1].strip():
							val = res[1].strip()
				yield (key, val)

		return dict(gen())

	def get_daemon_auth_cookie(self):
		fn = self.daemon.auth_cookie_fn
		return get_lines_from_file(
			self.cfg, fn, desc='cookie', quiet=True)[0] if os.access(fn, os.R_OK) else ''

	def info(self, info_id):

		def segwit_is_active():

			if 'deployment_info' in self.caps:
				return (
					self.cached['deploymentinfo']['deployments']['segwit']['active']
					or (self.cfg.test_suite and not self.chain == 'regtest')
				)

			d = self.cached['blockchaininfo']

			try:
				if d['softforks']['segwit']['active'] is True:
					return True
			except:
				pass

			try:
				if d['bip9_softforks']['segwit']['status'] == 'active':
					return True
			except:
				pass

			if self.cfg.test_suite and not self.chain == 'regtest':
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
		'getdeploymentinfo',
		'getmempoolentry',
		'getmempoolentry',
		'getmempoolinfo',
		'getnettotals',
		'getnetworkinfo',
		'getpeerinfo',
		'getrawmempool',
		'getrawtransaction',
		'getrawtransaction',
		'gettransaction',
		'gettransaction',
		'getwalletinfo',
		'importaddress', # address (address or script) label rescan p2sh (Add P2SH version of the script)
		'importdescriptors', # like above, but for descriptor wallets
		'listaccounts',
		'listlabels',
		'listreceivedbylabel',
		'listsinceblock',
		'listunspent',
		'sendrawtransaction',
		'setlabel',
		'signrawtransaction',
		'signrawtransactionwithkey', # method new to Core v0.17.0
		'validateaddress',
		'walletpassphrase',
	)
