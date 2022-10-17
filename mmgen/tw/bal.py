#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
twbal: Tracking wallet getbalance class for the MMGen suite
"""

from ..color import red,green
from ..base_obj import AsyncInit
from ..objmethods import MMGenObject
from ..rpc import rpc_init

class TwGetBalance(MMGenObject,metaclass=AsyncInit):

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(proto.base_proto_subclass(cls,'tw','bal'))

	async def __init__(self,proto,minconf,quiet):

		self.minconf = minconf
		self.quiet = quiet
		self.data = {k:[proto.coin_amt('0')] * 4 for k in ('TOTAL','Non-MMGen','Non-wallet')}
		self.rpc = await rpc_init(proto)
		self.proto = proto
		await self.create_data()

	def format(self):
		def gen_output():
			if self.proto.chain_name != 'mainnet':
				yield 'Chain: ' + green(self.proto.chain_name.upper())

			if self.quiet:
				yield str(self.data['TOTAL'][2] if self.data else 0)
			else:
				yield self.fs.format(
					w = 'Wallet',
					u = ' Unconfirmed',
					p = f' <{self.minconf} confirms',
					c = f' >={self.minconf} confirms' )

				for key in sorted(self.data):
					if not any(self.data[key]):
						continue
					yield self.fs.format(**dict(zip(
						('w','u','p','c'),
						[key+':'] + [a.fmt(color=True,suf=' '+self.proto.dcoin) for a in self.data[key]]
						)))

			for key,vals in list(self.data.items()):
				if key == 'TOTAL':
					continue
				if vals[3]:
					yield red(f'Warning: this wallet contains PRIVATE KEYS for {key} outputs!')

		return '\n'.join(gen_output()).rstrip()
