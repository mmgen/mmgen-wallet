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
from subprocess import run,PIPE,CompletedProcess
from collections import namedtuple
from .exception import *
from .common import *
from .flags import *

_dd = namedtuple('daemon_data',['coind_name','coind_version','coind_version_str']) # latest tested version
_cd = namedtuple('coins_data',['coin_name','daemon_ids'])
_nw = namedtuple('coin_networks',['mainnet','testnet','regtest'])

class Daemon(Lockable):

	desc = 'daemon'
	debug = False
	wait = True
	use_pidfile = True
	pids = ()
	use_threads = False
	cfg_file = None
	new_console_mswin = False
	lockfile = None
	private_port = None
	avail_opts = ()
	avail_flags = () # like opts, but can be set or unset after instantiation
	_reset_ok = ('debug','wait','pids')

	def __init__(self,opts=None,flags=None):

		self.platform = g.platform
		if self.platform == 'win':
			self.use_pidfile = False
			self.use_threads = True

		self.opt = ClassOpts(self,opts)
		self.flag = ClassFlags(self,flags)

	def exec_cmd_thread(self,cmd):
		import threading
		tname = ('exec_cmd','exec_cmd_win_console')[self.platform == 'win' and self.new_console_mswin]
		t = threading.Thread(target=getattr(self,tname),args=(cmd,))
		t.daemon = True
		t.start()
		if self.platform == 'win':
			Msg_r(' \b') # blocks w/o this...crazy
		return True

	def exec_cmd_win_console(self,cmd):
		from subprocess import Popen,CREATE_NEW_CONSOLE,STARTUPINFO,STARTF_USESHOWWINDOW,SW_HIDE
		si = STARTUPINFO(dwFlags=STARTF_USESHOWWINDOW,wShowWindow=SW_HIDE)
		p = Popen(cmd,creationflags=CREATE_NEW_CONSOLE,startupinfo=si)
		p.wait()

	def exec_cmd(self,cmd,is_daemon=False):
		out = (PIPE,None)[is_daemon and self.opt.no_daemonize]
		try:
			cp = run(cmd,check=False,stdout=out,stderr=out)
		except Exception as e:
			raise MMGenCalledProcessError(f'Error starting executable: {type(e).__name__} [Errno {e.errno}]')
		if self.debug:
			print(cp)
		return cp

	def run_cmd(self,cmd,silent=False,is_daemon=False):

		if is_daemon and not silent:
			msg(f'Starting {self.desc} on port {self.bind_port}')

		if self.debug:
			msg(f'\nExecuting: {" ".join(cmd)}')

		if self.use_threads and is_daemon and not self.opt.no_daemonize:
			ret = self.exec_cmd_thread(cmd)
		else:
			ret = self.exec_cmd(cmd,is_daemon)

		if isinstance(ret,CompletedProcess):
			if ret.stdout and (self.debug or not silent):
				msg(ret.stdout.decode().rstrip())
			if ret.stderr and (self.debug or (ret.returncode and not silent)):
				msg(ret.stderr.decode().rstrip())

		return ret

	@property
	def pid(self):
		if self.use_pidfile:
			return open(self.pidfile).read().strip()
		elif self.platform == 'win':
			"""
			Assumes only one running instance of given daemon.  If multiple daemons are running,
			the first PID in the list is returned and self.pids is set to the PID list.
			"""
			ss = f'{self.exec_fn}.exe'
			cp = self.run_cmd(['ps','-Wl'],silent=True)
			self.pids = ()
			# use Windows, not Cygwin, PID
			pids = tuple(line.split()[3] for line in cp.stdout.decode().splitlines() if ss in line)
			if pids:
				if len(pids) > 1:
					self.pids = pids
				return pids[0]
		elif self.platform == 'linux':
			ss = ' '.join(self.start_cmd)
			cp = self.run_cmd(['pgrep','-f',ss],silent=True)
			if cp.stdout:
				return cp.stdout.strip().decode()
		die(2,f'{ss!r} not found in process list, cannot determine PID')

	@property
	def bind_port(self):
		return self.private_port or self.rpc_port

	@property
	def state(self):
		if self.debug:
			msg(f'Testing port {self.bind_port}')
		return 'ready' if self.test_socket('localhost',self.bind_port) else 'stopped'

	@property
	def start_cmds(self):
		return [self.start_cmd]

	@property
	def stop_cmd(self):
		return ['kill','-Wf',self.pid] if self.platform == 'win' else ['kill',self.pid]

	def cmd(self,action,*args,**kwargs):
		return getattr(self,action)(*args,**kwargs)

	def do_start(self,silent=False):
		if not silent:
			msg(f'Starting {self.desc} on port {self.bind_port}')
		return self.run_cmd(self.start_cmd,silent=True,is_daemon=True)

	def do_stop(self,silent=False):
		if not silent:
			msg(f'Stopping {self.desc} on port {self.bind_port}')
		return self.run_cmd(self.stop_cmd,silent=True)

	def cli(self,*cmds,silent=False):
		return self.run_cmd(self.cli_cmd(*cmds),silent=silent)

	def state_msg(self,extra_text=None):
		extra_text = f'{extra_text} ' if extra_text else ''
		return '{:{w}} {:10} {}'.format(
			f'{self.desc} {extra_text}running',
			'pid N/A' if self.pid is None or self.pids else f'pid {self.pid}',
			f'port {self.bind_port}',
			w = 52 + len(extra_text) )

	def pre_start(self): pass

	def start(self,quiet=False,silent=False):
		if self.state == 'ready':
			if not (quiet or silent):
				msg(self.state_msg(extra_text='already'))
			return True

		self.wait_for_state('stopped')

		self.pre_start()

		ret = self.do_start(silent=silent)

		if self.wait:
			self.wait_for_state('ready')

		return ret

	def stop(self,quiet=False,silent=False):
		if self.state == 'ready':
			ret = self.do_stop(silent=silent)
			if self.pids:
				msg('Warning: multiple PIDs [{}] -- we may be stopping the wrong instance'.format(
					fmt_list(self.pids,fmt='bare')
				))
			if self.wait:
				self.wait_for_state('stopped')
			return ret
		else:
			if not (quiet or silent):
				msg(f'{self.desc} on port {self.bind_port} not running')
			return True

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
			die(2,f'Wait for state {req_state!r} timeout exceeded for {self.desc} (port {self.bind_port})')

