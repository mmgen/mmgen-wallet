#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2021 The MMGen Project <mmgen@tuta.io>
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
from .exception import *
from .common import *

class Daemon(MMGenObject):

	desc = 'daemon'
	debug = False
	wait = True
	use_pidfile = True
	cfg_file = None
	new_console_mswin = False
	ps_pid_mswin = False
	lockfile = None
	avail_opts = ()
	avail_flags = () # like opts, but can be added or removed after instantiation

	def __init__(self):
		self.opts = []
		self._flags = []

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
		if self.debug:
			print(cp)
		if check and cp.returncode != 0:
			raise MMGenCalledProcessError(cp)
		return cp

	def run_cmd(self,cmd,silent=False,check=True,is_daemon=False):
		if is_daemon and not silent:
			msg('Starting {} {} on port {}'.format(self.net_desc,self.desc,self.rpc_port))

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
			msg('Starting {} {} on port {}'.format(self.net_desc,self.desc,self.rpc_port))
		return self.run_cmd(self.start_cmd,silent=True,is_daemon=True)

	def do_stop(self,silent=False):
		if not silent:
			msg('Stopping {} {} on port {}'.format(self.net_desc,self.desc,self.rpc_port))
		return self.run_cmd(self.stop_cmd,silent=True)

	def cli(self,*cmds,silent=False,check=True):
		return self.run_cmd(self.cli_cmd(*cmds),silent=silent,check=check)

	def start(self,silent=False):
		if self.state == 'ready':
			if not silent:
				m = '{} {} already running with pid {}'
				msg(m.format(self.net_desc,self.desc,self.pid))
			return

		self.wait_for_state('stopped')

		os.makedirs(self.datadir,exist_ok=True)
		if self.cfg_file and not 'keep_cfg_file' in self.flags:
			open('{}/{}'.format(self.datadir,self.cfg_file),'w').write(self.cfg_file_hdr)

		if self.use_pidfile and os.path.exists(self.pidfile):
			# OpenEthereum just overwrites the data in the existing pidfile without zeroing it first,
			# leading to interesting consequences.
			os.unlink(self.pidfile)

		for i in range(20):
			try: ret = self.do_start(silent=silent)
			except FileNotFoundError as e:
				die(e.errno,e.strerror)
			except: pass
			else: break
			time.sleep(1)
		else:
			die(2,'Unable to start daemon')

		if self.wait:
			self.wait_for_state('ready')

		return ret

	def stop(self,silent=False):
		if self.state == 'ready':
			ret = self.do_stop(silent=silent)
			if self.wait:
				self.wait_for_state('stopped')
			return ret
		else:
			if not silent:
				msg('{} {} on port {} not running'.format(self.net_desc,self.desc,self.rpc_port))

	def restart(self,silent=False):
		self.stop(silent=silent)
		return self.start(silent=silent)

	def test_socket(self,host,port,timeout=10):
		import socket
		try: socket.create_connection((host,port),timeout=timeout).close()
		except: return False
		else: return True

	def wait_for_state(self,req_state):
		for i in range(300):
			if self.state == req_state:
				return True
			time.sleep(0.2)
		else:
			m = 'Wait for state {!r} timeout exceeded for daemon {} {} (port {})'
			die(2,m.format(req_state,self.daemon_id.upper(),self.network,self.rpc_port))

	@classmethod
	def check_implement(cls):
		m = 'required method {}() missing in class {}'
		for subcls in cls.__subclasses__():
			for k in cls.subclasses_must_implement:
				assert k in subcls.__dict__, m.format(k,subcls.__name__)

	@property
	def flags(self):
		return self._flags

	def add_flag(self,val):
		if val not in self.avail_flags:
			m = '{!r}: unrecognized flag (available options: {})'
			die(1,m.format(val,self.avail_flags))
		if val in self._flags:
			die(1,'Flag {!r} already set'.format(val))
		self._flags.append(val)

	def remove_flag(self,val):
		if val not in self.avail_flags:
			m = '{!r}: unrecognized flag (available options: {})'
			die(1,m.format(val,self.avail_flags))
		if val not in self._flags:
			die(1,'Flag {!r} not set, so cannot be removed'.format(val))
		self._flags.remove(val)

	def remove_datadir(self):
		if self.state == 'stopped':
			try: # exception handling required for MSWin/MSYS2
				run(['/bin/rm','-rf',self.datadir])
			except:
				pass
		else:
			msg(f'Cannot remove {self.datadir!r} - daemon is not stopped')

