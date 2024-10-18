#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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
proto.btc.regtest: Coin daemon regression test mode setup and operations
"""

import os, shutil, json
from ...util import msg, gmsg, die, capfirst, suf
from ...protocol import init_proto
from ...rpc import rpc_init, json_encoder
from ...objmethods import MMGenObject
from ...daemon import CoinDaemon

def create_data_dir(cfg, data_dir):
	try:
		os.stat(os.path.join(data_dir, 'regtest'))
	except:
		pass
	else:
		from ...ui import keypress_confirm
		if keypress_confirm(
				cfg,
				f'Delete your existing MMGen regtest setup at {data_dir!r} and create a new one?'):
			shutil.rmtree(data_dir)
		else:
			die(1, 'Exiting')

	try:
		os.makedirs(data_dir)
	except:
		pass

def cliargs_convert(args):
	def gen():
		for arg in args:
			try:
				yield json.loads(arg) # list, dict, bool, int, null
			except:
				yield arg # arbitrary string

	return tuple(gen())

class MMGenRegtest(MMGenObject):

	rpc_user     = 'bobandalice'
	rpc_password = 'hodltothemoon'
	users        = ('bob', 'alice', 'carol', 'miner')
	coins        = ('btc', 'bch', 'ltc')
	usr_cmds     = (
		'setup',
		'generate',
		'send',
		'start',
		'stop',
		'state',
		'balances',
		'mempool',
		'cli',
		'wallet_cli')
	bdb_hdseed = 'beadcafe' * 8
	bdb_miner_wif = 'cTyMdQ2BgfAsjopRVZrj7AoEGp97pKfrC2NkqLuwHr4KHfPNAKwp'
	bdb_miner_addrs = {
		# cTyMdQ2BgfAsjopRVZrj7AoEGp97pKfrC2NkqLuwHr4KHfPNAKwp hdseed=1
		'btc': 'bcrt1qaq8t3pakcftpk095tnqfv5cmmczysls024atnd',
		'ltc': 'rltc1qaq8t3pakcftpk095tnqfv5cmmczysls05c8zyn',
		'bch': 'n2fxhNx27GhHAWQhyuZ5REcBNrJqCJsJ12',
	}

	def __init__(self, cfg, coin, bdb_wallet=False):
		self.cfg = cfg
		self.coin = coin.lower()
		self.bdb_wallet = bdb_wallet

		assert self.coin in self.coins, f'{coin!r}: invalid coin for regtest'

		self.proto = init_proto(cfg, self.coin, regtest=True, need_amt=True)
		self.d = CoinDaemon(
			cfg,
			self.coin + '_rt',
			test_suite = cfg.test_suite,
			opts       = ['bdb_wallet'] if bdb_wallet else None)

	# Caching creates problems (broken pipe) when recreating + loading wallets,
	# so reinstantiate with every call:
	@property
	async def rpc(self):
		return await rpc_init(self.cfg, self.proto, backend=None, daemon=self.d)

	@property
	async def miner_addr(self):
		if not hasattr(self, '_miner_addr'):
			self._miner_addr = (
				self.bdb_miner_addrs[self.coin] if self.bdb_wallet else
				await self.rpc_call('getnewaddress', wallet='miner'))
		return self._miner_addr

	@property
	async def miner_wif(self):
		if not hasattr(self, '_miner_wif'):
			self._miner_wif = (
				self.bdb_miner_wif if self.bdb_wallet else
				await self.rpc_call('dumpprivkey', (await self.miner_addr), wallet='miner'))
		return self._miner_wif

	def create_hdseed_wif(self):
		from ...tool.api import tool_api
		t = tool_api(self.cfg)
		t.init_coin(self.proto.coin, self.proto.network)
		t.addrtype = 'compressed' if self.proto.coin == 'BCH' else 'bech32'
		return t.hex2wif(self.bdb_hdseed)

	async def generate(self, blocks=1, silent=False):

		blocks = int(blocks)

		if self.d.state == 'stopped':
			die(1, 'Regtest daemon is not running')

		self.d.wait_for_state('ready')

		# very slow with descriptor wallet and large block count - 'generatetodescriptor' no better
		out = await self.rpc_call(
			'generatetoaddress',
			blocks,
			await self.miner_addr,
			wallet = 'miner')

		if len(out) != blocks:
			die(4, 'Error generating blocks')

		if not silent:
			gmsg(f'Mined {blocks} block{suf(blocks)}')

	async def create_wallet(self, user):
		return await (await self.rpc).icall(
			'createwallet',
			wallet_name     = user,
			blank           = user != 'miner' or self.bdb_wallet,
			no_keys         = user != 'miner',
			descriptors     = not self.bdb_wallet,
			load_on_startup = False)

	async def setup(self):

		try:
			os.makedirs(self.d.datadir)
		except:
			pass

		if self.d.state != 'stopped':
			await self.rpc_call('stop')

		create_data_dir(self.cfg, self.d.datadir)

		gmsg(f'Starting {self.coin.upper()} regtest setup')

		self.d.start(silent=True)

		for user in ('miner', 'bob', 'alice'):
			gmsg(f'Creating {capfirst(user)}’s tracking wallet')
			await self.create_wallet(user)

		# BCH and LTC daemons refuse to set HD seed with empty blockchain ("in IBD" error),
		# so generate a block:
		await self.generate(1)

		# Unfortunately, we don’t get deterministic output with BCH and LTC even with fixed
		# hdseed, as their 'sendtoaddress' calls produce non-deterministic TXIDs due to random
		# input ordering and fee estimation.
		if self.bdb_wallet:
			await (await self.rpc).call(
				'sethdseed',
				True,
				self.create_hdseed_wif(),
				wallet = 'miner')

		# Broken litecoind can only mine 431 blocks in regtest mode, so generate just enough
		# blocks to fund the test suite.  Generation is slow, so divide into chunks:
		for n in (100, 100, 100, 92): # 392 blocks
			await self.generate(n)

		gmsg('Setup complete')

		if self.cfg.setup_no_stop_daemon:
			msg('Leaving regtest daemon running')
		else:
			msg('Stopping regtest daemon')
			await self.rpc_call('stop')

	def init_daemon(self, reindex=False):
		if reindex:
			self.d.usr_coind_args.append('--reindex')

	async def start_daemon(self, reindex=False, silent=True):
		self.init_daemon(reindex=reindex)
		self.d.start(silent=silent)
		for user in ('miner', 'bob', 'alice'):
			msg(f'Loading {capfirst(user)}’s wallet')
			await self.rpc_call('loadwallet', user, start_daemon=False)

	async def rpc_call(self, *args, wallet=None, start_daemon=True):
		if start_daemon and self.d.state == 'stopped':
			await self.start_daemon()
		return await (await self.rpc).call(*args, wallet=wallet)

	async def start(self):
		if self.d.state == 'stopped':
			await self.start_daemon(silent=False)
		else:
			msg(f'{self.cfg.coin} regtest daemon already started')

	async def stop(self):
		if self.d.state == 'stopped':
			msg(f'{self.cfg.coin} regtest daemon already stopped')
		else:
			msg(f'Stopping {self.cfg.coin} regtest daemon')
			self.d.stop(silent=True)

	def state(self):
		msg(self.d.state)

	async def balances(self):
		bal = {}
		users = ('bob', 'alice')
		for user in users:
			out = await self.rpc_call('listunspent', 0, wallet=user)
			bal[user] = sum(self.proto.coin_amt(e['amount']) for e in out)

		fs = '{:<16} {:18.8f}'
		for user in users:
			msg(fs.format(user.capitalize()+"'s balance:", bal[user]))
		msg(fs.format('Total balance:', sum(v for k, v in bal.items())))

	async def send(self, addr, amt):
		gmsg(f'Sending {amt} miner {self.d.coin} to address {addr}')
		await self.rpc_call('sendtoaddress', addr, str(amt), wallet='miner')
		await self.generate(1)

	async def mempool(self):
		await self.cli('getrawmempool')

	async def cli(self, *args):
		ret = await self.rpc_call(*cliargs_convert(args))
		print(ret if isinstance(ret, str) else json.dumps(ret, cls=json_encoder, indent=4))

	async def wallet_cli(self, wallet, *args):
		ret = await self.rpc_call(*cliargs_convert(args), wallet=wallet)
		print(ret if isinstance(ret, str) else json.dumps(ret, cls=json_encoder, indent=4))

	async def cmd(self, args):
		ret = getattr(self, args[0])(*args[1:])
		return (await ret) if type(ret).__name__ == 'coroutine' else ret

	async def fork(self, coin): # currently disabled

		proto = init_proto(self.cfg, coin, False)
		if not [f for f in proto.forks if f[2] == proto.coin.lower() and f[3] is True]:
			die(1, f'Coin {proto.coin} is not a replayable fork of coin {coin}')

		gmsg(f'Creating fork from coin {coin} to coin {proto.coin}')

		source_rt = MMGenRegtest(self.cfg, coin, bdb_wallet=self.bdb_wallet)

		try:
			os.stat(source_rt.d.datadir)
		except:
			die(1, f'Source directory {source_rt.d.datadir!r} does not exist!')

		# stop the source daemon
		if source_rt.d.state != 'stopped':
			await source_rt.d.cli('stop')

		# stop our daemon
		if self.d.state != 'stopped':
			await self.rpc_call('stop')

		try:
			os.makedirs(self.d.datadir)
		except:
			pass

		create_data_dir(self.cfg, self.d.datadir)
		os.rmdir(self.d.datadir)
		shutil.copytree(source_rt.d.datadir, self.d.datadir, symlinks=True)
		await self.start_daemon(reindex=True)
		await self.rpc_call('stop')

		gmsg(f'Fork {proto.coin} successfully created')
