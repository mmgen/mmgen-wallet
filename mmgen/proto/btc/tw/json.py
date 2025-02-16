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
proto.btc.tw.json: export and import tracking wallet to JSON format
"""

from collections import namedtuple
from ....tw.json import TwJSON
from ....tw.shared import TwMMGenID

class BitcoinTwJSON(TwJSON):

	class Base(TwJSON.Base):

		can_prune = True

		@property
		def mappings_json(self):
			return self.json_dump([(e.mmgen_id, e.address) for e in self.entries])

		@property
		def num_entries(self):
			return len(self.entries)

	class Import(TwJSON.Import, Base):

		info_msg = """
			This utility will create a new tracking wallet, import the addresses from
			the JSON dump into it and update their balances. The operation may take a
			few minutes.
		"""

		blockchain_rescan_warning = """
			Balances have been updated in the new tracking wallet.  However, the wallet
			is unaware of the used state of any spent addresses without balances, which
			creates the danger of address reuse, especially when automatic change address
			selection is in effect.

			To avoid this danger and restore full tracking wallet functionality, rescan
			the blockchain for used addresses by running ‘mmgen-tool rescan_blockchain’.
		"""

		@property
		async def tracking_wallet_exists(self):
			return await self.twctl.rpc.tracking_wallet_exists

		async def create_tracking_wallet(self):
			try:
				await self.twctl.rpc.check_or_create_daemon_wallet()
				return True
			except:
				return False

		async def get_entries(self):
			entries_in = [self.entry_tuple_in(*e) for e in self.data['data']['entries']]
			return sorted(
				[self.entry_tuple(
					TwMMGenID(self.proto, d.mmgen_id),
					d.address,
					getattr(d, 'amount', None),
					d.comment)
						for d in entries_in],
				key = lambda x: x.mmgen_id.sort_key)

		async def do_import(self, batch):
			import_tuple = namedtuple('import_data', ['addr', 'twmmid', 'comment'])
			await self.twctl.import_address_common(
				[import_tuple(e.address, e.mmgen_id, e.comment) for e in self.entries],
				batch = batch)
			return [e.address for e in self.entries]

	class Export(TwJSON.Export, Base):

		@property
		async def addrlist(self):
			if not hasattr(self, '_addrlist'):
				if self.prune:
					from .prune import TwAddressesPrune
					self._addrlist = al = await TwAddressesPrune(
						self.cfg,
						self.proto,
						get_data  = True,
						warn_used = self.warn_used)
					await al.view_filter_and_sort()
					self.pruned = al.do_prune()
				else:
					from .addresses import TwAddresses
					self._addrlist = await TwAddresses(self.cfg, self.proto, get_data=True)
			return self._addrlist

		async def get_entries(self): # TODO: include 'received' field
			return sorted(
				[self.entry_tuple(d.twmmid, d.addr, d.amt, d.comment)
					for d in (await self.addrlist).data],
				key = lambda x: x.mmgen_id.sort_key)

		@property
		async def entries_out(self):
			return [[getattr(d, k) for k in self.keys] for d in self.entries]

		@property
		async def total(self):
			return (await self.addrlist).total
