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
tw.unspent: Tracking wallet unspent outputs class for the MMGen suite
"""

from ..util import msg, suf
from ..obj import (
	ImmutableAttr,
	ListItemAttr,
	MMGenListItem,
	TwComment,
	HexStr,
	CoinTxID,
	NonNegativeInt)
from ..addr import CoinAddr
from ..amt import CoinAmtChk
from .shared import TwMMGenID, get_tw_label
from .view import TwView

class TwUnspentOutputs(TwView):

	class display_type(TwView.display_type):

		class squeezed(TwView.display_type.squeezed):
			cols = ('num', 'txid', 'vout', 'addr', 'mmid', 'comment', 'amt', 'amt2', 'date')

		class detail(TwView.display_type.detail):
			cols = ('num', 'txid', 'vout', 'addr', 'mmid', 'amt', 'amt2', 'block', 'date_time', 'comment')

	show_mmid = True
	no_rpcdata_errmsg = """
		No spendable outputs found!  Import addresses with balances into your
		watch-only wallet using 'mmgen-addrimport' and then re-run this program.
	"""
	update_widths_on_age_toggle = False
	print_output_types = ('detail',)
	mod_subpath = 'tw.unspent'

	class MMGenTwUnspentOutput(MMGenListItem):
		txid         = ListItemAttr(CoinTxID)
		vout         = ListItemAttr(NonNegativeInt)
		amt          = ImmutableAttr(CoinAmtChk, include_proto=True)
		amt2         = ListItemAttr(CoinAmtChk, include_proto=True) # the ETH balance for token account
		comment      = ListItemAttr(TwComment, reassign_ok=True)
		twmmid       = ImmutableAttr(TwMMGenID, include_proto=True)
		addr         = ImmutableAttr(CoinAddr, include_proto=True)
		confs        = ImmutableAttr(int, typeconv=False)
		date         = ListItemAttr(int, typeconv=False, reassign_ok=True)
		scriptPubKey = ImmutableAttr(HexStr)
		skip         = ListItemAttr(str, typeconv=False, reassign_ok=True)

		def __init__(self, proto, **kwargs):
			self.__dict__['proto'] = proto
			MMGenListItem.__init__(self, **kwargs)

	async def __init__(self, cfg, proto, minconf=1, addrs=[]):
		await super().__init__(cfg, proto)
		self.minconf  = minconf
		self.addrs    = addrs
		from ..cfg import gc
		self.min_cols = gc.min_screen_width

	@property
	def total(self):
		return sum(i.amt for i in self.data)

	def gen_data(self, rpc_data, lbl_id):
		for o in rpc_data:
			if not lbl_id in o:
				continue # coinbase outputs have no account field
			l = get_tw_label(self.proto, o[lbl_id])
			if l:
				if not 'amt' in o:
					o['amt'] = self.proto.coin_amt(o['amount'])
				o.update({
					'twmmid':  l.mmid,
					'comment': l.comment or '',
					'addr':    CoinAddr(self.proto, o['address']),
					'confs':   o['confirmations']
				})
				yield self.MMGenTwUnspentOutput(
					self.proto,
					**{k:v for k, v in o.items() if k in self.MMGenTwUnspentOutput.valid_attrs})

	def filter_data(self):

		data = self.data.copy()

		for d in data:
			d.skip = ''

		gkeys = {'addr': 'addr', 'twmmid': 'addr', 'txid': 'txid'}
		if self.group and self.sort_key in gkeys:
			for a, b in [(data[i], data[i+1]) for i in range(len(data)-1)]:
				for k in gkeys:
					if self.sort_key == k and getattr(a, k) == getattr(b, k):
						b.skip = gkeys[k]

		return data

	def get_column_widths(self, data, wide, interactive):

		show_mmid = self.show_mmid or wide

		# num txid vout addr [mmid] [comment] amt [amt2] date
		return self.compute_column_widths(
			widths = { # fixed cols
				'num': max(2, len(str(len(data)))+1),
				'vout': 4,
				'mmid': max(len(d.twmmid.disp) for d in data) if show_mmid else 0,
				'amt': self.amt_widths['amt'],
				'amt2': self.amt_widths.get('amt2', 0),
				'block': self.age_col_params['block'][0] if wide else 0,
				'date_time': self.age_col_params['date_time'][0] if wide else 0,
				'date': self.age_w,
				'spc': 7 if show_mmid else 5, # 7(5) spaces in fs
			},
			maxws = { # expandable cols
				'txid': self.txid_w,
				'addr': max(len(d.addr) for d in data),
				'comment': max(d.comment.screen_width for d in data) if show_mmid else 0,
			},
			minws = {
				'txid': 7,
				'addr': 10,
				'comment': len('Comment') if show_mmid else 0,
			},
			maxws_nice = {'txid':12, 'addr':16} if show_mmid else {'txid':12},
			wide = wide,
			interactive = interactive,
		)

	def squeezed_col_hdr(self, cw, fs, color):
		return fs.format(
			n = '',
			t = 'TxID',
			v = 'Vout',
			a = 'Address',
			m = 'MMGenID',
			c = 'Comment',
			A = 'Amt({})'.format(self.proto.dcoin),
			B = 'Amt({})'.format(self.proto.coin),
			d = self.age_hdr)

	def detail_col_hdr(self, cw, fs, color):
		return fs.format(
			n = '',
			t = 'TxID',
			v = 'Vout',
			a = 'Address',
			m = 'MMGenID',
			A = 'Amt({})'.format(self.proto.dcoin),
			B = 'Amt({})'.format(self.proto.coin),
			b = 'Block',
			D = 'Date/Time',
			c = 'Comment')

	def gen_squeezed_display(self, data, cw, fs, color, fmt_method):

		for n, d in enumerate(data):
			yield fs.format(
				n = str(n+1) + ')',
				t = (d.txid.fmtc('|' + '.'*(cw.txid-1), width=cw.txid, color=color) if d.skip  == 'txid'
					else d.txid.truncate(width=cw.txid, color=color)) if cw.txid else None,
				v = ' ' + d.vout.fmt(width=cw.vout-1, color=color) if cw.vout else None,
				a = d.addr.fmtc('|' + '.'*(cw.addr-1), width=cw.addr, color=color) if d.skip == 'addr'
					else d.addr.fmt(self.addr_view_pref, width=cw.addr, color=color),
				m = (d.twmmid.fmtc('.'*cw.mmid, width=cw.mmid, color=color) if d.skip == 'addr'
					else d.twmmid.fmt(width=cw.mmid, color=color)) if cw.mmid else None,
				c = d.comment.fmt2(width=cw.comment, color=color, nullrepl='-') if cw.comment else None,
				A = d.amt.fmt(color=color, iwidth=cw.iwidth, prec=self.disp_prec),
				B = d.amt2.fmt(color=color, iwidth=cw.iwidth2, prec=self.disp_prec) if cw.amt2 else None,
				d = self.age_disp(d, self.age_fmt),
			)

	def gen_detail_display(self, data, cw, fs, color, fmt_method):

		for n, d in enumerate(data):
			yield fs.format(
				n = str(n+1) + ')',
				t = d.txid.fmt(width=cw.txid, color=color) if cw.txid else None,
				v = ' ' + d.vout.fmt(width=cw.vout-1, color=color) if cw.vout else None,
				a = d.addr.fmt(self.addr_view_pref, width=cw.addr, color=color),
				m = d.twmmid.fmt(width=cw.mmid, color=color),
				A = d.amt.fmt(color=color, iwidth=cw.iwidth, prec=self.disp_prec),
				B = d.amt2.fmt(color=color, iwidth=cw.iwidth2, prec=self.disp_prec) if cw.amt2 else None,
				b = self.age_disp(d, 'block'),
				D = self.age_disp(d, 'date_time'),
				c = d.comment.fmt2(width=cw.comment, color=color, nullrepl='-'))

	def display_total(self):
		msg('\nTotal unspent: {} {} ({} output{})'.format(
			self.total.hl(),
			self.proto.dcoin,
			len(self.data),
			suf(self.data)))

	async def set_dates(self, us):
		if not self.dates_set:
			# 'blocktime' differs from 'time', is same as getblockheader['time']
			dates = [o.get('blocktime', 0)
				for o in await self.rpc.gathered_icall('gettransaction', [(o.txid, True, False) for o in us])]
			for idx, o in enumerate(us):
				o.date = dates[idx]
			self.dates_set = True

	class sort_action(TwView.sort_action):

		def s_twmmid(self, parent):
			parent.do_sort('twmmid')
			parent.show_mmid = True

	class display_action(TwView.display_action):

		def d_mmid(self, parent):
			parent.show_mmid = not parent.show_mmid

		def d_group(self, parent):
			if parent.can_group:
				parent.group = not parent.group