class MoneroWalletDaemon(Daemon):

	desc = 'RPC daemon'
	net_desc = 'Monero wallet'
	daemon_id = 'xmr'
	network = 'wallet RPC'
	new_console_mswin = True
	exec_fn_mswin = 'monero-wallet-rpc.exe'
	ps_pid_mswin = True

	def __init__(self, wallet_dir,
			test_suite  = False,
			host        = None,
			user        = None,
			passwd      = None,
			daemon_addr = None,
			proxy       = None,
			port_shift  = None,
			datadir     = None,
			testnet     = False ):

		super().__init__()
		self.platform = g.platform
		self.wallet_dir = wallet_dir
		self.rpc_port = 13142 if test_suite else 13131
		if port_shift:
			self.rpc_port += port_shift

		bn = 'monero-wallet-rpc'
		id_str = f'{bn}-{self.rpc_port}'
		self.datadir = os.path.join(datadir or ('','test')[test_suite], bn)
		self.pidfile = os.path.join(self.datadir,id_str+'.pid')
		self.logfile = os.path.join(self.datadir,id_str+'.log')

		self.proxy = proxy
		self.daemon_addr = daemon_addr
		self.daemon_port = None if daemon_addr else CoinDaemon('xmr',test_suite=test_suite).rpc_port

		if self.platform == 'win':
			self.use_pidfile = False

		self.host = host or g.monero_wallet_rpc_host
		self.user = user or g.monero_wallet_rpc_user
		self.passwd = passwd or g.monero_wallet_rpc_password

		assert self.host
		assert self.user
		if not self.passwd:
			die(1,
				'You must set your Monero wallet RPC password.\n' +
				'This can be done on the command line, with the --monero-wallet-rpc-password\n' +
				"option (insecure, not recommended), or by setting 'monero_wallet_rpc_password'\n" +
				"in the MMGen config file." )

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
			['--detach',                             not 'no_daemonize' in self.opts],
			['--testnet',                            testnet],
		)

		self.usr_daemon_args = []

	@property
	def start_cmd(self):
		return (['monero-wallet-rpc'] + self.daemon_args + self.usr_daemon_args )

	@property
	def state(self):
		return 'ready' if self.test_socket('localhost',self.rpc_port) else 'stopped'
		# TBD:
		if not self.test_socket(self.host,self.rpc_port):
			return 'stopped'
		from .rpc import MoneroWalletRPCClient
		try:
			MoneroWalletRPCClient(
				self.host,
				self.rpc_port,
				self.user,
				self.passwd).call('get_version')
			return 'ready'
		except:
			return 'stopped'

	@property
	def stop_cmd(self):
		return ['kill','-Wf',self.pid] if self.platform == 'win' else ['kill',self.pid]

