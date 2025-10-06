#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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
daemon: Daemon control interface for the MMGen suite
"""

import sys, os, time, importlib
from subprocess import run, PIPE, CompletedProcess
from collections import namedtuple

from .base_obj import Lockable
from .color import set_vt100
from .util import msg, Msg_r, die, remove_dups, oneshot_warning, fmt_list
from .flags import ClassFlags, ClassOpts

_dd = namedtuple('daemon_data', ['coind_name', 'coind_version', 'coind_version_str']) # latest tested version
_nw = namedtuple('coin_networks', ['mainnet', 'testnet', 'regtest'])

class Daemon(Lockable):

	desc = 'daemon'
	debug = False
	wait = True
	use_pidfile = True
	force_kill = False
	pids = ()
	use_threads = False
	cfg_file = None
	new_console_mswin = False
	lockfile = None
	private_port = None
	avail_opts = ()
	avail_flags = () # like opts, but can be set or unset after instantiation
	_reset_ok = ('debug', 'wait', 'pids')
	version_info_arg = '--version'

	def __init__(self, cfg, *, opts=None, flags=None):

		self.cfg = cfg
		self.platform = sys.platform
		if self.platform == 'win32':
			self.use_pidfile = False
			self.use_threads = True

		self.opt = ClassOpts(self, opts)
		self.flag = ClassFlags(self, flags)
		self.debug = self.debug or cfg.debug_daemon

	def exec_cmd_thread(self, cmd):
		import threading
		tname = ('exec_cmd', 'exec_cmd_win_console')[self.platform == 'win32' and self.new_console_mswin]
		t = threading.Thread(target=getattr(self, tname), args=(cmd,))
		t.daemon = True
		t.start()
		if self.platform == 'win32':
			Msg_r(' \b') # blocks w/o this...crazy
		return True

	def exec_cmd_win_console(self, cmd):
		from subprocess import Popen, CREATE_NEW_CONSOLE, STARTUPINFO, STARTF_USESHOWWINDOW, SW_HIDE
		si = STARTUPINFO(dwFlags=STARTF_USESHOWWINDOW, wShowWindow=SW_HIDE)
		p = Popen(cmd, creationflags=CREATE_NEW_CONSOLE, startupinfo=si)
		p.wait()

	def exec_cmd(self, cmd, *, is_daemon=False, check_retcode=False):
		out = (PIPE, None)[is_daemon and self.opt.no_daemonize]
		try:
			cp = run(cmd, check=False, stdout=out, stderr=out)
		except OSError as e:
			die('MMGenCalledProcessError', f'Error starting executable: {type(e).__name__} [Errno {e.errno}]')
		set_vt100()
		if check_retcode and cp.returncode:
			die(1, str(cp))
		if self.debug:
			print(cp)
		return cp

	def run_cmd(self, cmd, *, silent=False, is_daemon=False, check_retcode=False):

		if self.debug:
			msg('\n\n')

		if self.debug or (is_daemon and not silent):
			msg(f'Starting {self.desc} on port {self.bind_port}')

		if self.debug:
			msg(f'\nExecuting:\n{fmt_list(cmd, fmt="col", indent="  ")}\n')

		if self.use_threads and is_daemon and not self.opt.no_daemonize:
			ret = self.exec_cmd_thread(cmd)
		else:
			ret = self.exec_cmd(cmd, is_daemon=is_daemon, check_retcode=check_retcode)

		if isinstance(ret, CompletedProcess):
			if ret.stdout and (self.debug or not silent):
				msg(ret.stdout.decode().rstrip())
			if ret.stderr and (self.debug or (ret.returncode and not silent)):
				msg(ret.stderr.decode().rstrip())

		return ret

	@property
	def pid(self):
		if self.use_pidfile:
			with open(self.pidfile) as fp:
				return fp.read().strip()

		match self.platform:
			case 'win32':
				# Assumes only one running instance of given daemon.  If multiple daemons are running,
				# the first PID in the list is returned and self.pids is set to the PID list.
				ss = f'{self.exec_fn}.exe'
				cp = self.run_cmd(['ps', '-Wl'], silent=True)
				self.pids = ()
				# use Windows, not Cygwin, PID
				pids = tuple(line.split()[3] for line in cp.stdout.decode().splitlines() if ss in line)
				if pids:
					if len(pids) > 1:
						self.pids = pids
					return pids[0]
			case 'linux' | 'darwin':
				ss = ' '.join(self.start_cmd)
				cp = self.run_cmd(['pgrep', '-f', ss], silent=True)
				if cp.stdout:
					return cp.stdout.strip().decode()

		die(2, f'{ss!r} not found in process list, cannot determine PID')

	@property
	def bind_port(self):
		return self.private_port or self.rpc_port

	@property
	def state(self):
		if self.debug:
			msg(f'Testing port {self.bind_port}')
		return 'ready' if self.test_socket('localhost', self.bind_port) else 'stopped'

	@property
	def start_cmds(self):
		return [self.start_cmd]

	@property
	def stop_cmd(self):
		return (
			['kill', '-Wf', self.pid] if self.platform == 'win32' else
			['kill', '-9', self.pid] if self.force_kill else
			['kill', self.pid])

	def cmd(self, action, *args, **kwargs):
		return getattr(self, action)(*args, **kwargs)

	def cli(self, *cmds, silent=False):
		return self.run_cmd(self.cli_cmd(*cmds), silent=silent)

	def state_msg(self, *, extra_text=None):
		try:
			pid = self.pid
		except:
			pid = None
		extra_text = 'not ' if self.state == 'stopped' else f'{extra_text} ' if extra_text else ''
		return '{:{w}} {:10} {}'.format(
			f'{self.desc} {extra_text}running',
			'pid N/A' if pid is None or self.pids or self.state == 'stopped' else f'pid {pid}',
			f'port {self.bind_port}',
			w = 60)

	def pre_start(self):
		pass

	def start(self, *, quiet=False, silent=False):
		if self.state == 'ready':
			if not (quiet or silent):
				msg(self.state_msg(extra_text='already'))
			return True

		self.wait_for_state('stopped')

		self.pre_start()

		if not silent:
			msg(f'Starting {self.desc} on port {self.bind_port}')
		ret = self.run_cmd(self.start_cmd, silent=True, is_daemon=True, check_retcode=True)

		if self.wait:
			self.wait_for_state('ready')

		return ret

	def stop(self, *, quiet=False, silent=False):
		if self.state == 'ready':
			if not silent:
				msg(f'Stopping {self.desc} on port {self.bind_port}')
			if self.force_kill:
				run(['sync'])
			ret = self.run_cmd(self.stop_cmd, silent=True)

			if self.pids:
				msg('Warning: multiple PIDs [{}] -- we may be stopping the wrong instance'.format(
					fmt_list(self.pids, fmt='bare')
				))
			if self.wait:
				self.wait_for_state('stopped')
				time.sleep(0.3) # race condition
			return ret
		else:
			if not (quiet or silent):
				msg(f'{self.desc} on port {self.bind_port} not running')
			return True

	def restart(self, *, silent=False):
		self.stop(silent=silent)
		return self.start(silent=silent)

	def test_socket(self, host, port, *, timeout=10):
		import socket
		try:
			socket.create_connection((host, port), timeout=timeout).close()
		except:
			return False
		else:
			return True

	def wait_for_state(self, req_state):
		for _ in range(self.cfg.daemon_state_timeout * 5):
			if self.state == req_state:
				return True
			time.sleep(0.2)
		die(2, f'Wait for state {req_state!r} timeout exceeded for {self.desc} (port {self.bind_port})')

	@classmethod
	def get_exec_version_str(cls):
		try:
			cp = run([cls.exec_fn, cls.version_info_arg], stdout=PIPE, stderr=PIPE, check=True, text=True)
		except Exception as e:
			die(2, f'{e}\nUnable to execute {cls.exec_fn}')

		if cp.returncode:
			die(2, f'Unable to execute {cls.exec_fn}')
		else:
			res = cp.stdout.splitlines()
			return (res[0] if len(res) == 1 else [s for s in res if 'ersion' in s][0]).strip()

class RPCDaemon(Daemon):

	avail_opts = ('no_daemonize',)

	def __init__(self, cfg, *, opts=None, flags=None):
		super().__init__(cfg, opts=opts, flags=flags)
		self.desc = '{} {} {}RPC daemon'.format(
			self.rpc_desc,
			getattr(self.proto.network_names, self.proto.network),
			'test suite ' if self.test_suite else '')
		self._set_ok += ('usr_daemon_args',)
		self.usr_daemon_args = []

	@property
	def start_cmd(self):
		return [self.exec_fn] + self.daemon_args + self.usr_daemon_args

class CoinDaemon(Daemon):
	networks = ('mainnet', 'testnet', 'regtest')
	cfg_file_hdr = ''
	avail_flags = ('keep_cfg_file',)
	avail_opts = ('no_daemonize', 'online')
	testnet_dir = None
	test_suite_port_shift = 1237
	rpc_user = None
	rpc_password = None

	_cd = namedtuple('coins_data', ['daemon_ids'])
	coins = {
		'BTC': _cd(['bitcoin_core']),
		'BCH': _cd(['bitcoin_cash_node']),
		'LTC': _cd(['litecoin_core']),
		'XMR': _cd(['monero']),
		'ETH': _cd(['geth', 'reth', 'erigon']), #, 'openethereum'
		'ETC': _cd(['parity'])}

	@classmethod
	def all_daemon_ids(cls):
		return [i for coin in cls.coins for i in cls.coins[coin].daemon_ids]

	class warn_blacklisted(oneshot_warning):
		color = 'yellow'
		message = 'blacklisted daemon: {!r}'

	@classmethod
	def get_daemon_ids(cls, cfg, coin):

		ret = cls.coins[coin].daemon_ids
		if 'erigon' in ret and not cfg.enable_erigon:
			ret.remove('erigon')
		if cfg.blacklisted_daemons:
			blacklist = cfg.blacklisted_daemons.split()
			def gen():
				for daemon_id in ret:
					if daemon_id in blacklist:
						cls.warn_blacklisted(div=daemon_id, fmt_args=[daemon_id])
					else:
						yield daemon_id
			ret = list(gen())
		return ret

	@classmethod
	def get_daemon(cls, cfg, coin, daemon_id, *, proto=None):
		if proto:
			proto_cls = type(proto)
		else:
			from .protocol import init_proto
			proto_cls = init_proto(cfg, coin, return_cls=True)
		return getattr(
			importlib.import_module(f'mmgen.proto.{proto_cls.base_proto_coin.lower()}.daemon'),
			daemon_id+'_daemon')

	@classmethod
	def get_network_ids(cls, cfg):
		from .protocol import CoinProtocol
		def gen():
			for coin in cls.coins:
				for daemon_id in cls.get_daemon_ids(cfg, coin):
					for network in cls.get_daemon(cfg, coin, daemon_id).networks:
						yield CoinProtocol.Base.create_network_id(coin, network)
		return remove_dups(list(gen()), quiet=True)

	def __new__(cls,
			cfg,
			*,
			network_id = None,
			proto      = None,
			opts       = None,
			flags      = None,
			test_suite = False,
			port_shift = None,
			p2p_port   = None,
			datadir    = None,
			daemon_id  = None):

		assert network_id or proto,        'CoinDaemon_chk1'
		assert not (network_id and proto), 'CoinDaemon_chk2'

		if proto:
			network_id = proto.network_id
			network    = proto.network
			coin       = proto.coin
		else:
			network_id = network_id.lower()
			from .protocol import CoinProtocol, init_proto
			proto = init_proto(cfg, network_id=network_id)
			coin, network = CoinProtocol.Base.parse_network_id(network_id)
			coin = coin.upper()

		daemon_ids = cls.get_daemon_ids(cfg, coin)
		if not daemon_ids:
			die(1, f'No configured daemons for coin {coin}!')
		daemon_id = (
			daemon_id
			or getattr(cfg, f'{coin.lower()}_daemon_id', None)
			or cfg.daemon_id
			or daemon_ids[0])

		if daemon_id not in daemon_ids:
			die(1, f'{daemon_id!r}: invalid daemon_id - valid choices: {fmt_list(daemon_ids)}')

		me = Daemon.__new__(cls.get_daemon(cfg, None, daemon_id, proto=proto))

		assert network in me.networks, f'{network!r}: unsupported network for daemon {daemon_id}'
		me.network_id = network_id
		me.network = network
		me.coin = coin
		me.id = daemon_id
		me.proto = proto

		return me

	def __init__(self,
			cfg,
			*,
			network_id = None,
			proto      = None,
			opts       = None,
			flags      = None,
			test_suite = False,
			port_shift = None,
			p2p_port   = None,
			datadir    = None,
			daemon_id  = None):

		self.test_suite = test_suite

		super().__init__(cfg=cfg, opts=opts, flags=flags)

		self._set_ok += ('shared_args', 'usr_coind_args')
		self.shared_args = []
		self.usr_coind_args = []

		for k, v in self.daemon_data._asdict().items():
			setattr(self, k, v)

		self.desc = '{} {} {}daemon'.format(
			self.coind_name,
			getattr(self.proto.network_names, self.network),
			'test suite ' if test_suite else '')

		# user-set values take precedence
		self.datadir = os.path.abspath(datadir or cfg.daemon_data_dir or self.init_datadir())
		self.non_dfl_datadir = bool(datadir or cfg.daemon_data_dir or test_suite or self.network == 'regtest')

		# init_datadir() may have already initialized logdir
		self.logdir = os.path.abspath(getattr(self, 'logdir', self.datadir))

		ps_adj = (port_shift or 0) + (self.test_suite_port_shift if test_suite else 0)

		# user-set values take precedence
		usr_rpc_port = self.proto.rpc_port or cfg.rpc_port
		self.rpc_port = usr_rpc_port + (port_shift or 0) if usr_rpc_port else ps_adj + self.get_rpc_port()
		self.p2p_port = (
			p2p_port or (
				self.get_p2p_port() + ps_adj if self.get_p2p_port() and (test_suite or ps_adj) else None
			) if self.network != 'regtest' else None)

		if hasattr(self, 'private_ports'):
			self.private_port = getattr(self.private_ports, self.network)

		# bind_port == self.private_port or self.rpc_port
		self.pidfile = f'{self.logdir}/{self.id}-{self.network}-daemon-{self.bind_port}.pid'
		self.logfile = f'{self.logdir}/{self.id}-{self.network}-daemon-{self.bind_port}.log'

		self.init_subclass()

	def init_datadir(self):
		if self.test_suite:
			return os.path.join('test', 'daemons', self.network_id)
		else:
			return os.path.join(*self.datadirs[self.platform])

	@property
	def network_datadir(self):
		return self.datadir

	def get_rpc_port(self):
		return getattr(self.rpc_ports, self.network)

	def get_p2p_port(self):
		return None

	@property
	def start_cmd(self):
		return ([self.exec_fn]
				+ self.coind_args
				+ self.shared_args
				+ self.usr_coind_args)

	def cli_cmd(self, *cmds):
		return ([self.cli_fn]
				+ self.shared_args
				+ list(cmds))

	def start(self, *args, **kwargs):
		assert self.test_suite or self.network == 'regtest', 'start() restricted to test suite and regtest'
		return super().start(*args, **kwargs)

	def stop(self, *args, **kwargs):
		assert self.test_suite or self.network == 'regtest', 'stop() restricted to test suite and regtest'
		return super().stop(*args, **kwargs)

	def pre_start(self):
		os.makedirs(self.datadir, exist_ok=True)

		if self.test_suite or self.network == 'regtest':
			if self.cfg_file and not self.flag.keep_cfg_file:
				with open(f'{self.datadir}/{self.cfg_file}', 'w') as fp:
					fp.write(self.cfg_file_hdr)

		if self.use_pidfile and os.path.exists(self.pidfile):
			# Parity overwrites the data in the existing pidfile without zeroing it first, leading
			# to interesting consequences when the new PID has fewer digits than the previous one.
			os.unlink(self.pidfile)

	def remove_datadir(self):
		"remove the network's datadir"
		assert self.test_suite, 'datadir removal restricted to test suite'
		if self.state == 'stopped':
			run(['rm', '-rf', self.datadir])
			set_vt100()
		else:
			msg(f'Cannot remove {self.network_datadir!r} - daemon is not stopped')
