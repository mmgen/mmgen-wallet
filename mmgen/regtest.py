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
regtest: Coin daemon regression test mode setup and operations for the MMGen suite
"""

import os,time,shutil
from subprocess import run,PIPE
from .common import *
from .protocol import init_proto
from .daemon import CoinDaemon

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
		assert self.coin in self.coins, f'{coin!r}: invalid coin for regtest'

		self.proto = init_proto(self.coin,regtest=True)
		self.d = CoinDaemon(self.coin+'_rt',test_suite=g.test_suite_regtest)
		self.d.usr_shared_args = [f'--rpcuser={self.rpc_user}', f'--rpcpassword={self.rpc_password}', '--regtest']

	async def generate(self,blocks=1,silent=False):

		blocks = int(blocks)
		self.switch_user('miner',quiet=True)

		async def have_generatetoaddress():
			ret = await self.rpc_call('help','generatetoaddress')
			return not 'unknown command:' in ret

		async def get_miner_address():
			return await self.rpc_call('getnewaddress')

		if self.d.state == 'stopped':
			die(1,'Regtest daemon is not running')

		self.d.wait_for_state('ready')

		if await have_generatetoaddress():
			cmd_args = ( 'generatetoaddress', blocks, await get_miner_address() )
		else:
			cmd_args = ( 'generate', blocks )

		out = await self.rpc_call(*cmd_args)

		if len(out) != blocks:
			rdie(1,'Error generating blocks')

		gmsg('Mined {} block{}'.format(blocks,suf(blocks)))

	async def setup(self):

		try: os.makedirs(self.d.datadir)
		except: pass

		if self.d.state != 'stopped':
			await self.rpc_call('stop')

		create_data_dir(self.d.datadir)

		gmsg('Starting {} regtest setup'.format(self.coin))

		gmsg('Creating miner wallet')
		self.start_daemon('miner')

		await self.generate(432,silent=True)
		await self.rpc_call('stop')
		time.sleep(1.2) # race condition?

		for user in ('alice','bob'):
			gmsg("Creating {}'s tracking wallet".format(user.capitalize()))
			self.start_daemon(user)
			if user == 'bob' and opt.setup_no_stop_daemon:
				msg('Leaving daemon running with Bob as current user')
			else:
				await self.rpc_call('stop')
				time.sleep(0.2) # race condition?

		gmsg('Setup complete')

	def init_daemon(self,user,reindex=False):
		assert user is None or user in self.users,'{!r}: invalid user for regtest'.format(user)
		self.d.net_desc = self.coin.upper()
		self.d.usr_coind_args = [f'--wallet={user}']
		if reindex:
			self.d.usr_coind_args.append('--reindex')

	def start_daemon(self,user,reindex=False,silent=True):
		self.init_daemon(user=user,reindex=reindex)
		self.d.start(silent=silent)

	async def rpc_call(self,*args):
		from .rpc import rpc_init
		rpc = await rpc_init(self.proto,backend=None,daemon=self.d)
		return await rpc.call(*args)

	def current_user_unix(self,quiet=False):
		cmd = ['pgrep','-af','{}.*--rpcport={}.*'.format(self.d.coind_exec,self.d.rpc_port)]
		cmdout = run(cmd,stdout=PIPE).stdout.decode()
		if cmdout:
			for k in self.users:
				if '--wallet='+k in cmdout:
					return k
		return None

	def current_user_win(self,quiet=False):

		if self.d.state == 'stopped':
			return None

		debug_logfile = os.path.join(self.d.datadir,'regtest','debug.log')
		fd = os.open(debug_logfile,os.O_RDONLY|os.O_BINARY)
		file_size = os.fstat(fd).st_size

		def get_log_tail(num_bytes):
			os.lseek(fd,max(0,file_size-num_bytes),os.SEEK_SET)
			return os.read(fd,num_bytes)

		lines = reversed(get_log_tail(40_000).decode().splitlines())

		import re
		pat = re.compile(r'\b(alice|bob|miner)\b')
		for ss in ( 'BerkeleyEnvironment::Open',
					'Wallet completed loading in',
					'Using wallet wallet' ):
			for line in lines:
				if ss in line:
					m = pat.search(line)
					if m and m.group(1) in self.users:
						return m.group(1)

		return None # failure to determine current user is not fatal, so don't raise exception

	current_user = {
		'win': current_user_win,
		'linux': current_user_unix }[g.platform]

	async def stop(self):
		await self.rpc_call('stop')

	def state(self):
		msg(self.d.state)

	async def balances(self,*users):
		users = list(set(users or ['bob','alice']))
		cur_user = self.current_user()
		if cur_user in users:
			users.remove(cur_user)
			users = [cur_user] + users
		bal = {}
		for user in users:
			self.switch_user(user,quiet=True)
			out = await self.rpc_call('listunspent',0)
			bal[user] = sum(e['amount'] for e in out)

		fs = '{:<16} {:18.8f}'
		for user in sorted(users):
			msg(fs.format(user.capitalize()+"'s balance:",bal[user]))
		msg(fs.format('Total balance:',sum(v for k,v in bal.items())))

	async def send(self,addr,amt):
		self.switch_user('miner',quiet=True)
		gmsg('Sending {} miner {} to address {}'.format(amt,self.d.daemon_id.upper(),addr))
		cp = await self.rpc_call('sendtoaddress',addr,str(amt))
		await self.generate(1)

	async def mempool(self):
		await self.cli('getrawmempool')

	async def cli(self,*args):
		import json
		from .rpc import json_encoder
		print(json.dumps(await self.rpc_call(*args),cls=json_encoder))

	async def cmd(self,args):
		ret = getattr(self,args[0])(*args[1:])
		return (await ret) if type(ret).__name__ == 'coroutine' else ret

	def user(self):
		u = self.current_user()
		msg(u.capitalize() if u else str(u))

	def bob(self):   self.switch_user('bob')
	def alice(self): self.switch_user('alice')
	def miner(self): self.switch_user('miner')

	def switch_user(self,user,quiet=False):

		if self.d.state == 'busy':
			self.d.wait_for_state('ready')

		if self.d.state == 'ready':
			if user == self.current_user():
				if not quiet:
					msg('{} is already the current user for {}'.format(user.capitalize(),self.d.net_desc))
				return
			gmsg_r('Switching to user {} for {}'.format(user.capitalize(),self.d.net_desc))
			self.d.stop(silent=True)
			time.sleep(0.1) # file lock has race condition - TODO: test for lock file
			self.start_daemon(user)
		else:
			m = 'Starting {} {} with current user {}'
			gmsg_r(m.format(self.d.net_desc,self.d.desc,user.capitalize()))
			self.start_daemon(user,silent=True)

		gmsg('...done')

	async def fork(self,coin): # currently disabled

		proto = init_proto(coin,False)
		if not [f for f in proto.forks if f[2] == proto.coin.lower() and f[3] == True]:
			die(1,"Coin {} is not a replayable fork of coin {}".format(proto.coin,coin))

		gmsg('Creating fork from coin {} to coin {}'.format(coin,proto.coin))

		source_rt = MMGenRegtest(coin)

		try: os.stat(source_rt.d.datadir)
		except: die(1,"Source directory '{}' does not exist!".format(source_rt.d.datadir))

		# stop the source daemon
		if source_rt.d.state != 'stopped':
			await source_rt.d.cli('stop')

		# stop our daemon
		if self.d.state != 'stopped':
			await self.rpc_call('stop')

		try: os.makedirs(self.d.datadir)
		except: pass

		create_data_dir(self.d.datadir)
		os.rmdir(self.d.datadir)
		shutil.copytree(source_data_dir,self.d.datadir,symlinks=True)
		self.start_daemon('miner',reindex=True)
		await self.rpc_call('stop')

		gmsg('Fork {} successfully created'.format(proto.coin))
