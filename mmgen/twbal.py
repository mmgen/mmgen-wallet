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

from .color import red,green
from .util import altcoin_subclass
from .base_obj import AsyncInit
from .objmethods import MMGenObject
from .rpc import rpc_init
from .tw import get_tw_label

class TwGetBalance(MMGenObject,metaclass=AsyncInit):

	fs = '{w:13} {u:<16} {p:<16} {c}'

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(altcoin_subclass(cls,proto,'twbal'))

	async def __init__(self,proto,minconf,quiet):

		self.minconf = minconf
		self.quiet = quiet
		self.data = {k:[proto.coin_amt('0')] * 4 for k in ('TOTAL','Non-MMGen','Non-wallet')}
		self.rpc = await rpc_init(proto)
		self.proto = proto
		await self.create_data()

	async def create_data(self):
		# 0: unconfirmed, 1: below minconf, 2: confirmed, 3: spendable (privkey in wallet)
		lbl_id = ('account','label')['label_api' in self.rpc.caps]
		for d in await self.rpc.call('listunspent',0):
			lbl = get_tw_label(self.proto,d[lbl_id])
			if lbl:
				if lbl.mmid.type == 'mmgen':
					key = lbl.mmid.obj.sid
					if key not in self.data:
						self.data[key] = [self.proto.coin_amt('0')] * 4
				else:
					key = 'Non-MMGen'
			else:
				lbl,key = None,'Non-wallet'

			amt = self.proto.coin_amt(d['amount'])

			if not d['confirmations']:
				self.data['TOTAL'][0] += amt
				self.data[key][0] += amt

			conf_level = (1,2)[d['confirmations'] >= self.minconf]

			self.data['TOTAL'][conf_level] += amt
			self.data[key][conf_level] += amt

			if d['spendable']:
				self.data[key][3] += amt

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
