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
xmrwallet.ops.sync: Monero wallet ops for the MMGen Suite
"""

import time

from ...util import msg, msg_r, ymsg, die

from ..rpc import MoneroWalletRPC

from .wallet import OpWallet

class OpSync(OpWallet):
	opts = ('rescan_blockchain', 'skip_empty_accounts', 'skip_empty_addresses')

	def check_uopts(self):
		if self.cfg.rescan_blockchain and self.cfg.watch_only:
			die(1, f'Operation ‘{self.name}’ does not support --rescan-blockchain with watch-only wallets')

	def __init__(self, cfg, uarg_tuple):

		super().__init__(cfg, uarg_tuple)

		if not self.wallet_offline:
			self.dc = self.get_coin_daemon_rpc()

		self.wallets_data = {}

	async def process_wallet(self, d, fn, last):

		chain_height = self.dc.call_raw('get_height')['height']
		msg(f'  Chain height: {chain_height}')

		t_start = time.time()

		msg_r('  Opening wallet...')
		self.c.call(
			'open_wallet',
			filename = fn.name,
			password = d.wallet_passwd)
		msg('done')

		msg_r('  Getting wallet height (be patient, this could take a long time)...')
		wallet_height = self.c.call('get_height')['height']
		msg_r('\r' + ' '*68 + '\r')
		msg(f'  Wallet height: {wallet_height}        ')

		behind = chain_height - wallet_height
		if behind > 1000:
			msg_r(f'  Wallet is {behind} blocks behind chain tip.  Please be patient.  Syncing...')

		ret = self.c.call('refresh')

		if behind > 1000:
			msg('done')

		if ret['received_money']:
			msg('  Wallet has received funds')

		for i in range(2):
			wallet_height = self.c.call('get_height')['height']
			if wallet_height >= chain_height:
				break
			ymsg(f'  Wallet failed to sync (wallet height [{wallet_height}] < chain height [{chain_height}])')
			if i or not self.cfg.rescan_blockchain:
				break
			msg_r('  Rescanning blockchain, please be patient...')
			self.c.call('rescan_blockchain')
			self.c.call('refresh')
			msg('done')

		t_elapsed = int(time.time() - t_start)

		wd = MoneroWalletRPC(self, d).get_wallet_data(print=False, skip_empty_ok=True)

		from . import hl_amt
		msg('  Balance: {} Unlocked balance: {}'.format(
			hl_amt(wd.accts_data['total_balance']),
			hl_amt(wd.accts_data['total_unlocked_balance']),
		))

		self.wallets_data[fn.name] = wd

		msg(f'  Wallet height: {wallet_height}')
		msg(f'  Sync time: {t_elapsed//60:02}:{t_elapsed%60:02}')

		if not last:
			self.c.call('close_wallet')

		return wallet_height >= chain_height

	def gen_body(self, wallets_data):
		for wnum, (_, wallet_data) in enumerate(wallets_data.items()):
			yield from MoneroWalletRPC(self, self.addr_data[wnum]).gen_accts_info(
				wallet_data.accts_data,
				wallet_data.addrs_data,
				indent = '',
				skip_empty_ok = True)
			yield ''

	def post_main_success(self):

		def gen_info(data):
			yield from self.gen_body(data)

			col1_w = max(map(len, data)) + 1
			fs = '{:%s} {} {}' % col1_w
			tbals = [0, 0]
			yield fs.format('Wallet', 'Balance           ', 'Unlocked Balance')

			from . import fmt_amt
			for k in data:
				b  = data[k].accts_data['total_balance']
				ub = data[k].accts_data['total_unlocked_balance']
				yield fs.format(k + ':', fmt_amt(b), fmt_amt(ub))
				tbals[0] += b
				tbals[1] += ub

			yield fs.format('-'*col1_w, '-'*18, '-'*18)
			yield fs.format('TOTAL:', fmt_amt(tbals[0]), fmt_amt(tbals[1]))

		self.cfg._util.stdout_or_pager('\n'.join(gen_info(self.wallets_data)) + '\n')
