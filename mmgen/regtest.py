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
from .rpc import rpc_init

def create_data_dir(data_dir):
	try: os.stat(os.path.join(data_dir,'regtest'))
	except: pass
	else:
		if keypress_confirm(
				f'Delete your existing MMGen regtest setup at {data_dir!r} and create a new one?'):
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
	usr_cmds     = ('setup','generate','send','start','stop', 'state', 'balances','mempool','cli')

	def __init__(self,coin):
		self.coin = coin.lower()
		assert self.coin in self.coins, f'{coin!r}: invalid coin for regtest'

		from .daemon import CoinDaemon
		self.proto = init_proto(self.coin,regtest=True)
		self.d = CoinDaemon(self.coin+'_rt',test_suite=g.test_suite_regtest)

	async def generate(self,blocks=1,silent=False):

		blocks = int(blocks)

		async def have_generatetoaddress():
			ret = await self.rpc_call('help','generatetoaddress',wallet='miner')
			return not 'unknown command:' in ret

		async def get_miner_address():
			return await self.rpc_call('getnewaddress',wallet='miner')

		if self.d.state == 'stopped':
			die(1,'Regtest daemon is not running')

		self.d.wait_for_state('ready')

		if await have_generatetoaddress():
			cmd_args = ( 'generatetoaddress', blocks, await get_miner_address() )
		else:
			cmd_args = ( 'generate', blocks )

		out = await self.rpc_call(*cmd_args,wallet='miner')

		if len(out) != blocks:
			rdie(1,'Error generating blocks')

		gmsg(f'Mined {blocks} block{suf(blocks)}')

	async def setup(self):

		try: os.makedirs(self.d.datadir)
		except: pass

		if self.d.state != 'stopped':
			await self.rpc_call('stop')

		create_data_dir(self.d.datadir)

		gmsg(f'Starting {self.coin.upper()} regtest setup')

		self.d.start(silent=True)

		rpc = await rpc_init(self.proto,backend=None,daemon=self.d)
		for user in ('miner','bob','alice'):
			gmsg(f'Creating {capfirst(user)}’s wallet')
			await rpc.icall(
				'createwallet',
				wallet_name     = user,
				no_keys         = user != 'miner',
				load_on_startup = False )

		await self.generate(432,silent=True)

		gmsg('Setup complete')

		if opt.setup_no_stop_daemon:
			msg('Leaving regtest daemon running')
		else:
			msg('Stopping regtest daemon')
			await self.rpc_call('stop')

	def init_daemon(self,reindex=False):
		if reindex:
			self.d.usr_coind_args.append('--reindex')

	async def start_daemon(self,reindex=False,silent=True):
		self.init_daemon(reindex=reindex)
		self.d.start(silent=silent)
		for user in ('miner','bob','alice'):
			msg(f'Loading {capfirst(user)}’s wallet')
			await self.rpc_call('loadwallet',user,start_daemon=False)

	async def rpc_call(self,*args,wallet=None,start_daemon=True):
		# g.prog_name == 'mmgen-regtest' test is used by .rpc to identify caller, so require this:
		assert g.prog_name == 'mmgen-regtest', 'only mmgen-regtest util is allowed to use this method'
		if start_daemon and self.d.state == 'stopped':
			await self.start_daemon()
		rpc = await rpc_init(self.proto,backend=None,daemon=self.d)
		return await rpc.call(*args,wallet=wallet)

	async def start(self):
		if self.d.state == 'stopped':
			await self.start_daemon(silent=False)
		else:
			msg(f'{g.coin} regtest daemon already started')

	async def stop(self):
		if self.d.state == 'stopped':
			msg(f'{g.coin} regtest daemon already stopped')
		else:
			msg(f'Stopping {g.coin} regtest daemon')
			await self.rpc_call('stop',start_daemon=False)

	def state(self):
		msg(self.d.state)

	async def balances(self):
		bal = {}
		users = ('bob','alice')
		for user in users:
			out = await self.rpc_call('listunspent',0,wallet=user)
			bal[user] = sum(e['amount'] for e in out)

		fs = '{:<16} {:18.8f}'
		for user in users:
			msg(fs.format(user.capitalize()+"'s balance:",bal[user]))
		msg(fs.format('Total balance:',sum(v for k,v in bal.items())))

	async def send(self,addr,amt):
		gmsg(f'Sending {amt} miner {self.d.coin} to address {addr}')
		cp = await self.rpc_call('sendtoaddress',addr,str(amt),wallet='miner')
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

	async def fork(self,coin): # currently disabled

		proto = init_proto(coin,False)
		if not [f for f in proto.forks if f[2] == proto.coin.lower() and f[3] == True]:
			die(1,f'Coin {proto.coin} is not a replayable fork of coin {coin}')

		gmsg(f'Creating fork from coin {coin} to coin {proto.coin}')

		source_rt = MMGenRegtest(coin)

		try:
			os.stat(source_rt.d.datadir)
		except:
			die(1,f'Source directory {source_rt.d.datadir!r} does not exist!')

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
		await self.start_daemon(reindex=True)
		await self.rpc_call('stop')

		gmsg(f'Fork {proto.coin} successfully created')
