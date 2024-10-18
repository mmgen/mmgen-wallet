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
xmrwallet.ops.create: Monero wallet ops for the MMGen Suite
"""

from pathlib import Path

from ...util import msg, msg_r, gmsg, pp_msg, die
from ...addrlist import ViewKeyAddrList

from .wallet import OpWallet

class OpCreate(OpWallet):
	stem    = 'creat'
	wallet_exists = False
	opts    = ('restore_height',)

	def check_uopts(self):
		if self.cfg.restore_height != 'current':
			if int(self.cfg.restore_height or 0) < 0:
				die(1, f'{self.cfg.restore_height}: invalid value for --restore-height (less than zero)')

	async def process_wallet(self, d, fn, last):
		msg_r('') # for pexpect

		if self.cfg.restore_height == 'current':
			restore_height = self.get_coin_daemon_rpc().call_raw('get_height')['height']
		else:
			restore_height = self.cfg.restore_height

		if self.cfg.watch_only:
			ret = self.c.call(
				'generate_from_keys',
				filename       = fn.name,
				password       = d.wallet_passwd,
				address        = d.addr,
				viewkey        = d.viewkey,
				restore_height = restore_height)
		else:
			from ...xmrseed import xmrseed
			ret = self.c.call(
				'restore_deterministic_wallet',
				filename       = fn.name,
				password       = d.wallet_passwd,
				seed           = xmrseed().fromhex(d.sec.wif, tostr=True),
				restore_height = restore_height,
				language       = 'English')

		pp_msg(ret) if self.cfg.debug else msg(f'  Address: {ret["address"]}')
		return True

class OpCreateOffline(OpCreate):

	def __init__(self, cfg, uarg_tuple):

		super().__init__(cfg, uarg_tuple)

		gmsg('\nCreating viewkey-address file for watch-only wallets')
		vkal = ViewKeyAddrList(
			cfg       = self.cfg,
			proto     = self.proto,
			addrfile  = None,
			addr_idxs = self.uargs.wallets,
			seed      = self.seed_src.seed,
			skip_chksum_msg = True)
		vkf = vkal.file

		# before writing viewkey-address file, shred any old ones in the directory:
		for f in Path(self.asi.xmr_dir).iterdir():
			if f.name.endswith(vkf.ext):
				from ...fileutil import shred_file
				msg(f"\nShredding old viewkey-address file '{f}'")
				shred_file(f, verbose=self.cfg.verbose)

		vkf.write(outdir=self.asi.xmr_dir)
