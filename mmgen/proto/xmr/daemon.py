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
proto.xmr.daemon: Monero base protocol daemon classes
"""

import sys, os

from ...cfg import gc
from ...util import list_gen, die, contains_any
from ...daemon import CoinDaemon, RPCDaemon, _nw, _dd

class monero_daemon(CoinDaemon):
	daemon_data = _dd('Monero', 18004003, '0.18.4.3-release')
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

	def init_datadir(self):
		self.logdir = super().init_datadir()
		return os.path.join(
			self.logdir,
			self.testnet_dir if self.network == 'testnet' else '')

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

		self.use_pidfile = sys.platform == 'linux'

		self.shared_args = list_gen(
			['--no-zmq'],
			[f'--p2p-bind-port={self.p2p_port}', self.p2p_port],
			[f'--rpc-bind-port={self.rpc_port}'],
			['--stagenet', self.network == 'testnet'],
		)

		self.coind_args = list_gen(
			['--hide-my-port'],
			['--no-igd'],
			[f'--data-dir={self.datadir}', self.non_dfl_datadir],
			[f'--pidfile={self.pidfile}', self.use_pidfile],
			['--detach',                  not (self.opt.no_daemonize or self.platform=='win32')],
			['--offline',                 not self.opt.online],
		)

	@property
	def stop_cmd(self):
		if self.platform == 'win32':
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
	_reset_ok = ('debug', 'wait', 'pids', 'force_kill')
	test_suite_datadir = os.path.join('test', 'daemons', 'xmrtest', 'wallet_rpc')

	def start(self, *args, **kwargs):
		try: # NB: required due to bug in v18.3.1: PID file not deleted on shutdown
			os.unlink(self.pidfile)
		except FileNotFoundError:
			pass
		super().start(*args, **kwargs)

	def __init__(
			self,
			cfg,
			proto,
			*,
			wallet_dir  = None,
			test_suite  = False,
			user        = None,
			passwd      = None,
			monerod_addr = None,
			proxy       = None,
			port_shift  = None,
			datadir     = None,
			trust_monerod = False,
			test_monerod = False,
			opts         = None,
			flags        = None):

		self.proto = proto
		self.test_suite = test_suite

		super().__init__(cfg, opts=opts, flags=flags)

		self.network = proto.network
		self.wallet_dir = wallet_dir or (self.test_suite_datadir if test_suite else None)
		self.rpc_port = (
			self.cfg.wallet_rpc_port or
			getattr(self.rpc_ports, self.network) + (11 if test_suite else 0))
		if port_shift:
			self.rpc_port += port_shift

		id_str = f'{self.exec_fn}-{self.bind_port}'
		self.datadir = datadir or (self.test_suite_datadir if test_suite else self.exec_fn + '.d')
		self.pidfile = os.path.join(self.datadir, id_str+'.pid')
		self.logfile = os.path.join(self.datadir, id_str+'.log')

		self.use_pidfile = sys.platform == 'linux'

		self.proxy = proxy
		self.monerod_addr = monerod_addr
		self.monerod_port = (
			None if monerod_addr else
			CoinDaemon(
				cfg        = self.cfg,
				proto      = proto,
				test_suite = test_suite).rpc_port
		)

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
			['--trusted-daemon', trust_monerod],
			['--untrusted-daemon', not trust_monerod],
			[f'--rpc-bind-port={self.rpc_port}'],
			[f'--wallet-dir={self.wallet_dir}'],
			[f'--log-file={self.logfile}'],
			[f'--rpc-login={self.user}:{self.passwd}'],
			[f'--daemon-address={self.monerod_addr}', self.monerod_addr],
			[f'--daemon-port={self.monerod_port}',    not self.monerod_addr],
			[f'--proxy={self.proxy}',                self.proxy],
			[f'--pidfile={self.pidfile}',            self.platform == 'linux'],
			['--detach',                             not (self.opt.no_daemonize or self.platform=='win32')],
			['--stagenet',                           self.network == 'testnet'],
			['--allow-mismatched-daemon-version',    test_suite],
		)

		from .rpc import MoneroWalletRPCClient
		self.rpc = MoneroWalletRPCClient(
			cfg             = self.cfg,
			daemon          = self,
			test_connection = False)