class RPCDaemon(Daemon):

	avail_opts = ('no_daemonize',)

	def __init__(self):
		super().__init__()
		self.desc = '{} {} {}RPC daemon'.format(
			self.rpc_type,
			getattr(self.proto.network_names,self.proto.network),
			'test suite ' if self.test_suite else '' )
		self._set_ok += ('usr_daemon_args',)
		self.usr_daemon_args = []

	@property
	def start_cmd(self):
		return ([self.exec_fn] + self.daemon_args + self.usr_daemon_args)

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
			['--detach',                             not (self.opt.no_daemonize or self.platform=='win')],
			['--stagenet',                           self.network == 'testnet'],
		)

		from .rpc import MoneroWalletRPCClient
		self.rpc = MoneroWalletRPCClient( daemon=self, test_connection=False )

class CoinDaemon(Daemon):
	networks = ('mainnet','testnet','regtest')
	cfg_file_hdr = ''
	avail_flags = ('keep_cfg_file',)
	avail_opts = ('no_daemonize','online')
	testnet_dir = None
	test_suite_port_shift = 1237
	rpc_user = None
	rpc_password = None

	coins = {
		'BTC': _cd('Bitcoin',           ['bitcoin_core']),
		'BCH': _cd('Bitcoin Cash Node', ['bitcoin_cash_node']),
		'LTC': _cd('Litecoin',          ['litecoin_core']),
		'XMR': _cd('Monero',            ['monero']),
		'ETH': _cd('Ethereum',          ['openethereum','geth'] + (['erigon'] if g.enable_erigon else []) ),
		'ETC': _cd('Ethereum Classic',  ['parity']),
	}

	@classmethod
	def get_network_ids(cls): # FIXME: gets IDs for _default_ daemon only
		from .protocol import CoinProtocol
		def gen():
			for coin,data in cls.coins.items():
				for network in globals()[data.daemon_ids[0]+'_daemon'].networks:
					yield CoinProtocol.Base.create_network_id(coin,network)
		return list(gen())

	def __new__(cls,
			network_id = None,
			proto      = None,
			opts       = None,
			flags      = None,
			test_suite = False,
			port_shift = None,
			p2p_port   = None,
			datadir    = None,
			daemon_id  = None ):

		assert network_id or proto,        'CoinDaemon_chk1'
		assert not (network_id and proto), 'CoinDaemon_chk2'

		if proto:
			network_id = proto.network_id
			network    = proto.network
			coin       = proto.coin
		else:
			network_id = network_id.lower()
			from .protocol import CoinProtocol,init_proto
			proto = init_proto(network_id=network_id)
			coin,network = CoinProtocol.Base.parse_network_id(network_id)
			coin = coin.upper()

		daemon_ids = cls.coins[coin].daemon_ids
		daemon_id = daemon_id or g.daemon_id or daemon_ids[0]

		if daemon_id not in daemon_ids:
			die(1,f'{daemon_id!r}: invalid daemon_id - valid choices: {fmt_list(daemon_ids)}')

		me = Daemon.__new__(globals()[daemon_id + '_daemon'])
		assert network in me.networks, f'{network!r}: unsupported network for daemon {daemon_id}'
		me.network = network
		me.coin = coin
		me.coin_name = cls.coins[coin].coin_name
		me.id = daemon_id
		me.proto = proto

		return me

	def __init__(self,
			network_id = None,
			proto      = None,
			opts       = None,
			flags      = None,
			test_suite = False,
			port_shift = None,
			p2p_port   = None,
			datadir    = None,
			daemon_id  = None ):

		self.test_suite = test_suite

		super().__init__(opts=opts,flags=flags)

		self._set_ok += ('shared_args','usr_coind_args')
		self.shared_args = []
		self.usr_coind_args = []

		for k,v in self.daemon_data._asdict().items():
			setattr(self,k,v)

		self.desc = '{} {} {}daemon'.format(
			self.coind_name,
			getattr(self.proto.network_names,self.network),
			'test suite ' if test_suite else '' )

		# user-set values take precedence
		self.datadir = os.path.abspath(datadir or g.daemon_data_dir or self.init_datadir())
		self.non_dfl_datadir = bool(datadir or g.daemon_data_dir or test_suite or self.network == 'regtest')

		# init_datadir() may have already initialized logdir
		self.logdir = os.path.abspath(getattr(self,'logdir',self.datadir))

		ps_adj = (port_shift or 0) + (self.test_suite_port_shift if test_suite else 0)

		# user-set values take precedence
		self.rpc_port = (g.rpc_port or 0) + (port_shift or 0) if g.rpc_port else ps_adj + self.get_rpc_port()
		self.p2p_port = (
			p2p_port or (
				self.get_p2p_port() + ps_adj if self.get_p2p_port() and (test_suite or ps_adj) else None
			) if self.network != 'regtest' else None )

		if hasattr(self,'private_ports'):
			self.private_port = getattr(self.private_ports,self.network)

		# bind_port == self.private_port or self.rpc_port
		self.pidfile = '{}/{}-{}-daemon-{}.pid'.format(self.logdir,self.id,self.network,self.bind_port)
		self.logfile = '{}/{}-{}-daemon-{}.log'.format(self.logdir,self.id,self.network,self.bind_port)

		self.init_subclass()

	def init_datadir(self):
		if self.test_suite:
			return os.path.join('test','daemons',self.coin.lower())
		else:
			return os.path.join(*self.datadirs[self.platform])

	@property
	def network_datadir(self):
		return self.datadir

	def get_rpc_port(self):
		return getattr(self.rpc_ports,self.network)

	def get_p2p_port(self):
		return None

	@property
	def start_cmd(self):
		return ([self.exec_fn]
				+ self.coind_args
				+ self.shared_args
				+ self.usr_coind_args )

	def cli_cmd(self,*cmds):
		return ([self.cli_fn]
				+ self.shared_args
				+ list(cmds) )

	def start(self,*args,**kwargs):
		assert self.test_suite or self.network == 'regtest', 'start() restricted to test suite and regtest'
		return super().start(*args,**kwargs)

	def stop(self,*args,**kwargs):
		assert self.test_suite or self.network == 'regtest', 'stop() restricted to test suite and regtest'
		return super().stop(*args,**kwargs)

	def pre_start(self):
		os.makedirs(self.datadir,exist_ok=True)

		if self.test_suite or self.network == 'regtest':
			if self.cfg_file and not self.flag.keep_cfg_file:
				open(f'{self.datadir}/{self.cfg_file}','w').write(self.cfg_file_hdr)

		if self.use_pidfile and os.path.exists(self.pidfile):
			# Parity overwrites the data in the existing pidfile without zeroing it first, leading
			# to interesting consequences when the new PID has fewer digits than the previous one.
			os.unlink(self.pidfile)

	def remove_datadir(self):
		"remove the network's datadir"
		assert self.test_suite, 'datadir removal restricted to test suite'
		if self.state == 'stopped':
			try: # exception handling required for MSWin/MSYS2
				run(['/bin/rm','-rf',self.network_datadir])
			except:
				pass
		else:
			msg(f'Cannot remove {self.network_datadir!r} - daemon is not stopped')

