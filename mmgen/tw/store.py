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
tw.store: Tracking wallet control class with store
"""

from ..util import msg, die, cached_property
from ..addr import is_coin_addr, is_mmgen_id, CoinAddr

from .shared import TwLabel
from .ctl import TwCtl, write_mode, label_addr_pair

class TwCtlWithStore(TwCtl):

	caps = ('batch',)
	data_key = 'addresses'
	use_tw_file = True

	def init_empty(self):
		self.data = {
			'coin': self.proto.coin,
			'network': self.proto.network.upper(),
			'addresses': {},
		}

	@write_mode
	async def batch_import_address(self, args_list):
		return [await self.import_address(a, label=b, rescan=c) for a, b, c in args_list]

	async def rescan_addresses(self, coin_addrs):
		pass

	@write_mode
	async def import_address(self, addr, *, label, rescan=False):
		r = self.data_root
		if addr in r:
			if not r[addr]['mmid'] and label.mmid:
				msg(f'Warning: MMGen ID {label.mmid!r} was missing in tracking wallet!')
			elif r[addr]['mmid'] != label.mmid:
				die(3, 'MMGen ID {label.mmid!r} does not match tracking wallet!')
		r[addr] = {'mmid': label.mmid, 'comment': label.comment}

	@write_mode
	async def remove_address(self, addr):
		r = self.data_root

		if is_coin_addr(self.proto, addr):
			have_match = lambda k: k == addr
		elif is_mmgen_id(self.proto, addr):
			have_match = lambda k: r[k]['mmid'] == addr
		else:
			die(1, f'{addr!r} is not an Ethereum address or MMGen ID')

		for k in r:
			if have_match(k):
				# return the addr resolved to mmid if possible
				ret = r[k]['mmid'] if is_mmgen_id(self.proto, r[k]['mmid']) else addr
				del r[k]
				self.write()
				return ret
		msg(f'Address {addr!r} not found in {self.data_root_desc!r} section of tracking wallet')
		return None

	@write_mode
	async def set_label(self, coinaddr, lbl):
		for addr, d in list(self.data_root.items()):
			if addr == coinaddr:
				d['comment'] = lbl.comment
				self.write()
				return True
		msg(f'Address {coinaddr!r} not found in {self.data_root_desc!r} section of tracking wallet')
		return False

	@property
	def sorted_list(self):
		return sorted([{
				'addr':    x[0],
				'mmid':    x[1]['mmid'],
				'comment': x[1]['comment']
			} for x in self.data_root.items() if x[0] not in ('params', 'coin')],
			key = lambda x: x['mmid'].sort_key + x['addr'])

	@property
	def mmid_ordered_dict(self):
		return dict((x['mmid'], {'addr': x['addr'], 'comment': x['comment']}) for x in self.sorted_list)

	async def get_label_addr_pairs(self):
		return [label_addr_pair(
				TwLabel(self.proto, f"{mmid} {d['comment']}"),
				CoinAddr(self.proto, d['addr'])
			) for mmid, d in self.mmid_ordered_dict.items()]

	@cached_property
	def used_addrs(self):
		from decimal import Decimal
		# TODO: for now, consider used addrs to be addrs with balance
		return ({k for k, v in self.data['addresses'].items() if Decimal(v.get('balance', 0))})
