#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>
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
daemon.py:  Daemon control interface for the MMGen suite
"""

import shutil
from subprocess import run,PIPE
from collections import namedtuple
from mmgen.exception import *
from mmgen.common import *

class Daemon(MMGenObject):

	subclasses_must_implement = ('state','stop_cmd')
	debug = False
	wait = True
	use_pidfile = True
	cfg_file = None

	def subclass_init(self): pass

	def exec_cmd_thread(self,cmd,check):
		import threading
		t = threading.Thread(target=self.exec_cmd,args=(cmd,check))
		t.daemon = True
		t.start()
		Msg_r(' \b') # blocks w/o this...crazy

	def exec_cmd(self,cmd,check):
		cp = run(cmd,check=False,stdout=PIPE,stderr=PIPE)
		if check and cp.returncode != 0:
			raise MMGenCalledProcessError(cp)
		return cp

	def run_cmd(self,cmd,silent=False,check=True,is_daemon=False):
		if is_daemon and not silent:
			msg('Starting {} {}'.format(self.net_desc,self.desc))

		if self.debug:
			msg('\nExecuting: {}'.format(' '.join(cmd)))

		if self.platform == 'win' and is_daemon:
			cp = self.exec_cmd_thread(cmd,check)
		else:
			cp = self.exec_cmd(cmd,check)
		if cp:
			out = cp.stdout.decode().rstrip()
			err = cp.stderr.decode().rstrip()
			if out and (self.debug or not silent):
				msg(out)
			if err and (self.debug or (cp.returncode and not silent)):
				msg(err)

		return cp

	@property
	def pid(self):
		return open(self.pidfile).read().strip() if self.use_pidfile else '(unknown)'

	def cmd(self,action,*args,**kwargs):
		return getattr(self,action)(*args,**kwargs)

	def do_start(self,silent=False):
		if not silent:
			msg('Starting {} {}'.format(self.net_desc,self.desc))
		return self.run_cmd(self.start_cmd,silent=True,is_daemon=True)

	def do_stop(self,silent=False):
		if not silent:
			msg('Stopping {} {}'.format(self.net_desc,self.desc))
		return self.run_cmd(self.stop_cmd,silent=True)

	def cli(self,*cmds,silent=False,check=True):
		return self.run_cmd(self.cli_cmd(*cmds),silent=silent,check=check)

	def start(self,silent=False):
		if self.is_ready:
			if not silent:
				m = '{} {} already running with pid {}'
				msg(m.format(self.net_desc,self.desc,self.pid))
		else:
			os.makedirs(self.datadir,exist_ok=True)
			if self.cfg_file:
				open('{}/{}'.format(self.datadir,self.cfg_file),'w').write(self.cfg_file_hdr)
			if self.use_pidfile and os.path.exists(self.pidfile):
				# Parity just overwrites the data in an existing pidfile, leading to
				# interesting consequences.
				os.unlink(self.pidfile)
			ret = self.do_start(silent=silent)
			if self.wait:
				self.wait_for_state('ready')
			return ret

	def stop(self,silent=False):
		if self.is_ready:
			ret = self.do_stop(silent=silent)
			if self.wait:
				self.wait_for_state('stopped')
			return ret
		else:
			if not silent:
				msg('{} {} not running'.format(self.net_desc,self.desc))
		# rm -rf $datadir

	def wait_for_state(self,req_state):
		for i in range(200):
			if self.state == req_state:
				return True
			time.sleep(0.2)
		else:
			die(2,'Daemon wait timeout for {} {} exceeded'.format(self.daemon_id.upper(),self.network))

	@property
	def is_ready(self):
		return self.state == 'ready'

	@classmethod
	def check_implement(cls):
		m = 'required method {}() missing in class {}'
		for subcls in cls.__subclasses__():
			for k in cls.subclasses_must_implement:
				assert k in subcls.__dict__, m.format(k,subcls.__name__)

class CoinDaemon(Daemon):
	cfg_file_hdr = ''

	network_ids = ('btc','btc_tn','btc_rt','bch','bch_tn','bch_rt','ltc','ltc_tn','ltc_rt','xmr','eth','etc')

	cd = namedtuple('daemon_data',['coin','coind_exec','cli_exec','conf_file','dfl_rpc','dfl_rpc_tn','dfl_rpc_rt'])
	daemon_ids = {
		'btc': cd('Bitcoin',         'bitcoind',    'bitcoin-cli', 'bitcoin.conf',  8333,18333,18444),
		'bch': cd('Bcash',           'bitcoind-abc','bitcoin-cli', 'bitcoin.conf',  8442,18442,18553),# MMGen RPC dfls
		'ltc': cd('Litecoin',        'litecoind',   'litecoin-cli','litecoin.conf', 9333,19335,19446),
		'xmr': cd('Monero',          'monerod',     'monerod',     'bitmonero.conf',18082,None,None),
		'eth': cd('Ethereum',        'parity',      'parity',      'parity.conf',   8545,None,None),
		'etc': cd('Ethereum Classic','parity',      'parity',      'parity.conf',   8545,None,None)
	}

	testnet_arg = []
	coind_args = []
	cli_args = []
	shared_args = []
	coind_cmd = []

	coin_specific_coind_args = []
	coin_specific_cli_args = []
	coin_specific_shared_args = []

	usr_coind_args = []
	usr_cli_args = []
	usr_shared_args = []

	def __new__(cls,network_id,test_suite=False):
		network_id = network_id.lower()
		assert network_id in cls.network_ids, '{!r}: invalid network ID'.format(network_id)

		if test_suite:
			rel_datadir = os.path.join('test','daemons')
			desc = 'test suite daemon'
		elif not network_id.endswith('_rt'):
			raise RuntimeError('only test suite and regtest supported for CoinDaemon')

		if network_id.endswith('_tn'):
			daemon_id = network_id[:-3]
			network = 'testnet'
		elif network_id.endswith('_rt'):
			daemon_id = network_id[:-3]
			network = 'regtest'
			desc = 'regtest daemon'
			if test_suite:
				rel_datadir = os.path.join('test','data_dir','regtest')
			else:
				rel_datadir = os.path.join(g.data_dir_root,'regtest')
		else:
			daemon_id = network_id
			network = 'mainnet'

		me = MMGenObject.__new__(
			MoneroDaemon        if daemon_id == 'xmr'
			else EthereumDaemon if daemon_id in ('eth','etc')
			else BitcoinDaemon )

		if test_suite:
			me.datadir = os.path.abspath(os.path.join(os.getcwd(),rel_datadir,daemon_id))
			me.port_shift = 1237
		else:
			me.datadir = os.path.join(rel_datadir,daemon_id)
			me.port_shift = 0

		me.network_id = network_id
		me.daemon_id = daemon_id
		me.network = network
		me.desc = desc
		me.platform = g.platform
		return me

	def __init__(self,network_id,test_suite=False):

		self.pidfile = '{}/{}-daemon.pid'.format(self.datadir,self.network)

		for k in self.daemon_ids[self.daemon_id]._fields:
			setattr(self,k,getattr(self.daemon_ids[self.daemon_id],k))

		self.rpc_port = {
				'mainnet': self.dfl_rpc,
				'testnet': self.dfl_rpc_tn,
				'regtest': self.dfl_rpc_rt,
			}[self.network] + self.port_shift

		self.net_desc = '{} {}'.format(self.coin,self.network)
		self.subclass_init()

	@property
	def start_cmd(self):
		return ([self.coind_exec]
				+ self.testnet_arg
				+ self.coind_args
				+ self.shared_args
				+ self.coin_specific_coind_args
				+ self.coin_specific_shared_args
				+ self.usr_coind_args
				+ self.usr_shared_args
				+ self.coind_cmd )

	def cli_cmd(self,*cmds):
		return ([self.cli_exec]
				+ self.testnet_arg
				+ self.cli_args
				+ self.shared_args
				+ self.coin_specific_cli_args
				+ self.coin_specific_shared_args
				+ self.usr_cli_args
				+ self.usr_shared_args
				+ list(cmds))

class BitcoinDaemon(CoinDaemon):
	cfg_file_hdr = '# BitcoinDaemon config file\n'

	def subclass_init(self):

		if self.platform == 'win' and self.daemon_id == 'bch':
			self.use_pidfile = False

		if self.network=='testnet':
			self.testnet_arg = ['--testnet']

		self.shared_args = [
			'--datadir={}'.format(self.datadir),
			'--rpcport={}'.format(self.rpc_port) ]

		self.coind_args = [
			'--listen=0',
			'--keypool=1',
			'--rpcallowip=127.0.0.1',
			'--rpcbind=127.0.0.1:{}'.format(self.rpc_port) ]

		if self.use_pidfile:
			self.coind_args += ['--pid='+self.pidfile]

		if self.platform == 'linux':
			self.coind_args += ['--daemon']

		if self.daemon_id == 'bch':
			self.coin_specific_coind_args = ['--usecashaddr=0']
		elif self.daemon_id == 'ltc':
			self.coin_specific_coind_args = ['--mempoolreplacement=1']

	@property
	def state(self):
		cp = self.cli('getblockcount',silent=True,check=False)
		err = cp.stderr.decode()
		if ("error: couldn't connect" in err
			or "error: Could not connect" in err
			or "does not exist" in err ):
			return 'stopped'
		elif cp.returncode == 0:
			return 'ready'
		else:
			return 'busy'

	@property
	def stop_cmd(self):
		return self.cli_cmd('stop')

class MoneroDaemon(CoinDaemon):

	@property
	def shared_args(self):
		return ['--zmq-rpc-bind-port={}'.format(self.rpc_port+1),'--rpc-bind-port={}'.format(self.rpc_port)]

	@property
	def coind_args(self):
		return ['--bg-mining-enable',
				'--pidfile={}'.format(self.pidfile),
				'--data-dir={}'.format(self.datadir),
				'--detach',
				'--offline' ]

	@property
	def state(self):
		cp = self.run_cmd(
			[self.coind_exec]
			+ self.shared_args
			+ ['status'],
			silent=True,
			check=False )
		return 'stopped' if 'Error:' in cp.stdout.decode() else 'ready'

	@property
	def stop_cmd(self):
		return [self.coind_exec] + self.shared_args + ['exit']

class EthereumDaemon(CoinDaemon):

	def subclass_init(self):
		# defaults:
		# linux: $HOME/.local/share/io.parity.ethereum/chains/DevelopmentChain
		# win:   $LOCALAPPDATA/Parity/Ethereum/chains/DevelopmentChain
		self.chaindir = os.path.join(self.datadir,'devchain')
		shutil.rmtree(self.chaindir,ignore_errors=True)

	@property
	def coind_cmd(self):
		return ['daemon',self.pidfile] if self.platform == 'linux' else []

	@property
	def coind_args(self):
		return ['--ports-shift={}'.format(self.port_shift),
				'--base-path={}'.format(self.chaindir),
				'--config=dev',
				'--log-file={}'.format(os.path.join(self.datadir,'parity.log')) ]

	@property
	def state(self):
		from mmgen.rpc import EthereumRPCConnection
		try:
			conn = EthereumRPCConnection('localhost',self.rpc_port,socket_timeout=0.2)
		except:
			return 'stopped'

		ret = conn.eth_chainId(on_fail='return')

		return ('stopped','ready')[ret == '0x11']

	@property
	def stop_cmd(self):
		return ['kill','-Wf',self.pid] if self.platform == 'win' else ['kill',self.pid]

	@property
	def pid(self): # TODO: distinguish between ETH and ETC
		if self.platform == 'win':
			cp = self.run_cmd(['ps','-Wl'],silent=True,check=False)
			for line in cp.stdout.decode().splitlines():
				if 'parity.exe' in line:
					return line.split()[3] # use Windows, not Cygwin, PID
		else:
			return super().pid

CoinDaemon.check_implement()
