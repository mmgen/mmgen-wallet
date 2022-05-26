#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
base_proto.bitcoin.regtest: Coin daemon regression test mode setup and operations
"""

import os,time,shutil,json,re
from subprocess import run,PIPE
from ...common import *
from ...protocol import init_proto
from ...rpc import rpc_init,json_encoder

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

miner_addr = {
	# cTyMdQ2BgfAsjopRVZrj7AoEGp97pKfrC2NkqLuwHr4KHfPNAKwp hdseed=1 ('beadcafe'*8)
	'btc': 'bcrt1qaq8t3pakcftpk095tnqfv5cmmczysls024atnd',
	'ltc': 'rltc1qaq8t3pakcftpk095tnqfv5cmmczysls05c8zyn',
	'bch': 'n2fxhNx27GhHAWQhyuZ5REcBNrJqCJsJ12',
}

def create_hdseed(proto):
	from ...tool.api import tool_api
	t = tool_api()
	t.init_coin(proto.coin,proto.network)
	t.addrtype = 'compressed' if proto.coin == 'BCH' else 'bech32'
	return t.hex2wif('beadcafe'*8)

def cliargs_convert(args):
	def gen():
		for arg in args:
			if arg.lower() in ('true','false'):
				yield (True,False)[arg.lower() == 'false']
			elif len(str(arg)) < 20 and re.match(r'[0-9]+',arg):
				yield int(arg)
			else:
				yield arg

	return tuple(gen())

class MMGenRegtest(MMGenObject):

	rpc_user     = 'bobandalice'
	rpc_password = 'hodltothemoon'
	users        = ('bob','alice','miner')
	coins        = ('btc','bch','ltc')
	usr_cmds     = ('setup','generate','send','start','stop', 'state', 'balances','mempool','cli','wallet_cli')

	def __init__(self,coin):
		self.coin = coin.lower()
		assert self.coin in self.coins, f'{coin!r}: invalid coin for regtest'

		from ...daemon import CoinDaemon
		self.proto = init_proto(self.coin,regtest=True,need_amt=True)
		self.d = CoinDaemon(self.coin+'_rt',test_suite=g.test_suite)

	async def generate(self,blocks=1,silent=False):

		blocks = int(blocks)

		if self.d.state == 'stopped':
			die(1,'Regtest daemon is not running')

		self.d.wait_for_state('ready')

		out = await self.rpc_call(
			'generatetoaddress',
			blocks,
			miner_addr[self.coin],
			wallet = 'miner' )

		if len(out) != blocks:
			die(4,'Error generating blocks')

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
			gmsg(f'Creating {capfirst(user)}’s tracking wallet')
			await rpc.icall(
				'createwallet',
				wallet_name     = user,
				blank           = True,
				no_keys         = user != 'miner',
				load_on_startup = False )

		# BCH and LTC daemons refuse to set HD seed with empty blockchain ("in IBD" error),
		# so generate a block:
		await self.generate(1,silent=True)

		# Unfortunately, we don’t get deterministic output with BCH and LTC even with fixed
		# hdseed, as their 'sendtoaddress' calls produce non-deterministic TXIDs due to random
		# input ordering and fee estimation.
		await rpc.call(
			'sethdseed',
			True,
			create_hdseed(self.proto),
			wallet = 'miner' )

		# Broken litecoind can only mine 431 blocks in regtest mode, so generate just enough
		# blocks to fund the test suite
		await self.generate(392,silent=True)

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
			self.d.stop(silent=True)

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
		ret = await self.rpc_call(*cliargs_convert(args))
		print(ret if type(ret) == str else json.dumps(ret,cls=json_encoder,indent=4))

	async def wallet_cli(self,wallet,*args):
		ret = await self.rpc_call(*cliargs_convert(args),wallet=wallet)
		print(ret if type(ret) == str else json.dumps(ret,cls=json_encoder,indent=4))

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
