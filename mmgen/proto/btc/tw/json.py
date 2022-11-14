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
proto.btc.tw.json: export and import tracking wallet to JSON format
"""

from collections import namedtuple
from ....tw.json import TwJSON
from ....tw.shared import TwMMGenID

class BitcoinTwJSON(TwJSON):

	class Base(TwJSON.Base):

		@property
		def mappings_json(self):
			return self.json_dump([(e.mmgen_id,e.address) for e in self.entries])

		@property
		def num_entries(self):
			return len(self.entries)

	class Import(TwJSON.Import,Base):

		info_msg = """
			This utility will create a new tracking wallet, import the addresses from
			the JSON dump into it and update their balances. The operation may take a
			few minutes.
		"""

		@property
		async def tracking_wallet_exists(self):
			return await self.twctl.rpc.check_or_create_daemon_wallet(wallet_create=False)

		async def create_tracking_wallet(self):
			return await self.twctl.rpc.check_or_create_daemon_wallet(wallet_create=True)

		async def get_entries(self):
			entries_in = [self.entry_tuple_in(*e) for e in self.data['data']['entries']]
			return sorted(
				[self.entry_tuple(
					TwMMGenID(self.proto,d.mmgen_id),
					d.address,
					getattr(d,'amount',None),
					d.comment)
						for d in entries_in],
				key = lambda x: x.mmgen_id.sort_key )

		async def do_import(self,batch):
			import_tuple = namedtuple('import_data',['addr','twmmid','comment'])
			await self.twctl.import_address_common(
				[import_tuple(e.address, e.mmgen_id, e.comment) for e in self.entries],
				batch = batch )
			return [e.address for e in self.entries]

	class Export(TwJSON.Export,Base):

		@property
		async def addrlist(self):
			if not hasattr(self,'_addrlist'):
				from .addresses import TwAddresses
				self._addrlist = await TwAddresses(self.proto,get_data=True)
			return self._addrlist

		async def get_entries(self): # TODO: include 'received' field
			return sorted(
				[self.entry_tuple(d.twmmid.obj, d.addr, d.amt, d.comment)
					for d in (await self.addrlist).data],
				key = lambda x: x.mmgen_id.sort_key )

		@property
		async def entries_out(self):
			return [[getattr(d,k) for k in self.keys] for d in self.entries]

		@property
		async def total(self):
			return (await self.addrlist).total
