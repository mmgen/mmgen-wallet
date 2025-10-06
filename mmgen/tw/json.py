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
tw.json: export and import tracking wallet to JSON format
"""

import sys, os, json
from collections import namedtuple

from ..util import msg, ymsg, fmt, suf, die, make_timestamp, make_chksum_8
from ..base_obj import AsyncInit
from ..objmethods import MMGenObject
from ..rpc.util import json_encoder
from .ctl import TwCtl

class TwJSON:

	class Base(MMGenObject):

		can_prune = False
		pruned = None
		fn_pfx = 'mmgen-tracking-wallet-dump'

		def __new__(cls, cfg, proto, *args, **kwargs):
			return MMGenObject.__new__(
				proto.base_proto_subclass(TwJSON, 'tw.json', sub_clsname=cls.__name__))

		def __init__(self, cfg, proto):
			self.cfg = cfg
			self.proto = proto
			self.coin = proto.coin_id.lower()
			self.network = proto.network
			self.keys = ['mmgen_id', 'address', 'amount', 'comment']
			self.entry_tuple = namedtuple('tw_entry', self.keys)

		@property
		def dump_fn(self):

			def get_fn(prune_id):
				return '{a}{b}-{c}-{d}.json'.format(
					a = self.fn_pfx,
					b = f'-pruned[{prune_id}]' if prune_id else '',
					c = self.coin,
					d = self.network)

			if self.pruned:
				from ..addrlist import AddrIdxList
				prune_id = AddrIdxList(idx_list=self.pruned).id_str
				fn = get_fn(prune_id)
				mf = 255 if sys.platform == 'win32' else os.statvfs(self.cfg.outdir or os.curdir).f_namemax
				if len(fn) > mf:
					fn = get_fn(f'idhash={make_chksum_8(prune_id.encode()).lower()}')
			else:
				fn = get_fn(None)

			return fn

		def json_dump(self, data, *, pretty=False):
			return json.dumps(
				data,
				cls        = json_encoder,
				sort_keys  = True,
				separators = None if pretty else (',', ':'),
				indent     = 4 if pretty else None) + ('\n' if pretty else '')

		def make_chksum(self, data):
			return make_chksum_8(self.json_dump(data).encode()).lower()

		@property
		def mappings_chksum(self):
			return self.make_chksum(self.mappings_json)

		@property
		def entry_tuple_in(self):
			return namedtuple('entry_tuple_in', self.keys)

	class Import(Base, metaclass=AsyncInit):

		blockchain_rescan_warning = None

		async def __init__(
				self,
				cfg,
				proto,
				filename,
				*,
				ignore_checksum = False,
				batch           = False):

			super().__init__(cfg, proto)

			self.twctl = await TwCtl(cfg, proto, mode='i', rpc_ignore_wallet=True)

			def check_network(data):
				coin, network = data['network'].split('_')
				if coin != self.coin:
					die(2, f'Coin in wallet dump is {coin.upper()}, but configured coin is {self.coin.upper()}')
				if network != self.network:
					die(2, f'Network in wallet dump is {network}, but configured network is {self.network}')

			def check_chksum(d):
				chksum = self.make_chksum(d['data'])
				if chksum != d['checksum']:
					if ignore_checksum:
						ymsg(f'Warning: ignoring incorrect checksum {chksum}')
					else:
						die(3, f'File checksum incorrect! ({chksum} != {d["checksum"]})')

			def verify_data(d):
				check_network(d['data'])
				check_chksum(d)
				self.cfg._util.compare_or_die(
					val1  = self.mappings_chksum,
					val2  = d['data']['mappings_checksum'],
					desc1 = 'computed mappings checksum',
					desc2 = 'saved checksum')

			if not await self.check_and_create_wallet():
				return

			from ..fileutil import get_data_from_file
			self.data = json.loads(get_data_from_file(self.cfg, filename, quiet=True))
			self.keys = self.data['data']['entries_keys']
			self.entries = await self.get_entries()

			verify_data(self.data)

			addrs = await self.do_import(batch)

			await self.twctl.rescan_addresses(addrs)

			if self.blockchain_rescan_warning:
				ymsg('\n' + fmt(self.blockchain_rescan_warning.strip(), indent='  '))

		async def check_and_create_wallet(self):

			if await self.tracking_wallet_exists:
				die(3,
					f'Existing {self.twctl.rpc.daemon.desc} wallet detected!\n' +
					'It must be moved, or backed up and securely deleted, before running this command')

			msg('\n'+fmt(self.info_msg.strip(), indent='  '))

			from ..ui import keypress_confirm
			if not keypress_confirm(self.cfg, 'Continue?'):
				msg('Exiting at user request')
				return False

			if not await self.create_tracking_wallet():
				die(3, 'Wallet could not be created')

			return True

	class Export(Base, metaclass=AsyncInit):

		async def __init__(
				self,
				cfg,
				proto,
				*,
				include_amts    = True,
				pretty          = False,
				prune           = False,
				warn_used       = False,
				force_overwrite = False):

			if prune and not self.can_prune:
				die(1, f'Pruning not supported for {proto.name} protocol')

			self.prune = prune
			self.warn_used = warn_used

			super().__init__(cfg, proto)

			if not include_amts:
				self.keys.remove('amount')

			self.twctl = await TwCtl(cfg, proto)

			self.entries = await self.get_entries()

			if self.prune:
				msg('Pruned {} address{}'.format(len(self.pruned), suf(self.pruned, 'es')))

			msg('Exporting {} address{}'.format(self.num_entries, suf(self.num_entries, 'es')))

			data = {
				'id': 'mmgen_tracking_wallet',
				'version': 1,
				'network': f'{self.coin}_{self.network}',
				'blockheight': self.twctl.rpc.blockcount,
				'time': make_timestamp(),
				'mappings_checksum': self.mappings_chksum,
				'entries_keys': self.keys,
				'entries': await self.entries_out,
				'num_entries': self.num_entries}

			if include_amts:
				data['value'] = await self.total

			from ..fileutil import write_data_to_file
			write_data_to_file(
				cfg     = self.cfg,
				outfile = self.dump_fn,
				data    = self.json_dump(
					{
						'checksum': self.make_chksum(data),
						'data': data
					},
					pretty = pretty),
				desc    = 'tracking wallet JSON data',
				ask_overwrite = not force_overwrite)
