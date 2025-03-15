#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.btc.tw.rpc: Bitcoin base protocol tracking wallet RPC classes
"""

from ....addr import CoinAddr
from ....util import die, msg
from ....tw.shared import get_tw_label
from ....tw.rpc import TwRPC
from ....tw.ctl import label_addr_pair

class BitcoinTwRPC(TwRPC):

	async def get_label_addr_pairs(self):
		"""
		Get all the accounts in the tracking wallet and their associated addresses.
		Returns list of (label, address) tuples.
		"""
		def check_dup_mmid(acct_labels):
			mmid_prev, err = None, False
			for mmid in sorted(label.mmid for label in acct_labels if label):
				if mmid == mmid_prev:
					err = True
					msg(f'Duplicate MMGen ID ({mmid}) discovered in tracking wallet!\n')
				mmid_prev = mmid
			if err:
				die(4, 'Tracking wallet is corrupted!')

		async def get_acct_list():
			if 'label_api' in self.rpc.caps:
				return await self.rpc.call('listlabels')
			else:
				return (await self.rpc.call('listaccounts', 0, True)).keys()

		async def get_acct_addrs(acct_list):
			if 'label_api' in self.rpc.caps:
				return [list(a.keys())
					for a in await self.rpc.batch_call('getaddressesbylabel', [(k,) for k in acct_list])]
			else:
				return await self.rpc.batch_call('getaddressesbyaccount', [(a,) for a in acct_list])

		acct_labels = [get_tw_label(self.proto, a) for a in await get_acct_list()]

		if not acct_labels:
			return []

		check_dup_mmid(acct_labels)

		acct_addrs = await get_acct_addrs(acct_labels)

		for n, a in enumerate(acct_addrs):
			if len(a) != 1:
				raise ValueError(f'{a}: label {acct_labels[n]!r} has != 1 associated address!')

		return [label_addr_pair(label, CoinAddr(self.proto, addrs[0]))
			for label, addrs in zip(acct_labels, acct_addrs)]

	async def get_unspent_by_mmid(self, *, minconf=1, mmid_filter=[]):
		"""
		get unspent outputs in tracking wallet, compute balances per address
		and return a dict with elements {'twmmid': {'addr', 'lbl', 'amt'}}
		"""
		data = {}
		lbl_id = ('account', 'label')['label_api' in self.rpc.caps]
		amt0 = self.proto.coin_amt('0')

		for d in await self.rpc.call('listunspent', 0):

			if not lbl_id in d:
				continue  # skip coinbase outputs with missing account

			if d['confirmations'] < minconf:
				continue

			label = get_tw_label(self.proto, d[lbl_id])

			if label:
				lm = label.mmid
				if mmid_filter and (lm not in mmid_filter):
					continue
				if lm in data:
					if data[lm]['addr'] != d['address']:
						die(2, 'duplicate {} address ({}) for this MMGen address! ({})'.format(
							self.proto.coin,
							d['address'],
							data[lm]['addr']))
				else:
					lm.confs = d['confirmations']
					lm.txid = d['txid']
					lm.vout = d['vout']
					lm.date = None
					data[lm] = {
						'amt': amt0,
						'lbl': label,
						'addr': CoinAddr(self.proto, d['address'])}

				data[lm]['amt'] += self.proto.coin_amt(d['amount'])

		return data
