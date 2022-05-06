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
base_proto.ethereum.daemon: Ethereum base protocol daemon classes
"""

import os

from ...globalvars import g
from ...util import list_gen,get_subclasses
from ...daemon import CoinDaemon,RPCDaemon,_nw,_dd

class ethereum_daemon(CoinDaemon):
	chain_subdirs = _nw('ethereum','goerli','DevelopmentChain')
	base_rpc_port = 8545  # same for all networks!
	base_p2p_port = 30303 # same for all networks!
	daemon_port_offset = 100
	network_port_offsets = _nw(0,10,20)

	def __init__(self,*args,**kwargs):

		if not hasattr(self,'all_daemons'):
			ethereum_daemon.all_daemons = get_subclasses(ethereum_daemon,names=True)

		self.port_offset = (
			self.all_daemons.index(self.id+'_daemon') * self.daemon_port_offset
			+ getattr(self.network_port_offsets,self.network) )

		return super().__init__(*args,**kwargs)

	def get_rpc_port(self):
		return self.base_rpc_port + self.port_offset

	def get_p2p_port(self):
		return self.base_p2p_port + self.port_offset

	def init_datadir(self):
		self.logdir = super().init_datadir()
		return os.path.join(
			self.logdir,
			self.id,
			getattr(self.chain_subdirs,self.network) )

class openethereum_daemon(ethereum_daemon):
	daemon_data = _dd('OpenEthereum', 3003000, '3.3.0')
	version_pat = r'OpenEthereum//v(\d+)\.(\d+)\.(\d+)'
	exec_fn = 'openethereum'
	cfg_file = 'parity.conf'
	datadirs = {
		'linux': [g.home_dir,'.local','share','io.parity.ethereum'],
		'win':   [os.getenv('LOCALAPPDATA'),'Parity','Ethereum']
	}

	def init_subclass(self):

		ld = self.platform == 'linux' and not self.opt.no_daemonize

		self.coind_args = list_gen(
			['--no-ws'],
			['--no-ipc'],
			['--no-secretstore'],
			[f'--jsonrpc-port={self.rpc_port}'],
			[f'--port={self.p2p_port}', self.p2p_port],
			[f'--base-path={self.datadir}', self.non_dfl_datadir],
			[f'--chain={self.proto.chain_name}', self.network!='regtest'],
			[f'--config=dev', self.network=='regtest'], # no presets for mainnet or testnet
			['--mode=offline', self.test_suite or self.network=='regtest'],
			[f'--log-file={self.logfile}', self.non_dfl_datadir],
			['daemon', ld],
			[self.pidfile, ld],
		)

class parity_daemon(openethereum_daemon):
	daemon_data = _dd('Parity', 2007002, '2.7.2')
	version_pat = r'Parity-Ethereum//v(\d+)\.(\d+)\.(\d+)'
	exec_fn = 'parity'

class geth_daemon(ethereum_daemon):
	# bug in v1.10.17 requires --dev to be omitted to initialize blockchain (devnet_init_bug)
	# daemon_data = _dd('Geth', 1010017, '1.10.17')
	daemon_data = _dd('Geth', 1010014, '1.10.14')
	version_pat = r'Geth/v(\d+)\.(\d+)\.(\d+)'
	exec_fn = 'geth'
	use_pidfile = False
	use_threads = True
	datadirs = {
		'linux': [g.home_dir,'.ethereum','geth'],
		'win':   [os.getenv('LOCALAPPDATA'),'Geth'] # FIXME
	}
	avail_opts = ('no_daemonize','online','devnet_init_bug')

	def init_subclass(self):
		self.coind_args = list_gen(
			['--verbosity=0'],
			['--http'],
			['--http.api=eth,web3,txpool'],
			[f'--http.port={self.rpc_port}'],
			[f'--port={self.p2p_port}', self.p2p_port], # geth binds p2p port even with --maxpeers=0
			['--maxpeers=0', not self.opt.online],
			[f'--datadir={self.datadir}', self.non_dfl_datadir],
			['--goerli', self.network=='testnet'],
			['--dev', self.network=='regtest' and not self.opt.devnet_init_bug],
		)

# https://github.com/ledgerwatch/erigon
class erigon_daemon(geth_daemon):
	daemon_data = _dd('Erigon', 2022099099, '2022.99.99')
	version_pat = r'erigon/(\d+)\.(\d+)\.(\d+)'
	exec_fn = 'erigon'
	private_ports = _nw(9090,9091,9092) # testnet and regtest are non-standard
	datadirs = {
		'linux': [g.home_dir,'.local','share','erigon'],
		'win':   [os.getenv('LOCALAPPDATA'),'Erigon'] # FIXME
	}

	def init_subclass(self):
		self.coind_args = list_gen(
			['--verbosity=0'],
			[f'--port={self.p2p_port}', self.p2p_port],
			['--maxpeers=0', not self.opt.online],
			[f'--private.api.addr=127.0.0.1:{self.private_port}'],
			[f'--datadir={self.datadir}', self.non_dfl_datadir],
			['--chain=goerli', self.network=='testnet'],
			['--chain=dev', self.network=='regtest'],
			['--mine', self.network=='regtest'],
		)
		self.rpc_d = erigon_rpcdaemon(
			proto        = self.proto,
			rpc_port     = self.rpc_port,
			private_port = self.private_port,
			test_suite   = self.test_suite,
			datadir      = self.datadir )

	def start(self,quiet=False,silent=False):
		super().start(quiet=quiet,silent=silent)
		self.rpc_d.debug = self.debug
		return self.rpc_d.start(quiet=quiet,silent=silent)

	def stop(self,quiet=False,silent=False):
		self.rpc_d.debug = self.debug
		self.rpc_d.stop(quiet=quiet,silent=silent)
		return super().stop(quiet=quiet,silent=silent)

	@property
	def start_cmds(self):
		return [self.start_cmd,self.rpc_d.start_cmd]

class erigon_rpcdaemon(RPCDaemon):

	master_daemon = 'erigon_daemon'
	rpc_type = 'Erigon'
	exec_fn = 'rpcdaemon'
	use_pidfile = False
	use_threads = True

	def __init__(self,proto,rpc_port,private_port,test_suite,datadir):

		self.proto = proto
		self.test_suite = test_suite

		super().__init__()

		self.network = proto.network
		self.rpc_port = rpc_port
		self.datadir = datadir

		self.daemon_args = list_gen(
			['--verbosity=0'],
			[f'--private.api.addr=127.0.0.1:{private_port}'],
			[f'--http.port={self.rpc_port}'],
			[f'--datadir={self.datadir}'],
			['--http.api=eth,erigon,web3,net,debug,trace,txpool,parity'],
		)
