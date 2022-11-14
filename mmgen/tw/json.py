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
tw.json: export and import tracking wallet to JSON format
"""

import json
from collections import namedtuple

from ..util import msg,ymsg,fmt,die,make_timestamp,make_chksum_8,compare_or_die
from ..base_obj import AsyncInit
from ..objmethods import MMGenObject
from ..rpc import json_encoder
from .ctl import TwCtl

class TwJSON:

	class Base(MMGenObject):

		fn_pfx = 'mmgen-tracking-wallet-dump'

		def __new__(cls,proto,*args,**kwargs):
			return MMGenObject.__new__(proto.base_proto_subclass(TwJSON,'tw.json',cls.__name__))

		def __init__(self,proto):
			self.proto = proto
			self.coin = proto.coin_id.lower()
			self.network = proto.network
			self.keys = ['mmgen_id','address','amount','comment']
			self.entry_tuple = namedtuple('tw_entry',self.keys)

		@property
		def dump_fn(self):
			return f'{self.fn_pfx}-{self.coin}-{self.network}.json'

		def json_dump(self,data,pretty=False):
			return json.dumps(
				data,
				cls        = json_encoder,
				sort_keys  = True,
				separators = None if pretty else (',', ':'),
				indent     = 4 if pretty else None )

		def make_chksum(self,data):
			return make_chksum_8( self.json_dump(data).encode() ).lower()

		@property
		def mappings_chksum(self):
			return self.make_chksum(self.mappings_json)

		@property
		def entry_tuple_in(self):
			return namedtuple('entry_tuple_in',self.keys)

	class Import(Base,metaclass=AsyncInit):

		async def __init__(self,proto,filename,ignore_checksum=False,batch=False):

			super().__init__(proto)

			self.tw = await TwCtl( proto, mode='i', rpc_ignore_wallet=True )

			def check_network(data):
				coin,network = data['network'].split('_')
				if coin != self.coin:
					die(2,f'Coin in wallet dump is {coin.upper()}, but configured coin is {self.coin.upper()}')
				if network != self.network:
					die(2,f'Network in wallet dump is {network}, but configured network is {self.network}')

			def check_chksum(d):
				chksum = self.make_chksum(d['data'])
				if chksum != d['checksum']:
					if ignore_checksum:
						ymsg(f'Warning: ignoring incorrect checksum {chksum}')
					else:
						die(3,'File checksum incorrect! ({} != {})'.format(chksum,d['checksum']))

			def verify_data(d):
				check_network(d['data'])
				check_chksum(d)
				compare_or_die(
					self.mappings_chksum,           'computed mappings checksum',
					d['data']['mappings_checksum'], 'saved checksum' )

			if not await self.check_and_create_wallet():
				return True

			from ..fileutil import get_data_from_file
			self.data = json.loads(get_data_from_file(filename,quiet=True))
			self.keys = self.data['data']['entries_keys']
			self.entries = await self.get_entries()

			verify_data(self.data)

			addrs = await self.do_import(batch)

			await self.tw.rescan_addresses(addrs)

		async def check_and_create_wallet(self):

			if await self.tracking_wallet_exists:
				die(3,
					f'Existing {self.tw.rpc.daemon.desc} wallet detected!\n' +
					'It must be moved, or backed up and securely deleted, before running this command' )

			msg('\n'+fmt(self.info_msg.strip(),indent='  '))

			from ..ui import keypress_confirm
			if not keypress_confirm('Continue?'):
				msg('Exiting at user request')
				return False

			if not await self.create_tracking_wallet():
				die(3,'Wallet could not be created')

			return True

	class Export(Base,metaclass=AsyncInit):

		async def __init__(self,proto,include_amts=True,pretty=False):

			super().__init__(proto)

			if not include_amts:
				self.keys.remove('amount')

			self.tw = await TwCtl( proto )

			self.entries = await self.get_entries()

			data = {
				'id': 'mmgen_tracking_wallet',
				'version': 1,
				'network': f'{self.coin}_{self.network}',
				'blockheight': self.tw.rpc.blockcount,
				'time': make_timestamp(),
				'mappings_checksum': self.mappings_chksum,
				'entries_keys': self.keys,
				'entries': await self.entries_out,
				'num_entries': self.num_entries,
			}
			if include_amts:
				data['value'] = await self.total

			from ..fileutil import write_data_to_file
			write_data_to_file(
				outfile = self.dump_fn,
				data = self.json_dump(
					{
						'checksum': self.make_chksum(data),
						'data': data
					},
					pretty = pretty ),
				desc = f'tracking wallet JSON data' )