class CoinDaemon(Daemon):
	cfg_file_hdr = ''
	subclasses_must_implement = ('state','stop_cmd')
	avail_flags = ('keep_cfg_file',)
	avail_opts = ('no_daemonize','online')
	datadir_is_subdir = False
	data_subdir = ''

	network_ids = (
		'btc','btc_tn','btc_rt',
		'bch','bch_tn','bch_rt',
		'ltc','ltc_tn','ltc_rt',
		'xmr','xmr_tn',
		'eth','etc'
	)

	cd = namedtuple('daemon_data', [
		'id',
		'coin',
		'cls_pfx',
		'coind_name',
		'coind_version', 'coind_version_str', # latest tested version
		'coind_exec',
		'cli_exec',
		'cfg_file',
		'testnet_dir',
		'dfl_rpc',
		'dfl_rpc_tn',
		'dfl_rpc_rt' ])

	daemon_ids = {
		'btc': cd(
			'bitcoin_core',
			'Bitcoin',
			'Bitcoin',
			'Bitcoin Core', 210000, '0.21.0',
			'bitcoind',
			'bitcoin-cli',
			'bitcoin.conf',
			'testnet3',
			8332, 18332, 18444),
		'bch': cd(
			'bitcoin_cash_node',
			'BitcoinCashNode',
			'Bitcoin',
			'Bitcoin Cash Node', 22020000, '22.2.0',
			'bitcoind-bchn',
			'bitcoin-cli-bchn',
			'bitcoin.conf',
			'testnet3',
			8442, 18442, 18553), # for BCH we use non-standard RPC ports
		'ltc': cd(
			'litecoin_core',
			'Litecoin',
			'Bitcoin',
			'Litecoin Core', 180100, '0.18.1',
			'litecoind',
			'litecoin-cli',
			'litecoin.conf',
			'testnet4',
			9332, 19332, 19444),
		'xmr': cd(
			'monerod',
			'Monero',
			'Monero',
			'Monero', 'N/A', 'N/A',
			'monerod',
			'monerod',
			'bitmonero.conf',
			'testnet',
			18081, 28081, None),
		'eth': cd(
			'openethereum',
			'Ethereum',
			'Ethereum',
			'OpenEthereum', 3000001, '3.0.1',
			'openethereum',
			'openethereum',
			'parity.conf',
			None,
			8545, 8545, 8545),
		'etc': cd(
			'openethereum',
			'Ethereum Classic',
			'Ethereum',
			'OpenEthereum', 3000001, '3.0.1',
			'openethereum',
			'openethereum',
			'parity.conf',
			None,
			8545, 8545, 8545)
	}

	dfl_datadirs = {
		'linux': {
			'btc': [g.home_dir,'.bitcoin'],
			'bch': [g.home_dir,'.bitcoin-bchn'],
			'ltc': [g.home_dir,'.litecoin'],
			'xmr': [g.home_dir,'.bitmonero'],
			'eth': [g.home_dir,'.local','share','io.parity.ethereum'],
			'etc': [g.home_dir,'.local','share','io.parity.ethereum'],
		},
		'win': {
			'btc': [os.getenv('APPDATA'),'Bitcoin'],
			'bch': [os.getenv('APPDATA'),'Bitcoin_ABC'],
			'ltc': [os.getenv('APPDATA'),'Litecoin'],
			'xmr': ['/','c','ProgramData','bitmonero'],
			'eth': [g.home_dir,'.local','share','io.parity.ethereum'],
			'etc': [g.home_dir,'.local','share','io.parity.ethereum'],
		},
	}

	def __new__(cls,
			network_id = None,
			test_suite = False,
			flags      = None,
			proto      = None,
			opts       = None,
			port_shift = None,
			datadir    = None ):

		assert network_id or proto,        'CoinDaemon_chk1'
		assert not (network_id and proto), 'CoinDaemon_chk2'

		if proto:
			network_id = proto.network_id
			network    = proto.network
			daemon_id  = proto.coin.lower()
		else:
			network_id = network_id.lower()
			assert network_id in cls.network_ids, f'{network_id!r}: invalid network ID'
			from mmgen.protocol import CoinProtocol
			daemon_id,network = CoinProtocol.Base.parse_network_id(network_id)

		me = Daemon.__new__(globals()[cls.daemon_ids[daemon_id].cls_pfx+'Daemon'])
		me.network_id = network_id
		me.network = network
		me.daemon_id = daemon_id

		return me

	def __init__(self,
			network_id = None,
			test_suite = False,
			flags      = None,
			proto      = None,
			opts       = None,
			port_shift = None,
			datadir    = None ):

		super().__init__()

		self.shared_args = []
		self.usr_coind_args = []
		self.platform = g.platform

		if opts:
			if type(opts) not in (list,tuple):
				die(1,f'{opts!r}: illegal value for opts (must be list or tuple)')
			for o in opts:
				if o not in self.avail_opts:
					die(1,f'{o!r}: unrecognized opt')
			self.opts = list(opts)

		if flags:
			if type(flags) not in (list,tuple):
				die(1,f'{flags!r}: illegal value for flags (must be list or tuple)')
			for flag in flags:
				self.add_flag(flag)

		for k in self.daemon_ids[self.daemon_id]._fields:
			setattr(self,k,getattr(self.daemon_ids[self.daemon_id],k))

		if self.network == 'regtest':
			self.desc = 'regtest daemon'
			if test_suite:
				rel_datadir = os.path.join(
					'test',
					'data_dir{}'.format('-α' if g.debug_utf8 else ''),
					'regtest',
					self.daemon_id )
			else:
				dfl_datadir = os.path.join(g.data_dir_root,'regtest',self.daemon_id)
		elif test_suite:
			self.desc = 'test suite daemon'
			rel_datadir = os.path.join('test','daemons',self.daemon_id)
		else:
			dfl_datadir = os.path.join( *self.dfl_datadirs[g.platform][self.daemon_id] )


		if test_suite:
			dfl_datadir = os.path.join(os.getcwd(),rel_datadir)

		# user-set values take precedence
		datadir = datadir or g.daemon_data_dir or dfl_datadir

		self.datadir = os.path.abspath(datadir)

		if self.network == 'testnet' and self.testnet_dir:
			self.data_subdir = self.testnet_dir
			if self.datadir_is_subdir:
				self.datadir = os.path.join(self.datadir,self.testnet_dir)

		self.port_shift = (1237 if test_suite else 0) + (port_shift or 0)
		self.rpc_port = {
				'mainnet': self.dfl_rpc,
				'testnet': self.dfl_rpc_tn,
				'regtest': self.dfl_rpc_rt,
			}[self.network] + self.port_shift

		if g.rpc_port: # user-set global overrides everything else
			self.rpc_port = g.rpc_port

		self.pidfile = '{}/{}-daemon-{}.pid'.format(self.datadir,self.network,self.rpc_port)
		self.net_desc = '{} {}'.format(self.coin,self.network)
		self.subclass_init()

	@property
	def start_cmd(self):
		return ([self.coind_exec]
				+ self.coind_args
				+ self.shared_args
				+ self.usr_coind_args )

	def cli_cmd(self,*cmds):
		return ([self.cli_exec]
				+ self.shared_args
				+ list(cmds) )

