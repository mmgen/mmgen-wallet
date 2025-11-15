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

import json
from pathlib import Path

from ..base_obj import AsyncInit
from ..obj import TwComment
from ..util import msg, die, cached_property
from ..addr import is_coin_addr, is_mmgen_id, CoinAddr

from .shared import TwMMGenID, TwLabel
from .ctl import TwCtl, write_mode, label_addr_pair

class TwCtlWithStore(TwCtl, metaclass=AsyncInit):

	caps = ('batch',)
	tw_subdir = None
	tw_fn = 'tracking-wallet.json'
	aggressive_sync = False

	async def __init__(
			self,
			cfg,
			proto,
			*,
			mode              = 'r',
			token_addr        = None,
			no_rpc            = False,
			no_wallet_init    = False,
			rpc_ignore_wallet = False):

		await super().__init__(cfg, proto, mode=mode, no_rpc=no_rpc, rpc_ignore_wallet=rpc_ignore_wallet)

		self.cur_balances = {} # cache balances to prevent repeated lookups per program invocation

		if cfg.cached_balances:
			self.use_cached_balances = True

		self.tw_dir = type(self).get_tw_dir(self.cfg, self.proto)
		self.tw_path = self.tw_dir / self.tw_fn

		if no_wallet_init:
			return

		self.init_from_wallet_file()

		if self.data['coin'] != self.proto.coin:
			fs = 'Tracking wallet coin ({}) does not match current coin ({})!'
			die('WalletFileError', fs.format(self.data['coin'], self.proto.coin))

		self.conv_types(self.data[self.data_key])

	def __del__(self):
		"""
		TwCtl instances opened in write or import mode must be explicitly destroyed with ‘del
		twuo.twctl’ and the like to ensure the instance is deleted and wallet is written before
		global vars are destroyed by the interpreter at shutdown.

		Not that this code can only be debugged by examining the program output, as exceptions
		are ignored within __del__():

			/usr/share/doc/python3.6-doc/html/reference/datamodel.html#object.__del__

		Since no exceptions are raised, errors will not be caught by the test suite.
		"""
		if getattr(self, 'mode', None) == 'w': # mode attr might not exist in this state
			self.write()
		elif self.cfg.debug:
			msg('read-only wallet, doing nothing')

	@classmethod
	def get_tw_dir(cls, cfg, proto):
		return Path(
			cfg.data_dir_root,
			cfg.test_user,
			'altcoins',
			proto.coin.lower(),
			('' if proto.network == 'mainnet' else proto.network),
			(cls.tw_subdir or ''))

	def upgrade_wallet_maybe(self):
		pass

	def conv_types(self, ad):
		for k, v in ad.items():
			if k not in ('params', 'coin'):
				v['mmid'] = TwMMGenID(self.proto, v['mmid'])
				v['comment'] = TwComment(v['comment'])

	def init_empty(self):
		self.data = {
			'coin': self.proto.coin,
			'network': self.proto.network.upper(),
			'addresses': {}}

	def init_from_wallet_file(self):
		from ..fileutil import check_or_create_dir, get_data_from_file
		check_or_create_dir(self.tw_dir)
		try:
			self.orig_data = get_data_from_file(self.cfg, self.tw_path, quiet=True)
			self.data = json.loads(self.orig_data)
		except:
			try:
				self.tw_path.stat()
			except:
				self.orig_data = ''
				self.init_empty()
				self.force_write()
			else:
				die('WalletFileError', f'File ‘{self.tw_path}’ exists but does not contain valid JSON data')
		else:
			self.upgrade_wallet_maybe()

		# ensure that wallet file is written when user exits via KeyboardInterrupt:
		if self.mode == 'w':
			import atexit
			def del_twctl(twctl):
				self.cfg._util.dmsg(f'Running exit handler del_twctl() for {twctl!r}')
				del twctl
			atexit.register(del_twctl, self)

	@write_mode
	async def batch_import_address(self, args_list):
		return [await self.import_address(a, label=b, rescan=c) for a, b, c in args_list]

	async def rescan_addresses(self, coin_addrs):
		pass

	@write_mode
	async def import_address(self, addr, *, label, rescan=False):
		r = self.data_root
		if addr in r:
			if self.check_import_mmid(addr, r[addr]['mmid'], label.mmid):
				r[addr]['mmid'] = label.mmid
			if label.comment: # overwrite existing comment only if new comment not empty
				r[addr]['comment'] = label.comment
		else:
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

	@property
	def data_root(self):
		return self.data[self.data_key]

	@property
	def data_root_desc(self):
		return self.data_key

	def cache_balance(self, addr, bal, *, session_cache, data_root, force=False):
		if force or addr not in session_cache:
			session_cache[addr] = str(bal)
			if addr in data_root:
				data_root[addr]['balance'] = str(bal)
				if self.aggressive_sync:
					self.write()

	def get_cached_balance(self, addr, session_cache, data_root):
		if addr in session_cache:
			return self.proto.coin_amt(session_cache[addr])
		if self.use_cached_balances:
			return self.proto.coin_amt(
				data_root[addr]['balance'] if addr in data_root and 'balance' in data_root[addr]
				else '0')

	async def get_balance(self, addr, *, force_rpc=False, block='latest'):
		ret = None if force_rpc else self.get_cached_balance(addr, self.cur_balances, self.data_root)
		if ret is None:
			ret = await self.rpc_get_balance(addr, block=block)
			if ret is not None:
				self.cache_balance(addr, ret, session_cache=self.cur_balances, data_root=self.data_root)
		return ret

	def force_write(self):
		mode_save = self.mode
		self.mode = 'w'
		self.write()
		self.mode = mode_save

	@write_mode
	def write_changed(self, data, quiet):
		from ..fileutil import write_data_to_file
		write_data_to_file(
			self.cfg,
			self.tw_path,
			data,
			desc              = f'{self.base_desc} data',
			ask_overwrite     = False,
			ignore_opt_outdir = True,
			quiet             = quiet,
			check_data        = True, # die if wallet has been altered by another program
			cmp_data          = self.orig_data)

		self.orig_data = data

	def write(self, *, quiet=True):
		self.cfg._util.dmsg(f'write(): checking if {self.desc} data has changed')

		wdata = json.dumps(self.data)
		if self.orig_data != wdata:
			self.write_changed(wdata, quiet=quiet)
		elif self.cfg.debug:
			msg('Data is unchanged\n')
