#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.btc.daemon: Bitcoin base protocol daemon classes
"""

import os

from ...cfg import gc
from ...util import list_gen
from ...daemon import CoinDaemon, _nw, _dd

class bitcoin_core_daemon(CoinDaemon):
	daemon_data = _dd('Bitcoin Core', 280000, '28.0.0')
	exec_fn = 'bitcoind'
	cli_fn = 'bitcoin-cli'
	testnet_dir = 'testnet3'
	cfg_file_hdr = '# Bitcoin Core config file\n'
	rpc_ports = _nw(8332, 18332, 18443)
	cfg_file = 'bitcoin.conf'
	nonstd_datadir = False
	datadirs = {
		'linux': [gc.home_dir, '.bitcoin'],
		'darwin': [gc.home_dir, 'Library', 'Application Support', 'Bitcoin'],
		'win32': [os.getenv('APPDATA'), 'Bitcoin']
	}
	avail_opts = ('no_daemonize', 'online', 'bdb_wallet')

	def init_datadir(self):
		if self.network == 'regtest' and not self.test_suite:
			return os.path.join(self.cfg.data_dir_root, 'regtest', self.cfg.coin.lower())
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
			}[self.network])

	@property
	def auth_cookie_fn(self):
		return os.path.join(self.network_datadir, '.cookie')

	def init_subclass(self):

		if self.network == 'regtest':
			# fall back on hard-coded credentials:
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
			['--daemon',               self.platform in ('linux', 'darwin') and not self.opt.no_daemonize],
			['--fallbackfee=0.0002',   self.coin == 'BTC' and self.network == 'regtest'],
			['--deprecatedrpc=create_bdb', self.coin == 'BTC' and self.opt.bdb_wallet],
			['--mempoolreplacement=1', self.coin == 'LTC'],
			['--txindex=1',            self.coin == 'LTC' or self.network == 'regtest'],
			['--addresstype=bech32',   self.coin == 'LTC' and self.network == 'regtest'],
		)

		self.lockfile = os.path.join(self.network_datadir, '.cookie')

	@property
	def state(self):
		cp = self.cli('getblockcount', silent=True)
		err = cp.stderr.decode()
		if ("error: couldn't connect" in err
			or "error: Could not connect" in err
			or "does not exist" in err):
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

	def set_comment_args(self, rpc, coinaddr, lbl):
		if 'label_api' in rpc.caps:
			return ('setlabel', coinaddr, lbl)
		else:
			# NOTE: this works because importaddress() removes the old account before
			# associating the new account with the address.
			# RPC args: addr, label, rescan[=true], p2sh[=none]
			return ('importaddress', coinaddr, lbl, False)

	def estimatefee_args(self, rpc):
		return (self.cfg.fee_estimate_confs,)

	def sigfail_errmsg(self, e):
		return e.args[0]

class bitcoin_cash_node_daemon(bitcoin_core_daemon):
	daemon_data = _dd('Bitcoin Cash Node', 27010000, '27.1.0')
	exec_fn = 'bitcoind-bchn'
	cli_fn = 'bitcoin-cli-bchn'
	rpc_ports = _nw(8432, 18432, 18543) # use non-standard ports (core+100)
	cfg_file_hdr = '# Bitcoin Cash Node config file\n'
	nonstd_datadir = True
	datadirs = {
		'linux': [gc.home_dir, '.bitcoin-bchn'],
		'darwin': [gc.home_dir, 'Library', 'Application Support', 'Bitcoin-Cash-Node'],
		'win32': [os.getenv('APPDATA'), 'Bitcoin-Cash-Node']
	}

	def set_comment_args(self, rpc, coinaddr, lbl):
		# bitcoin-{abc, bchn} 'setlabel' RPC is broken, so use old 'importaddress' method to set label
		# Broken behavior: new label is set OK, but old label gets attached to another address
		return ('importaddress', coinaddr, lbl, False)

	def estimatefee_args(self, rpc):
		return () if rpc.daemon_version >= 190100 else (self.cfg.fee_estimate_confs,)

	def sigfail_errmsg(self, e):
		return (
			'This is not the BCH chain.\nRe-run the script without the --coin=bch option.'
				if 'Invalid sighash param' in e.args[0] else
			e.args[0])

class litecoin_core_daemon(bitcoin_core_daemon):
	# v0.21.2rc5 crashes when mining more than 431 blocks in regtest mode:
	#   CreateNewBlock: TestBlockValidity failed: bad-txns-vin-empty, Transaction check failed
	daemon_data = _dd('Litecoin Core', 210400, '0.21.4')
	exec_fn = 'litecoind'
	cli_fn = 'litecoin-cli'
	testnet_dir = 'testnet4'
	rpc_ports = _nw(9332, 19332, 19443)
	cfg_file = 'litecoin.conf'
	cfg_file_hdr = '# Litecoin Core config file\n'
	datadirs = {
		'linux': [gc.home_dir, '.litecoin'],
		'darwin': [gc.home_dir, 'Library', 'Application Support', 'Litecoin'],
		'win32': [os.getenv('APPDATA'), 'Litecoin']
	}
