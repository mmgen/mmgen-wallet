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
base_proto.bitcoin.twaddrs: Bitcoin base protocol tracking wallet address list class
"""

from ....util import msg,die
from ....obj import MMGenList
from ....addr import CoinAddr
from ....rpc import rpc_init
from ....tw.addrs import TwAddrList
from ....tw.common import get_tw_label

class BitcoinTwAddrList(TwAddrList):

	has_age = True

	async def __init__(self,proto,usr_addr_list,minconf,showempty,showbtcaddrs,all_labels,wallet=None):

		def check_dup_mmid(acct_labels):
			mmid_prev,err = None,False
			for mmid in sorted(a.mmid for a in acct_labels if a):
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
						msg(f'{addrs!r}: more than one {proto.coin} address in account!')
			if err:
				die(4,'Tracking wallet is corrupted!')

		self.rpc   = await rpc_init(proto)
		self.total = proto.coin_amt('0')
		self.proto = proto

		lbl_id = ('account','label')['label_api' in self.rpc.caps]
		for d in await self.rpc.call('listunspent',0):
			if not lbl_id in d:
				continue  # skip coinbase outputs with missing account
			if d['confirmations'] < minconf:
				continue
			label = get_tw_label(proto,d[lbl_id])
			if label:
				lm = label.mmid
				if usr_addr_list and (lm not in usr_addr_list):
					continue
				if lm in self:
					if self[lm]['addr'] != d['address']:
						die(2,'duplicate {} address ({}) for this MMGen address! ({})'.format(
							proto.coin,
							d['address'],
							self[lm]['addr'] ))
				else:
					lm.confs = d['confirmations']
					lm.txid = d['txid']
					lm.date = None
					self[lm] = {
						'amt': proto.coin_amt('0'),
						'lbl': label,
						'addr': CoinAddr(proto,d['address']) }
				amt = proto.coin_amt(d['amount'])
				self[lm]['amt'] += amt
				self.total += amt

		# We use listaccounts only for empty addresses, as it shows false positive balances
		if showempty or all_labels:
			# for compatibility with old mmids, must use raw RPC rather than native data for matching
			# args: minconf,watchonly, MUST use keys() so we get list, not dict
			if 'label_api' in self.rpc.caps:
				acct_list = await self.rpc.call('listlabels')
				aa = await self.rpc.batch_call('getaddressesbylabel',[(k,) for k in acct_list])
				acct_addrs = [list(a.keys()) for a in aa]
			else:
				acct_list = list((await self.rpc.call('listaccounts',0,True)).keys()) # raw list, no 'L'
				acct_addrs = await self.rpc.batch_call('getaddressesbyaccount',[(a,) for a in acct_list]) # use raw list here
			acct_labels = MMGenList([get_tw_label(proto,a) for a in acct_list])
			check_dup_mmid(acct_labels)
			assert len(acct_list) == len(acct_addrs),(
				'listaccounts() and getaddressesbyaccount() not equal in length')
			addr_pairs = list(zip(acct_labels,acct_addrs))
			check_addr_array_lens(addr_pairs)
			for label,addr_arr in addr_pairs:
				if not label:
					continue
				if all_labels and not showempty and not label.comment:
					continue
				if usr_addr_list and (label.mmid not in usr_addr_list):
					continue
				if label.mmid not in self:
					self[label.mmid] = { 'amt':proto.coin_amt('0'), 'lbl':label, 'addr':'' }
					if showbtcaddrs:
						self[label.mmid]['addr'] = CoinAddr(proto,addr_arr[0])
