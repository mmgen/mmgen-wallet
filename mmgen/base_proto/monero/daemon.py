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
base_proto.monero.daemon: Monero daemon classes
"""

import os

from ...globalvars import g
from ...opts import opt
from ...util import list_gen
from ...daemon import CoinDaemon,RPCDaemon,_nw

class MoneroWalletDaemon(RPCDaemon):

	master_daemon = 'monero_daemon'
	rpc_type = 'Monero wallet'
	exec_fn = 'monero-wallet-rpc'
	coin = 'XMR'
	new_console_mswin = True
	rpc_ports = _nw(13131, 13141, None) # testnet is non-standard

	def __init__(self, proto, wallet_dir,
			test_suite  = False,
			host        = None,
			user        = None,
			passwd      = None,
			daemon_addr = None,
			proxy       = None,
			port_shift  = None,
			datadir     = None ):

		self.proto = proto
		self.test_suite = test_suite

		super().__init__()

		self.network = proto.network
		self.wallet_dir = wallet_dir
		self.rpc_port = getattr(self.rpc_ports,self.network) + (11 if test_suite else 0)
		if port_shift:
			self.rpc_port += port_shift

		id_str = f'{self.exec_fn}-{self.bind_port}'
		self.datadir = os.path.join((datadir or self.exec_fn),('','test_suite')[test_suite])
		self.pidfile = os.path.join(self.datadir,id_str+'.pid')
		self.logfile = os.path.join(self.datadir,id_str+'.log')

		self.proxy = proxy
		self.daemon_addr = daemon_addr
		self.daemon_port = None if daemon_addr else CoinDaemon(proto=proto,test_suite=test_suite).rpc_port

		self.host = host or opt.wallet_rpc_host or g.monero_wallet_rpc_host
		self.user = user or opt.wallet_rpc_user or g.monero_wallet_rpc_user
		self.passwd = passwd or opt.wallet_rpc_password or g.monero_wallet_rpc_password

		assert self.host
		assert self.user
		if not self.passwd:
			from ...util import die
			die(1,
				'You must set your Monero wallet RPC password.\n' +
				'This can be done on the command line with the --wallet-rpc-password option\n' +
				"(insecure, not recommended), or by setting 'monero_wallet_rpc_password' in\n" +
				"the MMGen config file." )

		self.daemon_args = list_gen(
			['--untrusted-daemon'],
			[f'--rpc-bind-port={self.rpc_port}'],
			['--wallet-dir='+self.wallet_dir],
			['--log-file='+self.logfile],
			[f'--rpc-login={self.user}:{self.passwd}'],
			[f'--daemon-address={self.daemon_addr}', self.daemon_addr],
			[f'--daemon-port={self.daemon_port}',    not self.daemon_addr],
			[f'--proxy={self.proxy}',                self.proxy],
			[f'--pidfile={self.pidfile}',            self.platform == 'linux'],
			['--detach',                             not (self.opt.no_daemonize or self.platform=='win')],
			['--stagenet',                           self.network == 'testnet'],
		)

		from ...rpc import MoneroWalletRPCClient
		self.rpc = MoneroWalletRPCClient( daemon=self, test_connection=False )
