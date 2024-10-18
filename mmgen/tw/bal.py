#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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
tw.bal: Tracking wallet getbalance class for the MMGen suite
"""

from ..base_obj import AsyncInit
from ..objmethods import MMGenObject
from ..obj import NonNegativeInt

class TwGetBalance(MMGenObject, metaclass=AsyncInit):

	def __new__(cls, cfg, proto, *args, **kwargs):
		return MMGenObject.__new__(proto.base_proto_subclass(cls, 'tw.bal'))

	async def __init__(self, cfg, proto, minconf, quiet):

		class BalanceInfo(dict):
			def __init__(self):
				amt0 = proto.coin_amt('0')
				data = {
					'unconfirmed': amt0,
					'lt_minconf': amt0,
					'ge_minconf': amt0,
					'spendable': amt0,
				}
				dict.__init__(self, **data)

		self.minconf = NonNegativeInt(minconf)
		self.balance_info = BalanceInfo
		self.quiet = quiet
		self.proto = proto
		self.data = {k:self.balance_info() for k in self.start_labels}

		if minconf < 2 and 'lt_minconf' in self.conf_cols:
			del self.conf_cols['lt_minconf']

		await self.create_data()

	def format(self, color):

		def gen_output():

			if self.quiet:
				yield str(self.data['TOTAL']['ge_minconf'] if self.data else 0)
			else:

				def get_col_iwidth(colname):
					return len(str(int(max(v[colname] for v in self.data.values())))) + iwidth_adj

				def make_col(label, col):
					return self.data[label][col].fmt(iwidth=iwidths[col], color=color)

				if color:
					from ..color import green, yellow
				else:
					from ..color import nocolor
					green = yellow = nocolor

				add_w = self.proto.coin_amt.max_prec + 1 # 1 = len('.')
				iwidth_adj = 1 # so that min iwidth (1) + add_w + iwidth_adj >= len('Unconfirmed')
				col1_w = max(len(l) for l in self.start_labels) + 1 # 1 = len(':')

				iwidths = {colname: get_col_iwidth(colname) for colname in self.conf_cols}

				net_desc = self.proto.coin + ' ' + self.proto.network.upper()
				if net_desc != 'BTC MAINNET':
					yield f'Network: {green(net_desc)}'

				yield '{lbl:{w}} {cols}'.format(
					lbl = 'Wallet',
					w = col1_w + iwidth_adj,
					cols = ' '.join(v.format(minconf=self.minconf).ljust(iwidths[k]+add_w)
						for k, v in self.conf_cols.items())).rstrip()

				from ..addr import MMGenID
				for label in sorted(self.data.keys()):
					yield '{lbl} {cols}'.format(
						lbl = yellow((label + ' ' + self.proto.coin).ljust(col1_w)) if label == 'TOTAL'
							else MMGenID.hlc((label+':').ljust(col1_w), color=color),
						cols = ' '.join(make_col(label, col) for col in self.conf_cols)
					).rstrip()

		return '\n'.join(gen_output())
