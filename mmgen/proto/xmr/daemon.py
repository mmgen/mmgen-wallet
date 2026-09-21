#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.xmr.daemon: Monero base protocol daemon classes
"""

from pathlib import Path

from ...cfg import gc
from ...util import list_gen, die, contains_any
from ...daemon import CoinDaemon, RPCDaemon, _nw, _dd

class monero_daemon(CoinDaemon):
	daemon_data = _dd('Monero', 18005001, '0.18.5.1-release')
	networks = ('mainnet', 'testnet')
	exec_fn = 'monerod'
	testnet_dir = 'stagenet'
	new_console_mswin = True
	rpc_ports = _nw(18081, 38081, None) # testnet is stagenet
	cfg_file = 'bitmonero.conf'
	datadirs = {
		'linux': [gc.home_dir, '.bitmonero'],
		'darwin': [gc.home_dir, '.bitmonero'],
		'win32': ['/', 'c', 'ProgramData', 'bitmonero']}
	use_pidfile = gc.platform == 'linux'

	def get_p2p_port(self):
		return self.rpc_port - 1

	def init_subclass(self):

		from .rpc import MoneroRPCClient
		self.rpc = MoneroRPCClient(
			cfg    = self.cfg,
			proto  = self.proto,
			host   = 'localhost',
			port   = self.rpc_port,
			user   = None,
			passwd = None,
			test_connection = False,
			daemon = self)

		self.shared_args = list_gen(
			['--no-zmq'],
			[f'--p2p-bind-port={self.p2p_port}', self.p2p_port],
			[f'--rpc-bind-port={self.rpc_port}'],
			['--stagenet', self.network == 'testnet'])

		self.coind_args = list_gen(
			['--hide-my-port'],
			['--no-igd'],
			[f'--data-dir={self.network_datadir}', self.has_non_dfl_datadir],
			[f'--pidfile={self.pidfile}', self.use_pidfile],
			['--detach',                  not (self.opt.no_daemonize or gc.platform=='win32')],
			['--offline',                 not self.opt.online])

	@property
	def stop_cmd(self):
		if gc.platform == 'win32':
			return ['kill', '-Wf', self.pid]
		elif contains_any(self.start_cmd, ['--restricted-rpc', '--public-node']):
			return ['kill', self.pid]
		else:
			return [self.exec_fn] + self.shared_args + ['exit']

class MoneroWalletDaemon(RPCDaemon):

	master_daemon = 'monero_daemon'
	rpc_desc = 'Monero wallet'
	exec_fn = 'monero-wallet-rpc'
	coin = 'XMR'
	new_console_mswin = True
	networks = ('mainnet', 'testnet')
	rpc_ports = _nw(13131, 13141, None) # testnet is non-standard
	use_pidfile = gc.platform == 'linux'
	_reset_ok = ('debug', 'wait', 'pids', 'force_kill')
	test_user_port_shifts = {
		'bob':   10,
		'alice': 20,
		'miner': 30}

	def __init__(
			self,
			cfg,
			proto,
			*,
			wallet_dir  = None,
			user        = None,
			passwd      = None,
			monerod_addr = None,
			proxy       = None,
			port_shift  = None,
			datadir     = None,
			disable_authentication = False,
			trust_monerod = False,
			test_monerod = False,
			**kwargs):

		self.proto = proto

		super().__init__(cfg, **kwargs)

		self.network = proto.network
		self.rpc_port = getattr(self.rpc_ports, self.network) + (11 if self.test_suite else 0)
		self.disable_authentication = disable_authentication

		if port_shift:
			self.rpc_port += port_shift
		elif cfg.test_user:
			self.rpc_port += self.test_user_port_shifts[cfg.test_user]

		if wallet_dir or cfg.wallet_dir:
			self.wallet_dir = Path(wallet_dir or cfg.wallet_dir)
		else:
			from .tw.ctl import MoneroTwCtl
			self.wallet_dir = MoneroTwCtl.get_tw_dir(self.proto)

		fn_stem = f'{self.exec_fn}-{self.bind_port}'
		if self.use_pidfile:
			self.pidfile = self.proto.network_datadir / (fn_stem + '.pid')
		self.logfile = self.proto.network_datadir / (fn_stem + '.log')

		self.proxy = proxy
		self.monerod_addr = monerod_addr
		self.monerod_port = (
			None if monerod_addr else
			CoinDaemon(
				cfg   = self.cfg,
				proto = proto).rpc_port)

		if test_monerod and self.monerod_port:
			import socket
			try:
				socket.create_connection(('localhost', self.monerod_port), timeout=1).close()
			except:
				die('SocketError', f'Unable to connect to Monero daemon at localhost:{self.monerod_port}')

		self.user = user or self.cfg.wallet_rpc_user or self.cfg.monero_wallet_rpc_user
		self.passwd = passwd or self.cfg.wallet_rpc_password or self.cfg.monero_wallet_rpc_password

		assert self.user
		if not self.passwd:
			die(1,
				'You must set your Monero wallet RPC password.\n' +
				'This can be done on the command line with the --wallet-rpc-password option\n' +
				"(insecure, not recommended), or by setting 'monero_wallet_rpc_password' in\n" +
				"the MMGen config file.")

		self.daemon_args = list_gen(
			['--disable-rpc-login', self.disable_authentication],
			['--trusted-daemon', trust_monerod],
			['--untrusted-daemon', not trust_monerod],
			[f'--rpc-bind-port={self.rpc_port}'],
			[f'--wallet-dir={self.wallet_dir}'],
			[f'--log-file={self.logfile}'],
			[f'--rpc-login={self.user}:{self.passwd}', not self.disable_authentication],
			[f'--daemon-address={self.monerod_addr}', self.monerod_addr],
			[f'--daemon-port={self.monerod_port}',    not self.monerod_addr],
			[f'--proxy={self.proxy}',                self.proxy],
			[f'--pidfile={self.pidfile}',            self.use_pidfile],
			['--detach',                             not (self.opt.no_daemonize or gc.platform=='win32')],
			['--stagenet',                           self.network == 'testnet'],
			['--allow-mismatched-daemon-version',    self.test_suite])

		from .rpc import MoneroWalletRPCClient
		self.rpc = MoneroWalletRPCClient(
			cfg             = self.cfg,
			daemon          = self,
			test_connection = False)

	def start(self, *args, **kwargs):
		try: # NB: required due to bug in v18.3.1: PID file not deleted on shutdown
			self.pidfile.unlink()
		except FileNotFoundError:
			pass
		super().start(*args, **kwargs)