class bitcoin_core_daemon(CoinDaemon):
	daemon_data = _dd('Bitcoin Core', 220000, '22.0.0')
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

class bitcoin_cash_node_daemon(bitcoin_core_daemon):
	daemon_data = _dd('Bitcoin Cash Node', 24000000, '24.0.0')
	exec_fn = 'bitcoind-bchn'
	cli_fn = 'bitcoin-cli-bchn'
	rpc_ports = _nw(8432, 18432, 18543) # use non-standard ports (core+100)
	datadirs = {
		'linux': [g.home_dir,'.bitcoin-bchn'],
		'win':   [os.getenv('APPDATA'),'Bitcoin_ABC']
	}
	cfg_file_hdr = '# Bitcoin Cash Node config file\n'
	nonstd_datadir = True

class litecoin_core_daemon(bitcoin_core_daemon):
	daemon_data = _dd('Litecoin Core', 180100, '0.18.1')
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

class monero_daemon(CoinDaemon):
	daemon_data = _dd('Monero', 'N/A', 'N/A')
	networks = ('mainnet','testnet')
	exec_fn = 'monerod'
	testnet_dir = 'stagenet'
	new_console_mswin = True
	host = 'localhost' # FIXME
	rpc_ports = _nw(18081, 38081, None) # testnet is stagenet
	cfg_file = 'bitmonero.conf'
	datadirs = {
		'linux': [g.home_dir,'.bitmonero'],
		'win':   ['/','c','ProgramData','bitmonero']
	}

	def init_datadir(self):
		self.logdir = super().init_datadir()
		return os.path.join(
			self.logdir,
			self.testnet_dir if self.network == 'testnet' else '' )

	def get_p2p_port(self):
		return self.rpc_port - 1

	def init_subclass(self):

		from .rpc import MoneroRPCClientRaw
		self.rpc = MoneroRPCClientRaw(
			host   = self.host,
			port   = self.rpc_port,
			user   = None,
			passwd = None,
			test_connection = False,
			daemon = self )

		self.shared_args = list_gen(
			[f'--no-zmq'],
			[f'--p2p-bind-port={self.p2p_port}', self.p2p_port],
			[f'--rpc-bind-port={self.rpc_port}'],
			['--stagenet', self.network == 'testnet'],
		)

		self.coind_args = list_gen(
			['--hide-my-port'],
			['--no-igd'],
			[f'--data-dir={self.datadir}', self.non_dfl_datadir],
			[f'--pidfile={self.pidfile}', self.platform == 'linux'],
			['--detach',                  not (self.opt.no_daemonize or self.platform=='win')],
			['--offline',                 not self.opt.online],
		)

	@property
	def stop_cmd(self):
		return ['kill','-Wf',self.pid] if self.platform == 'win' else [self.exec_fn] + self.shared_args + ['exit']

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
	daemon_data = _dd('Geth', 1010014, '1.10.14')
	version_pat = r'Geth/v(\d+)\.(\d+)\.(\d+)'
	exec_fn = 'geth'
	use_pidfile = False
	use_threads = True
	datadirs = {
		'linux': [g.home_dir,'.ethereum','geth'],
		'win':   [os.getenv('LOCALAPPDATA'),'Geth'] # FIXME
	}

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
			['--dev', self.network=='regtest'],
		)

# https://github.com/ledgerwatch/erigon
class erigon_daemon(geth_daemon):
	daemon_data = _dd('Erigon', 2021009005, '2021.09.5')
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
			[f'--datadir={self.datadir}', self.non_dfl_datadir and not self.network=='regtest'],
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
			[f'--datadir={self.datadir}', self.network != 'regtest'],
			['--http.api=eth,web3,txpool'],
		)