class BitcoinDaemon(CoinDaemon):
	cfg_file_hdr = '# BitcoinDaemon config file\n'
	tracking_wallet_name = 'mmgen-tracking-wallet'

	def subclass_init(self):

		if self.platform == 'win' and self.daemon_id == 'bch':
			self.use_pidfile = False

		from mmgen.regtest import MMGenRegtest
		self.shared_args = list_gen(
			[f'--datadir={self.datadir}'],
			[f'--rpcport={self.rpc_port}'],
			[f'--rpcuser={MMGenRegtest.rpc_user}',         self.network == 'regtest'],
			[f'--rpcpassword={MMGenRegtest.rpc_password}', self.network == 'regtest'],
			['--testnet',                                  self.network == 'testnet'],
			['--regtest',                                  self.network == 'regtest'],
		)

		self.coind_args = list_gen(
			['--listen=0'],
			['--keypool=1'],
			['--rpcallowip=127.0.0.1'],
			[f'--rpcbind=127.0.0.1:{self.rpc_port}'],
			['--pid='+self.pidfile,    self.use_pidfile],
			['--daemon',               self.platform == 'linux' and not 'no_daemonize' in self.opts],
			['--fallbackfee=0.0002',   self.daemon_id == 'btc' and self.network == 'regtest'],
			['--usecashaddr=0',        self.daemon_id == 'bch'],
			['--mempoolreplacement=1', self.daemon_id == 'ltc'],
			['--txindex=1',            self.daemon_id == 'ltc'],
		)

		if self.network == 'testnet':
			self.lockfile = os.path.join(self.datadir,self.testnet_dir,'.cookie')
		elif self.network == 'mainnet':
			self.lockfile = os.path.join(self.datadir,'.cookie')

	@property
	def state(self):
		cp = self.cli('getblockcount',silent=True,check=False)
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

class MoneroDaemon(CoinDaemon):

	exec_fn_mswin = 'monerod.exe'
	ps_pid_mswin = True
	new_console_mswin = True
	host = 'localhost' # FIXME
	datadir_is_subdir = True

	def subclass_init(self):

		self.p2p_port = self.rpc_port - 1
		self.zmq_port = self.rpc_port + 1

		if self.platform == 'win':
			self.use_pidfile = False

		self.shared_args = list_gen(
			[f'--p2p-bind-port={self.p2p_port}'],
			[f'--rpc-bind-port={self.rpc_port}'],
			[f'--zmq-rpc-bind-port={self.zmq_port}'],
			['--testnet', self.network == 'testnet'],
		)

		self.coind_args = list_gen(
			['--hide-my-port'],
			['--no-igd'],
			[f'--data-dir={self.datadir}'],
			[f'--pidfile={self.pidfile}', self.platform == 'linux'],
			['--detach',                  not 'no_daemonize' in self.opts],
			['--offline',                 not 'online' in self.opts],
		)

	@property
	def state(self):
		return 'ready' if self.test_socket(self.host,self.rpc_port) else 'stopped'
		# TODO:
		if not self.test_socket(self.host,self.rpc_port):
			return 'stopped'
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

	exec_fn_mswin = 'openethereum.exe'
	ps_pid_mswin = True

	def subclass_init(self):
		# defaults:
		# linux: $HOME/.local/share/io.parity.ethereum/chains/DevelopmentChain
		# win:   $LOCALAPPDATA/Parity/Ethereum/chains/DevelopmentChain

		chaindir = os.path.join(self.datadir,'devchain')
		shutil.rmtree(chaindir,ignore_errors=True)

		ld = self.platform == 'linux' and not 'no_daemonize' in self.opts
		self.coind_args = list_gen(
			[f'--ports-shift={self.port_shift}'],
			[f'--base-path={chaindir}'],
			['--config=dev'],
			['--log-file='+os.path.join(self.datadir,'openethereum.log')],
			['daemon',     ld],
			[self.pidfile, ld],
		)

	@property
	def state(self):
		return 'ready' if self.test_socket('localhost',self.rpc_port) else 'stopped'

		# the following code does not work
		async def do():
			ret = await self.rpc.call('eth_chainId')
			return ('stopped','ready')[ret == '0x11']

		try:
			return run_session(do()) # socket exception is not propagated
		except:# SocketError:
			return 'stopped'

	@property
	def stop_cmd(self):
		return ['kill','-Wf',self.pid] if self.platform == 'win' else ['kill',self.pid]

CoinDaemon.check_implement()
