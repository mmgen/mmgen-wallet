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
test_daemon.py:  Daemon control classes for MMGen test suite and regtest mode
"""

from subprocess import run,PIPE
from collections import namedtuple
from mmgen.exception import *
from mmgen.common import *

class TestDaemon(MMGenObject):
	cfg_file_hdr = ''

	subclasses_must_implement = ('state','stop_cmd')

	network_ids = ('btc','btc_tn','bch','bch_tn','ltc','ltc_tn','xmr')

	cd = namedtuple('coin_data',['coin','coind_exec','cli_exec','conf_file','dfl_rpc','dfl_rpc_tn'])
	coins = {
		'btc': cd('Bitcoin',         'bitcoind',    'bitcoin-cli', 'bitcoin.conf',  8333,18333),
		'bch': cd('Bcash',           'bitcoind-abc','bitcoin-cli', 'bitcoin.conf',  8442,18442), # MMGen RPC dfls
		'ltc': cd('Litecoin',        'litecoind',   'litecoin-cli','litecoin.conf', 9333,19335),
		'xmr': cd('Monero',          'monerod',     'monerod',     'bitmonero.conf',18082,28082),
		'eth': cd('Ethereum',        'parity',      'parity',      'parity.conf',   8545,8545),
		'etc': cd('Ethereum Classic','parity',      'parity',      'parity.conf',   8545,8545)
	}
	port_shift = 1000

	debug = False
	wait = True
	use_pidfile = True

	testnet_arg = []

	coind_args = []
	cli_args = []
	shared_args = []

	coin_specific_coind_args = []
	coin_specific_cli_args = []
	coin_specific_shared_args = []

	usr_coind_args = []
	usr_cli_args = []
	usr_shared_args = []

	usr_rpc_port = None

	def __new__(cls,network_id,datadir=None,rpc_port=None,desc='test suite daemon'):

		network_id = network_id.lower()
		assert network_id in cls.network_ids, '{!r}: invalid network ID'.format(network_id)

		if not datadir: # hack for throwaway instances
			datadir = '/tmp/foo'
		assert os.path.isabs(datadir), '{!r}: invalid datadir (not an absolute path)'.format(datadir)

		if network_id.endswith('_tn'):
			coinsym = network_id[:-3]
			network = 'testnet'
		else:
			coinsym = network_id
			network = 'mainnet'

		me = MMGenObject.__new__(
			MoneroTestDaemon        if coinsym == 'xmr'
			else BitcoinTestDaemon )

		me.network_id = network_id
		me.coinsym = coinsym
		me.network = network
		me.datadir = datadir
		me.platform = g.platform
		me.desc = desc
		me.usr_rpc_port = rpc_port
		return me

	def __init__(self,network_id,datadir=None,rpc_port=None,desc='test suite daemon'):

		self.pidfile = '{}/{}-daemon.pid'.format(self.datadir,self.network)

		for k in self.coins[self.coinsym]._fields:
			setattr(self,k,getattr(self.coins[self.coinsym],k))

		self.rpc_port = self.usr_rpc_port or (
			(self.dfl_rpc,self.dfl_rpc_tn)[self.network=='testnet'] + self.port_shift
		)

		self.net_desc = '{} {}'.format(self.coin,self.network)
		self.subclass_init()

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

	@property
	def start_cmd(self):
		return ([self.coind_exec]
				+ self.testnet_arg
				+ self.coind_args
				+ self.shared_args
				+ self.coin_specific_coind_args
				+ self.coin_specific_shared_args
				+ self.usr_coind_args
				+ self.usr_shared_args)

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
			if self.conf_file:
				open('{}/{}'.format(self.datadir,self.conf_file),'w').write(self.cfg_file_hdr)
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
			die(2,'Daemon wait timeout for {} {} exceeded'.format(self.coin,self.network))

	@property
	def is_ready(self):
		return self.state == 'ready'

	@classmethod
	def check_implement(cls):
		m = 'required method {}() missing in class {}'
		for subcls in cls.__subclasses__():
			for k in cls.subclasses_must_implement:
				assert k in subcls.__dict__, m.format(k,subcls.__name__)

class BitcoinTestDaemon(TestDaemon):
	cfg_file_hdr = '# TestDaemon config file\n'

	def subclass_init(self):

		if self.platform == 'win' and self.coinsym == 'bch':
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

		if self.coinsym == 'bch':
			self.coin_specific_coind_args = ['--usecashaddr=0']
		elif self.coinsym == 'ltc':
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

class MoneroTestDaemon(TestDaemon):

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

TestDaemon.check_implement()
