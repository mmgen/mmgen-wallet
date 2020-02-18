#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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

	debug = False
	wait = True
	use_pidfile = True
	cfg_file = None
	new_console_mswin = False
	ps_pid_mswin = False

	def subclass_init(self): pass

	def exec_cmd_thread(self,cmd,check):
		import threading
		tname = ('exec_cmd','exec_cmd_win_console')[self.platform == 'win' and self.new_console_mswin]
		t = threading.Thread(target=getattr(self,tname),args=(cmd,check))
		t.daemon = True
		t.start()
		Msg_r(' \b') # blocks w/o this...crazy

	def exec_cmd_win_console(self,cmd,check):
		from subprocess import Popen,CREATE_NEW_CONSOLE,STARTUPINFO,STARTF_USESHOWWINDOW,SW_HIDE
		si = STARTUPINFO(dwFlags=STARTF_USESHOWWINDOW,wShowWindow=SW_HIDE)
		p = Popen(cmd,creationflags=CREATE_NEW_CONSOLE,startupinfo=si)
		p.wait()

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
		if self.ps_pid_mswin and self.platform == 'win':
			# TODO: assumes only one running instance of given daemon
			cp = self.run_cmd(['ps','-Wl'],silent=True,check=False)
			for line in cp.stdout.decode().splitlines():
				if self.exec_fn_mswin in line:
					return line.split()[3] # use Windows, not Cygwin, PID
			die(2,'PID for {!r} not found in ps output'.format(ss))
		elif self.use_pidfile:
			return open(self.pidfile).read().strip()
		else:
			return '(unknown)'


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

class MoneroWalletDaemon(Daemon):

	desc = 'RPC daemon'
	net_desc = 'Monero wallet'
	daemon_id = 'xmr'
	network = 'wallet RPC'
	new_console_mswin = True
	exec_fn_mswin = 'monero-wallet-rpc.exe'
	ps_pid_mswin = True

	def __init__(self,wallet_dir,test_suite=False):
		self.platform = g.platform
		self.wallet_dir = wallet_dir
		if test_suite:
			self.datadir = os.path.join('test','monero-wallet-rpc')
			self.rpc_port = 13142
		else:
			self.datadir = 'monero-wallet-rpc'
			self.rpc_port = 13131
		self.daemon_port = CoinDaemon('xmr',test_suite=test_suite).rpc_port
		self.pidfile = os.path.join(self.datadir,'monero-wallet-rpc.pid')
		self.logfile = os.path.join(self.datadir,'monero-wallet-rpc.log')

		if self.platform == 'win':
			self.use_pidfile = False

		if not g.monero_wallet_rpc_password:
			die(1,
				'You must set your Monero wallet RPC password.\n' +
				'This can be done on the command line, with the --monero-wallet-rpc-password\n' +
				"option (insecure, not recommended), or by setting 'monero_wallet_rpc_password'\n" +
				"in the MMGen config file." )

	@property
	def start_cmd(self):
		cmd = [
			'monero-wallet-rpc',
			'--daemon-port={}'.format(self.daemon_port),
			'--rpc-bind-port={}'.format(self.rpc_port),
			'--wallet-dir='+self.wallet_dir,
			'--log-file='+self.logfile,
			'--rpc-login={}:{}'.format(g.monero_wallet_rpc_user,g.monero_wallet_rpc_password) ]
		if self.platform == 'linux':
			cmd += ['--pidfile={}'.format(self.pidfile),'--detach']
		return cmd

	@property
	def state(self):
		from mmgen.rpc import MoneroWalletRPCConnection
		try:
			MoneroWalletRPCConnection(
				g.monero_wallet_rpc_host,
				self.rpc_port,
				g.monero_wallet_rpc_user,
				g.monero_wallet_rpc_password).get_version()
			return 'ready'
		except:
			return 'stopped'

	@property
	def stop_cmd(self):
		return ['kill','-Wf',self.pid] if self.platform == 'win' else ['kill',self.pid]

class CoinDaemon(Daemon):
	cfg_file_hdr = ''
	subclasses_must_implement = ('state','stop_cmd')

	network_ids = ('btc','btc_tn','btc_rt','bch','bch_tn','bch_rt','ltc','ltc_tn','ltc_rt','xmr','eth','etc')

	cd = namedtuple('daemon_data',
				['coin','cls_pfx','coind_exec','cli_exec','cfg_file','dfl_rpc','dfl_rpc_tn','dfl_rpc_rt'])
	daemon_ids = {
		'btc': cd('Bitcoin',         'Bitcoin', 'bitcoind',    'bitcoin-cli', 'bitcoin.conf',  8332,18332,18444),
		'bch': cd('Bcash',           'Bitcoin', 'bitcoind-abc','bitcoin-cli', 'bitcoin.conf',  8442,18442,18553),# MMGen RPC dfls
		'ltc': cd('Litecoin',        'Bitcoin', 'litecoind',   'litecoin-cli','litecoin.conf', 9332,19332,19444),
		'xmr': cd('Monero',          'Monero',  'monerod',     'monerod',     'bitmonero.conf',18081,None,None),
		'eth': cd('Ethereum',        'Ethereum','parity',      'parity',      'parity.conf',   8545,None,None),
		'etc': cd('Ethereum Classic','Ethereum','parity',      'parity',      'parity.conf',   8545,None,None)
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

		if network_id.endswith('_rt'):
			network = 'regtest'
			daemon_id = network_id[:-3]
		elif network_id.endswith('_tn'):
			network = 'testnet'
			daemon_id = network_id[:-3]
		else:
			network = 'mainnet'
			daemon_id = network_id

		me = Daemon.__new__(globals()[cls.daemon_ids[daemon_id].cls_pfx+'Daemon'])
		me.network_id = network_id
		me.network = network
		me.daemon_id = daemon_id

		me.desc = 'daemon'
		if network == 'regtest':
			me.desc = 'regtest daemon'
			if test_suite:
				rel_datadir = os.path.join('test','data_dir','regtest',daemon_id)
			else:
				me.datadir = os.path.join(g.data_dir_root,'regtest',daemon_id)
		elif test_suite:
			me.desc = 'test suite daemon'
			rel_datadir = os.path.join('test','daemons',daemon_id)
		else:
			from mmgen.protocol import CoinProtocol
			me.datadir = CoinProtocol(daemon_id,False).daemon_data_dir

		if test_suite:
			me.datadir = os.path.abspath(os.path.join(os.getcwd(),rel_datadir))

		me.port_shift = 1237 if test_suite else 0
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

	exec_fn_mswin = 'monerod.exe'
	ps_pid_mswin = True
	new_console_mswin = True

	def subclass_init(self):
		if self.platform == 'win':
			self.use_pidfile = False

	@property
	def shared_args(self):
		return ['--zmq-rpc-bind-port={}'.format(self.rpc_port+1),'--rpc-bind-port={}'.format(self.rpc_port)]

	@property
	def coind_args(self):
		cmd = [
			'--bg-mining-enable',
			'--data-dir={}'.format(self.datadir),
			'--offline' ]
		if self.platform == 'linux':
			cmd += ['--pidfile={}'.format(self.pidfile),'--detach']
		return cmd

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
		if self.platform == 'win':
			return ['kill','-Wf',self.pid]
		else:
			return [self.coind_exec] + self.shared_args + ['exit']

class EthereumDaemon(CoinDaemon):

	exec_fn_mswin = 'parity.exe'
	ps_pid_mswin = True

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

CoinDaemon.check_implement()
