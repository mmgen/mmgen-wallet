#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
proto.btc.daemon: Bitcoin base protocol daemon classes
"""

import os

from ...globalvars import g
from ...opts import opt
from ...util import list_gen
from ...daemon import CoinDaemon,_nw,_dd

class bitcoin_core_daemon(CoinDaemon):
	daemon_data = _dd('Bitcoin Core', 230000, '23.0.0')
	exec_fn = 'bitcoind'
	cli_fn = 'bitcoin-cli'
	testnet_dir = 'testnet3'
	cfg_file_hdr = '# Bitcoin Core config file\n'
	tracking_wallet_name = 'mmgen-tracking-wallet'
	rpc_ports = _nw(8332, 18332, 18443)
	cfg_file = 'bitcoin.conf'
	datadirs = {
		'linux': [g.home_dir,'.bitcoin'],
		'win':   [os.getenv('APPDATA'),'Bitcoin']
	}
	nonstd_datadir = False

	def init_datadir(self):
		if self.network == 'regtest' and not self.test_suite:
			return os.path.join( g.data_dir_root, 'regtest', g.coin.lower() )
		else:
			return super().init_datadir()

	@property
	def network_datadir(self):
		"location of the network's blockchain data and authentication cookie"
		return os.path.join (
			self.datadir, {
				'mainnet': '',
				'testnet': self.testnet_dir,
				'regtest': 'regtest',
			}[self.network] )

	@property
	def auth_cookie_fn(self):
		return os.path.join(self.network_datadir,'.cookie')

	def init_subclass(self):

		if self.network == 'regtest':
			"""
			fall back on hard-coded credentials
			"""
			from .regtest import MMGenRegtest
			self.rpc_user = MMGenRegtest.rpc_user
			self.rpc_password = MMGenRegtest.rpc_password

		self.shared_args = list_gen(
			[f'--datadir={self.datadir}',         self.nonstd_datadir or self.non_dfl_datadir],
			[f'--rpcport={self.rpc_port}'],
			[f'--rpcuser={self.rpc_user}',         self.network == 'regtest'],
			[f'--rpcpassword={self.rpc_password}', self.network == 'regtest'],
			['--testnet',                          self.network == 'testnet'],
			['--regtest',                          self.network == 'regtest'],
		)

		self.coind_args = list_gen(
			['--listen=0'],
			['--keypool=1'],
			['--rpcallowip=127.0.0.1'],
			[f'--rpcbind=127.0.0.1:{self.rpc_port}'],
			['--pid='+self.pidfile,    self.use_pidfile],
			['--daemon',               self.platform == 'linux' and not self.opt.no_daemonize],
			['--fallbackfee=0.0002',   self.coin == 'BTC' and self.network == 'regtest'],
			['--usecashaddr=0',        self.coin == 'BCH'],
			['--mempoolreplacement=1', self.coin == 'LTC'],
			['--txindex=1',            self.coin == 'LTC' or self.network == 'regtest'],
			['--addresstype=bech32',   self.coin == 'LTC' and self.network == 'regtest'],
		)

		self.lockfile = os.path.join(self.network_datadir,'.cookie')

	@property
	def state(self):
		cp = self.cli('getblockcount',silent=True)
		err = cp.stderr.decode()
		if ("error: couldn't connect" in err
			or "error: Could not connect" in err
			or "does not exist" in err ):
			# regtest has no cookie file, so test will always fail
			ret = 'busy' if (self.lockfile and os.path.exists(self.lockfile)) else 'stopped'
		elif cp.returncode == 0:
			ret = 'ready'
		else:
			ret = 'busy'
		if self.debug:
			print(f'State: {ret!r}')
		return ret

	@property
	def stop_cmd(self):
		return self.cli_cmd('stop')

	def set_comment_args(self,rpc,coinaddr,lbl):
		if 'label_api' in rpc.caps:
			return ('setlabel',coinaddr,lbl)
		else:
			# NOTE: this works because importaddress() removes the old account before
			# associating the new account with the address.
			# RPC args: addr,label,rescan[=true],p2sh[=none]
			return ('importaddress',coinaddr,lbl,False)

	def estimatefee_args(self,rpc):
		return (opt.fee_estimate_confs,)

	def sigfail_errmsg(self,e):
		return e.args[0]

class bitcoin_cash_node_daemon(bitcoin_core_daemon):
	daemon_data = _dd('Bitcoin Cash Node', 24010000, '24.1.0')
	exec_fn = 'bitcoind-bchn'
	cli_fn = 'bitcoin-cli-bchn'
	rpc_ports = _nw(8432, 18432, 18543) # use non-standard ports (core+100)
	datadirs = {
		'linux': [g.home_dir,'.bitcoin-bchn'],
		'win':   [os.getenv('APPDATA'),'Bitcoin_ABC']
	}
	cfg_file_hdr = '# Bitcoin Cash Node config file\n'
	nonstd_datadir = True

	def set_comment_args(self,rpc,coinaddr,lbl):
		# bitcoin-{abc,bchn} 'setlabel' RPC is broken, so use old 'importaddress' method to set label
		# Broken behavior: new label is set OK, but old label gets attached to another address
		return ('importaddress',coinaddr,lbl,False)

	def estimatefee_args(self,rpc):
		return () if rpc.daemon_version >= 190100 else (opt.fee_estimate_confs,)

	def sigfail_errmsg(self,e):
		return (
			'This is not the BCH chain.\nRe-run the script without the --coin=bch option.'
				if 'Invalid sighash param' in e.args[0] else
			e.args[0] )

class litecoin_core_daemon(bitcoin_core_daemon):
	# v0.21.2rc5 crashes when mining more than 431 blocks in regtest mode:
	#   CreateNewBlock: TestBlockValidity failed: bad-txns-vin-empty, Transaction check failed
	daemon_data = _dd('Litecoin Core', 210201, '0.21.2.1')
	exec_fn = 'litecoind'
	cli_fn = 'litecoin-cli'
	testnet_dir = 'testnet4'
	rpc_ports = _nw(9332, 19332, 19443)
	cfg_file = 'litecoin.conf'
	datadirs = {
		'linux': [g.home_dir,'.litecoin'],
		'win':   [os.getenv('APPDATA'),'Litecoin']
	}
	cfg_file_hdr = '# Litecoin Core config file\n'
