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
from .rpc import rpc_init

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

	async def generate(self,blocks=1,silent=False):

		blocks = int(blocks)
		await self.switch_user('miner',quiet=True)

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

	async def create_tracking_wallet(self,user):
		try:
			await self.rpc_call('getbalance')
		except:
			await self.rpc_call('createwallet',
					user,            # wallet_name
					user != 'miner', # disable_private_keys
					user != 'miner', # blank (no keys or seed)
					'',              # passphrase (empty string for non-encrypted)
					False,           # avoid_reuse (track address reuse)
					False,           # descriptors (native descriptor wallet)
					False            # load_on_startup
				)

	async def setup(self):

		try: os.makedirs(self.d.datadir)
		except: pass

		if self.d.state != 'stopped':
			await self.rpc_call('stop')

		create_data_dir(self.d.datadir)

		gmsg('Starting {} regtest setup'.format(self.coin.upper()))

		gmsg('Creating miner wallet')
		self.start_daemon('miner')
		await self.create_tracking_wallet('miner')

		await self.generate(432,silent=True)
		await self.rpc_call('stop')
		time.sleep(1.2) # race condition?

		for user in ('alice','bob'):
			gmsg("Creating {}'s tracking wallet".format(user.capitalize()))
			self.start_daemon(user)
			await self.create_tracking_wallet(user)
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
		rpc = await rpc_init(self.proto,backend=None,daemon=self.d,caller='regtest')
		return await rpc.call(*args)

	async def current_user(self):
		try:
			return (await self.rpc_call('getwalletinfo'))['walletname']
		except SocketError as e:
			msg(str(e))
			return None

	async def stop(self):
		await self.rpc_call('stop')

	def state(self):
		msg(self.d.state)

	async def balances(self,*users):
		users = list(set(users or ['bob','alice']))
		cur_user = await self.current_user()
		if cur_user in users:
			users.remove(cur_user)
			users = [cur_user] + users
		bal = {}
		for user in users:
			await self.switch_user(user,quiet=True)
			out = await self.rpc_call('listunspent',0)
			bal[user] = sum(e['amount'] for e in out)

		fs = '{:<16} {:18.8f}'
		for user in sorted(users):
			msg(fs.format(user.capitalize()+"'s balance:",bal[user]))
		msg(fs.format('Total balance:',sum(v for k,v in bal.items())))

	async def send(self,addr,amt):
		await self.switch_user('miner',quiet=True)
		gmsg('Sending {} miner {} to address {}'.format(amt,self.d.daemon_id.upper(),addr))
		cp = await self.rpc_call('sendtoaddress',addr,str(amt))
		await self.generate(1)

	async def mempool(self):
		await self.cli('getrawmempool')

	async def cli(self,*args):
		import json
		from .rpc import json_encoder
		ret = await self.rpc_call(*args)
		print(ret if type(ret) == str else json.dumps(ret,cls=json_encoder))

	async def cmd(self,args):
		ret = getattr(self,args[0])(*args[1:])
		return (await ret) if type(ret).__name__ == 'coroutine' else ret

	async def user(self):
		ret = await self.current_user()
		msg(ret.capitalize() if ret else 'None')

	async def bob(self):   await self.switch_user('bob')
	async def alice(self): await self.switch_user('alice')
	async def miner(self): await self.switch_user('miner')

	async def switch_user(self,user,quiet=False):

		if self.d.state == 'busy':
			self.d.wait_for_state('ready')

		if self.d.state == 'ready':
			cur_user = await self.current_user()
			if user == cur_user:
				if not quiet:
					msg('{} is already the current user for {}'.format(user.capitalize(),self.d.net_desc))
				return
			gmsg_r('Switching to user {} for {}'.format(user.capitalize(),self.d.net_desc))
			if cur_user:
				await self.rpc_call('unloadwallet',cur_user)
			await self.rpc_call('loadwallet',user)
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
