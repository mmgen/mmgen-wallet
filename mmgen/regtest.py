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
regtest: Coin daemon regression test mode setup and operations for the MMGen suite
"""

import os,time,shutil,re,json
from subprocess import run,PIPE
from mmgen.common import *
from mmgen.daemon import CoinDaemon

def create_data_dir(data_dir):
	try: os.stat(os.path.join(data_dir,'regtest'))
	except: pass
	else:
		m = "Delete your existing MMGen regtest setup at '{}' and create a new one?"
		if keypress_confirm(m.format(data_dir)):
			shutil.rmtree(data_dir)
		else:
			die()

	try: os.makedirs(data_dir)
	except: pass

class RegtestDaemon(MMGenObject): # mixin class

	def generate(self,blocks=1,silent=False):

		def have_generatetoaddress():
			cp = self.cli('help','generatetoaddress',check=False,silent=True)
			return not 'unknown command' in cp.stdout.decode()

		def get_miner_address():
			return self.cli('getnewaddress',silent=silent).stdout.decode().strip()

		if self.state == 'stopped':
			die(1,'Regtest daemon is not running')

		self.wait_for_state('ready')

		if have_generatetoaddress():
			cmd = ( 'generatetoaddress', str(blocks), get_miner_address() )
		else:
			cmd = ( 'generate', str(blocks) )

		out = self.cli(*cmd,silent=silent).stdout.decode().strip()

		if len(json.loads(out)) != blocks:
			rdie(1,'Error generating blocks')

		gmsg('Mined {} block{}'.format(blocks,suf(blocks)))

class MMGenRegtest(MMGenObject):

	rpc_user     = 'bobandalice'
	rpc_password = 'hodltothemoon'
	users        = ('bob','alice','miner')
	coins        = ('btc','bch','ltc')
	usr_cmds     = (
		'bob','alice','miner','user','state',
		'setup','generate','send','stop',
		'balances','mempool','cli' )

	def __init__(self,coin):
		self.coin = coin.lower()
		self.test_suite = os.getenv('MMGEN_TEST_SUITE_REGTEST')
		self.d = CoinDaemon(self.coin+'_rt',test_suite=self.test_suite)

		assert self.coin in self.coins,'{!r}: invalid coin for regtest'.format(user)

	def setup(self):

		try: os.makedirs(self.d.datadir)
		except: pass

		if self.daemon_state() != 'stopped':
			self.stop_daemon()

		create_data_dir(self.d.datadir)

		gmsg('Starting {} regtest setup'.format(self.coin))

		gmsg('Creating miner wallet')
		d = self.start_daemon('miner')
		d.generate(432,silent=True)
		d.stop(silent=True)

		for user in ('alice','bob'):
			gmsg("Creating {}'s tracking wallet".format(user.capitalize()))
			d = self.start_daemon(user)
			if user == 'bob' and opt.setup_no_stop_daemon:
				msg('Leaving daemon running with Bob as current user')
			else:
				d.stop(silent=True)
				time.sleep(0.2) # race condition? (BCH only)

		gmsg('Setup complete')

	def daemon_state(self):
		return self.test_daemon().state

	def daemon_shared_args(self):
		return ['--rpcuser={}'.format(self.rpc_user),
				'--rpcpassword={}'.format(self.rpc_password),
				'--regtest' ]

	def daemon_coind_args(self,user):
		return ['--wallet=wallet.dat.{}'.format(user)]

	def test_daemon(self,user=None,reindex=False):

		assert user is None or user in self.users,'{!r}: invalid user for regtest'.format(user)

		d = CoinDaemon(self.coin+'_rt',test_suite=self.test_suite)

		type(d).generate = RegtestDaemon.generate

		d.net_desc = self.coin.upper()
		d.usr_shared_args = self.daemon_shared_args()

		if user:
			d.usr_coind_args = self.daemon_coind_args(user)
		if reindex:
			d.usr_coind_args += ['--reindex']

		return d

	def start_daemon(self,user,reindex=False,silent=True):
		d = self.test_daemon(user,reindex=reindex)
		d.start(silent=silent)
		return d

	def stop_daemon(self,silent=True):
		cp = self.test_daemon().stop(silent=silent)
		if cp:
			err = cp.stderr.decode()
			if err:
				if "couldn't connect to server" in err:
					rdie(1,'Error stopping the {} daemon:\n{}'.format(g.proto.name.capitalize(),err))
				msg(err)

	def current_user_unix(self,quiet=False):
		cmd = ['pgrep','-af','{}.*--rpcport={}.*'.format(g.proto.daemon_name,self.d.rpc_port)]
		cmdout = run(cmd,stdout=PIPE).stdout.decode()
		if cmdout:
			for k in self.users:
				if 'wallet.dat.'+k in cmdout:
					return k
		return None

	def current_user_win(self,quiet=False):

		if self.daemon_state() == 'stopped':
			return None

		debug_logfile = os.path.join(self.d.datadir,'regtest','debug.log')
		fd = os.open(debug_logfile,os.O_RDONLY|os.O_BINARY)
		file_size = os.fstat(fd).st_size

		def get_log_tail(num_bytes):
			os.lseek(fd,max(0,file_size-num_bytes),os.SEEK_SET)
			return os.read(fd,num_bytes)

		lines = reversed(get_log_tail(40_000).decode().splitlines())

		for ss in ( 'BerkeleyEnvironment::Open',
					'Wallet completed loading in',
					'Using wallet wallet' ):
			for line in lines:
				if ss in line:
					m = re.search(r'\bwallet\.dat\.([a-z]+)',line)
					if m and m.group(1) in self.users:
						return m.group(1)

		return None # failure to determine current user is not fatal, so don't raise exception

	current_user = {
		'win': current_user_win,
		'linux': current_user_unix }[g.platform]

	def stop(self):
		self.stop_daemon(silent=False)

	def state(self):
		msg(self.daemon_state())

	def balances(self,*users):
		users = list(set(users or ['bob','alice']))
		cur_user = self.current_user()
		if cur_user in users:
			users.remove(cur_user)
			users = [cur_user] + users
		bal = {}
		for user in users:
			d = self.switch_user(user,quiet=True)
			out = d.cli('listunspent','0',silent=True).stdout.strip().decode()
			bal[user] = sum(e['amount'] for e in json.loads(out))

		fs = '{:<16} {:18.8f}'
		for user in sorted(users):
			msg(fs.format(user.capitalize()+"'s balance:",bal[user]))
		msg(fs.format('Total balance:',sum(v for k,v in bal.items())))

	def send(self,addr,amt):
		d = self.switch_user('miner',quiet=True)
		gmsg('Sending {} miner {} to address {}'.format(amt,d.daemon_id.upper(),addr))
		cp = d.cli('sendtoaddress',addr,str(amt),silent=True)
		d.generate(1)

	def mempool(self):
		self.cli('getrawmempool')

	def cli(self,*args,silent=False,check=True):
		return self.test_daemon().cli(*args,silent=silent,check=check)

	def cmd(self,args):
		return getattr(self,args[0])(*args[1:])

	def user(self):
		u = self.current_user()
		msg(u.capitalize() if u else str(u))

	def bob(self):   self.switch_user('bob')
	def alice(self): self.switch_user('alice')
	def miner(self): self.switch_user('miner')

	def switch_user(self,user,quiet=False):

		d = self.test_daemon(user)

		if d.state == 'busy':
			d.wait_for_state('ready')

		if d.state == 'ready':
			if user == self.current_user():
				if not quiet:
					msg('{} is already the current user for {}'.format(user.capitalize(),d.net_desc))
				return d
			gmsg_r('Switching to user {} for {}'.format(user.capitalize(),d.net_desc))
			d.stop(silent=True)
			time.sleep(0.1) # file lock has race condition - TODO: test for lock file
			d = self.start_daemon(user)
		else:
			m = 'Starting {} {} with current user {}'
			gmsg_r(m.format(d.net_desc,d.desc,user.capitalize()))
			d.start(silent=True)

		gmsg('...done')
		return d

	def generate(self,amt=1):
		self.switch_user('miner',quiet=True).generate(int(amt),silent=True)

	def fork(self,coin): # currently disabled

		from mmgen.protocol import CoinProtocol
		forks = CoinProtocol(coin,False).forks
		if not [f for f in forks if f[2] == g.coin.lower() and f[3] == True]:
			die(1,"Coin {} is not a replayable fork of coin {}".format(g.coin,coin))

		gmsg('Creating fork from coin {} to coin {}'.format(coin,g.coin))

		source_rt = MMGenRegtest(coin)

		try: os.stat(source_rt.d.datadir)
		except: die(1,"Source directory '{}' does not exist!".format(source_rt.d.datadir))

		# stop the source daemon
		if source_rt.daemon_state() != 'stopped':
			source_rt.stop_daemon()

		# stop our daemon
		if self.daemon_state() != 'stopped':
			self.stop_daemon()

		try: os.makedirs(self.d.datadir)
		except: pass

		create_data_dir(self.d.datadir)
		os.rmdir(self.d.datadir)
		shutil.copytree(source_data_dir,self.d.datadir,symlinks=True)
		self.start_daemon('miner',reindex=True)
		self.stop_daemon()

		gmsg('Fork {} successfully created'.format(g.coin))
