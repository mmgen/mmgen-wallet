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
proto.eth.tw.json: export and import tracking wallet to JSON format
"""

from collections import namedtuple
from ....tw.json import TwJSON
from ....tw.shared import TwMMGenID

class EthereumTwJSON(TwJSON):

	class Base(TwJSON.Base):

		def __init__(self, proto, *args, **kwargs):

			self.params_keys = ['symbol', 'decimals']
			self.params_tuple = namedtuple('params_tuple', self.params_keys)

			super().__init__(proto, *args, **kwargs)

		@property
		def mappings_json(self):

			def gen_mappings(data):
				for d in data:
					yield (d.mmgen_id, d.address) if hasattr(d, 'mmgen_id') else d

			return self.json_dump({
				'accounts': list(gen_mappings(self.entries['accounts'])),
				'tokens': {k: list(gen_mappings(v)) for k, v in self.entries['tokens'].items()}})

		@property
		def num_entries(self):
			return len(self.entries['accounts']) + len(self.entries['tokens'])

	class Import(TwJSON.Import, Base):

		info_msg = """
			This utility will recreate a new tracking wallet from the supplied JSON dump.
			If the dump contains address balances, balances will be updated from it.
		"""

		@property
		async def tracking_wallet_exists(self):
			return bool(self.twctl.data['accounts'] or self.twctl.data['tokens'])

		async def create_tracking_wallet(self):
			return True

		async def get_entries(self):

			edata = self.data['data']['entries']

			def gen_entries(data):
				for d in data:
					if len(d) == 2:
						yield self.params_tuple(*d)
					else:
						e = self.entry_tuple_in(*d)
						yield self.entry_tuple(
							TwMMGenID(self.proto, e.mmgen_id),
							e.address,
							getattr(e, 'amount', '0'),
							e.comment)

			def gen_token_entries():
				for token_addr, token_data in edata['tokens'].items():
					yield (
						token_addr,
						list(gen_entries(token_data)),
					)

			return {
				'accounts': list(gen_entries(edata['accounts'])),
				'tokens': dict(list(gen_token_entries()))}

		async def do_import(self, batch):

			from ....obj import TwComment

			def gen_data(data):
				for d in data:
					if hasattr(d, 'address'):
						yield (
							d.address,
							{'mmid': d.mmgen_id, 'comment': TwComment(d.comment)}
							| ({} if d.amount is None else {'balance': d.amount}))
					else:
						yield ('params', {'symbol': d.symbol, 'decimals': d.decimals})

			self.twctl.data = { # keys must be in correct order
				'coin': self.coin.upper(),
				'network': self.network.upper(),
				'accounts': dict(gen_data(self.entries['accounts'])),
				'tokens': {k: dict(gen_data(v)) for k, v in self.entries['tokens'].items()}}
			self.twctl.write(quiet=False)

	class Export(TwJSON.Export, Base):

		async def get_entries(self, *, include_amts=True):

			def gen_data(data):
				for k, v in data.items():
					if k == 'params':
						yield self.params_tuple(**v)
					elif include_amts:
						yield self.entry_tuple(TwMMGenID(self.proto, v['mmid']), k, v.get('balance'), v['comment'])
					else:
						yield self.entry_tuple_in(TwMMGenID(self.proto, v['mmid']), k, v['comment'])

			def gen_token_data():
				for token_addr, token_data in self.twctl.data['tokens'].items():
					yield (
						token_addr,
						sorted(
							gen_data(token_data),
							key = lambda x: x.mmgen_id.sort_key if hasattr(x, 'mmgen_id') else '+'
						)
					)

			return {
				'accounts': sorted(
					gen_data(self.twctl.data['accounts']),
					key = lambda x: x.mmgen_id.sort_key),
				'tokens': dict(sorted(gen_token_data()))}

		@property
		async def entries_out(self):
			return await self.get_entries(include_amts='amount' in self.keys)

		@property
		async def total(self):
			return sum(self.proto.coin_amt(i.amount) for i in self.entries['accounts']) or self.proto.coin_amt('0')
