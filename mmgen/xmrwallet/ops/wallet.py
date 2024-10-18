#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
xmrwallet.ops.wallet: xmrwallet wallet op for the MMGen Suite
"""

import asyncio, re, atexit
from pathlib import Path

from ...color import orange
from ...util import msg, gmsg, ymsg, die, suf
from ...addrlist import KeyAddrList, ViewKeyAddrList, AddrIdxList
from ...proto.xmr.rpc import MoneroRPCClient, MoneroWalletRPCClient
from ...proto.xmr.daemon import MoneroWalletDaemon

from . import OpBase

class OpWallet(OpBase):

	opts = (
		'use_internal_keccak_module',
		'hash_preset',
		'daemon',
		'no_start_wallet_daemon',
		'no_stop_wallet_daemon',
		'autosign',
		'watch_only',
	)
	wallet_offline = False
	wallet_exists = True
	start_daemon = True
	skip_wallet_check = False # for debugging

	def __init__(self, cfg, uarg_tuple):

		def wallet_exists(fn):
			try:
				fn.stat()
			except:
				return False
			else:
				return True

		def check_wallets():
			for d in self.addr_data:
				fn = self.get_wallet_fn(d)
				exists = wallet_exists(fn)
				if exists and not self.wallet_exists:
					die(1, f'Wallet ‘{fn}’ already exists!')
				elif not exists and self.wallet_exists:
					die(1, f'Wallet ‘{fn}’ not found!')

		super().__init__(cfg, uarg_tuple)

		if self.cfg.offline or (self.name == 'create' and self.cfg.restore_height is None):
			self.wallet_offline = True

		self.wd = MoneroWalletDaemon(
			cfg         = self.cfg,
			proto       = self.proto,
			wallet_dir  = self.cfg.wallet_dir or '.',
			test_suite  = self.cfg.test_suite,
			monerod_addr = self.cfg.daemon or None,
			trust_monerod = self.trust_monerod,
			test_monerod = not self.wallet_offline,
		)

		if self.wallet_offline:
			self.wd.usr_daemon_args = ['--offline']

		self.c = MoneroWalletRPCClient(
			cfg             = self.cfg,
			daemon          = self.wd,
			test_connection = False,
		)

		if self.cfg.offline:
			from ...wallet import Wallet
			self.seed_src = Wallet(
				cfg           = cfg,
				fn            = self.uargs.infile,
				ignore_in_fmt = True)

			gmsg('\nCreating ephemeral key-address list for offline wallets')
			self.kal = KeyAddrList(
				cfg       = cfg,
				proto     = self.proto,
				seed      = self.seed_src.seed,
				addr_idxs = self.uargs.wallets,
				skip_chksum_msg = True)
		else:
			self.mount_removable_device()
			# with watch_only, make a second attempt to open the file as KeyAddrList:
			for first_try in (True, False):
				try:
					self.kal = (ViewKeyAddrList if (self.cfg.watch_only and first_try) else KeyAddrList)(
						cfg      = cfg,
						proto    = self.proto,
						addrfile = str(self.autosign_viewkey_addr_file) if self.cfg.autosign else self.uargs.infile,
						key_address_validity_check = True,
						skip_chksum_msg = True)
					break
				except:
					if first_try:
						msg(f'Attempting to open ‘{self.uargs.infile}’ as key-address list')
						continue
					raise

		self.create_addr_data()

		if not self.skip_wallet_check:
			check_wallets()

		if self.start_daemon and not self.cfg.no_start_wallet_daemon:
			asyncio.run(self.restart_wallet_daemon())

	@classmethod
	def get_idx_from_fn(cls, fn):
		return int(re.match(r'[0-9a-fA-F]{8}-(\d+)-Monero(WatchOnly)?Wallet.*', fn.name)[1])

	def pre_init_action(self):
		if self.cfg.skip_empty_accounts:
			msg(orange('Skipping display of empty accounts where applicable'))
		if self.cfg.skip_empty_addresses:
			msg(orange('Skipping display of empty used addresses where applicable'))

	def get_coin_daemon_rpc(self):

		host, port = self.cfg.daemon.split(':') if self.cfg.daemon else ('localhost', self.wd.monerod_port)

		from ...daemon import CoinDaemon
		return MoneroRPCClient(
			cfg    = self.cfg,
			proto  = self.proto,
			daemon = CoinDaemon(self.cfg, 'xmr'),
			host   = host,
			port   = int(port),
			user   = None,
			passwd = None)

	@property
	def autosign_viewkey_addr_file(self):
		from ...addrfile import ViewKeyAddrFile
		flist = [f for f in self.asi.xmr_dir.iterdir() if f.name.endswith(ViewKeyAddrFile.ext)]
		if len(flist) != 1:
			die(2,
				'{a} viewkey-address files found in autosign mountpoint directory ‘{b}’!\n'.format(
					a = 'Multiple' if flist else 'No',
					b = self.asi.xmr_dir
				)
				+ 'Have you run ‘mmgen-autosign setup’ on your offline machine with the --xmrwallets option?'
			)
		else:
			return flist[0]

	def create_addr_data(self):
		if self.uargs.wallets:
			idxs = AddrIdxList(self.uargs.wallets)
			self.addr_data = [d for d in self.kal.data if d.idx in idxs]
			if len(self.addr_data) != len(idxs):
				die(1, f'List {self.uargs.wallets!r} contains addresses not present in supplied key-address file')
		else:
			self.addr_data = self.kal.data

	async def restart_wallet_daemon(self):
		atexit.register(lambda: asyncio.run(self.stop_wallet_daemon()))
		await self.c.restart_daemon()

	async def stop_wallet_daemon(self):
		if not self.cfg.no_stop_wallet_daemon:
			try:
				await self.c.stop_daemon()
			except KeyboardInterrupt:
				ymsg('\nForce killing wallet daemon')
				self.c.daemon.force_kill = True
				self.c.daemon.stop()

	def get_wallet_fn(self, data, watch_only=None):
		if watch_only is None:
			watch_only = self.cfg.watch_only
		return Path(
			(self.cfg.wallet_dir or '.'),
			'{a}-{b}-Monero{c}Wallet{d}'.format(
				a = self.kal.al_id.sid,
				b = data.idx,
				c = 'WatchOnly' if watch_only else '',
				d = f'.{self.cfg.network}' if self.cfg.network != 'mainnet' else '')
		)

	@property
	def add_wallet_desc(self):
		return 'offline signing ' if self.cfg.offline else 'watch-only ' if self.cfg.watch_only else ''

	async def main(self):
		gmsg('\n{a}ing {b} {c}wallet{d}'.format(
			a = self.stem.capitalize(),
			b = len(self.addr_data),
			c = self.add_wallet_desc,
			d = suf(self.addr_data)))
		processed = 0
		for n, d in enumerate(self.addr_data): # [d.sec,d.addr,d.wallet_passwd,d.viewkey]
			fn = self.get_wallet_fn(d)
			gmsg('\n{a}ing wallet {b}/{c} ({d})'.format(
				a = self.stem.capitalize(),
				b = n + 1,
				c = len(self.addr_data),
				d = fn.name,
			))
			processed += await self.process_wallet(d, fn, last=n==len(self.addr_data)-1)
		gmsg(f'\n{processed} wallet{suf(processed)} {self.stem}ed\n')
		return processed

	def head_msg(self, wallet_idx, fn):
		gmsg('\n{a} {b}wallet #{c} ({d})'.format(
			a = self.action.capitalize(),
			b = self.add_wallet_desc,
			c = wallet_idx,
			d = fn.name
		))
