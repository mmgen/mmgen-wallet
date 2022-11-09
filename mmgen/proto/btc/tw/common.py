#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
proto.btc.tw.common: Bitcoin base protocol tracking wallet dependency classes
"""

from ....addr import CoinAddr
from ....util import die
from ....obj import MMGenList
from ....tw.common import get_tw_label

class BitcoinTwCommon:

	async def get_addr_label_pairs(self):
		"""
		Get all the accounts in the tracking wallet and their associated addresses.
		Returns list of (label,address) tuples.
		"""
		def check_dup_mmid(acct_labels):
			mmid_prev,err = None,False
			for mmid in sorted(label.mmid for label in acct_labels if label):
				if mmid == mmid_prev:
					err = True
					msg(f'Duplicate MMGen ID ({mmid}) discovered in tracking wallet!\n')
				mmid_prev = mmid
			if err:
				die(4,'Tracking wallet is corrupted!')

		def check_addr_array_lens(acct_pairs):
			err = False
			for label,addrs in acct_pairs:
				if not label:
					continue
				if len(addrs) != 1:
					err = True
					if len(addrs) == 0:
						msg(f'Label {label!r}: has no associated address!')
					else:
						msg(f'{addrs!r}: more than one {self.proto.coin} address in account!')
			if err:
				die(4,'Tracking wallet is corrupted!')

		# for compatibility with old mmids, must use raw RPC rather than native data for matching
		# args: minconf,watchonly, MUST use keys() so we get list, not dict
		if 'label_api' in self.rpc.caps:
			acct_list = await self.rpc.call('listlabels')
			aa = await self.rpc.batch_call('getaddressesbylabel',[(k,) for k in acct_list])
			acct_addrs = [list(a.keys()) for a in aa]
		else:
			acct_list = list((await self.rpc.call('listaccounts',0,True)).keys()) # raw list, no 'L'
			# use raw list here
			acct_addrs = await self.rpc.batch_call('getaddressesbyaccount',[(a,) for a in acct_list])
		acct_labels = MMGenList([get_tw_label(self.proto,a) for a in acct_list])
		check_dup_mmid(acct_labels)
		assert len(acct_list) == len(acct_addrs), 'len(listaccounts()) != len(getaddressesbyaccount())'
		addr_pairs = list(zip(acct_labels,acct_addrs))
		check_addr_array_lens(addr_pairs)
		return [(lbl,addrs[0]) for lbl,addrs in addr_pairs]

	async def get_unspent_by_mmid(self,minconf=1,mmid_filter=[]):
		"""
		get unspent outputs in tracking wallet, compute balances per address
		and return a dict with elements { 'twmmid': {'addr','lbl','amt'} }
		"""
		data = {}
		lbl_id = ('account','label')['label_api' in self.rpc.caps]
		amt0 = self.proto.coin_amt('0')

		for d in await self.rpc.call('listunspent',0):

			if not lbl_id in d:
				continue  # skip coinbase outputs with missing account

			if d['confirmations'] < minconf:
				continue

			label = get_tw_label(self.proto,d[lbl_id])

			if label:
				lm = label.mmid
				if mmid_filter and (lm not in mmid_filter):
					continue
				if lm in data:
					if data[lm]['addr'] != d['address']:
						die(2,'duplicate {} address ({}) for this MMGen address! ({})'.format(
							self.proto.coin,
							d['address'],
							data[lm]['addr'] ))
				else:
					lm.confs = d['confirmations']
					lm.txid = d['txid']
					lm.vout = d['vout']
					lm.date = None
					data[lm] = {
						'amt': amt0,
						'lbl': label,
						'addr': CoinAddr(self.proto,d['address']) }
				amt = self.proto.coin_amt(d['amount'])
				data[lm]['amt'] += amt

		return data
