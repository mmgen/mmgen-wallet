#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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
	CoinTxID,
	NonNegativeInt)
from ..addr import CoinAddr
from ..amt import CoinAmtChk
from .shared import TwMMGenID, TwLabel, get_tw_label
from .view import TwView

class TwUnspentOutputs(TwView):

	show_mmid = True
	hdr_lbl = 'tracked addresses'
	desc    = 'address balances'
	item_desc = 'address'
	item_desc_pl = 'addresses'
	no_rpcdata_errmsg = """
		No spendable outputs found!  Import addresses with balances into your
		watch-only wallet using 'mmgen-addrimport' and then re-run this program.
	"""
	update_widths_on_age_toggle = False
	print_output_types = ('detail',)
	mod_subpath = 'tw.unspent'
	dump_fn_pfx = 'balances'
	prompt_fs_in = [
		'Sort options: [a]mount, a[d]dr, [M]mgen addr, [r]everse',
		'Display options: show [m]mgen addr, r[e]draw screen',
		'View/Print: pager [v]iew, [w]ide pager view, [p]rint to file{s}',
		'Actions: [q]uit menu, [D]elete addr, add [l]abel, [R]efresh balance:']
	key_mappings = {
		'a':'s_amt',
		'd':'s_addr',
		'r':'s_reverse',
		'M':'s_twmmid',
		'm':'d_mmid',
		'e':'d_redraw',
		'p':'a_print_detail',
		'v':'a_view',
		'w':'a_view_detail',
		'l':'i_comment_add'}
	extra_key_mappings = {
		'D':'i_addr_delete',
		'R':'i_balance_refresh'}
	disp_spc = 3
	vout_w = 0

	class display_type(TwView.display_type):

		class squeezed(TwView.display_type.squeezed):
			cols = ('num', 'addr', 'mmid', 'comment', 'amt', 'amt2')

		class detail(TwView.display_type.detail):
			cols = ('num', 'addr', 'mmid', 'amt', 'amt2', 'comment')

	class MMGenTwUnspentOutput(MMGenListItem):
		valid_attrs = {'txid', 'vout', 'amt', 'amt2', 'comment', 'twmmid', 'addr', 'confs', 'skip'}
		invalid_attrs = {'proto'}
		txid    = ListItemAttr(CoinTxID)
		vout    = ListItemAttr(NonNegativeInt)
		amt     = ImmutableAttr(CoinAmtChk, include_proto=True)
		amt2    = ListItemAttr(CoinAmtChk, include_proto=True) # the ETH balance for token account
		comment = ListItemAttr(TwComment, reassign_ok=True)
		twmmid  = ImmutableAttr(TwMMGenID, include_proto=True)
		addr    = ImmutableAttr(CoinAddr, include_proto=True)
		confs   = ImmutableAttr(int, typeconv=False)
		skip    = ListItemAttr(str, typeconv=False, reassign_ok=True)

		def __init__(self, proto, **kwargs):
			self.__dict__['proto'] = proto
			MMGenListItem.__init__(self, **kwargs)

	async def __init__(self, cfg, proto, *, minconf=1, addrs=[]):
		await super().__init__(cfg, proto)
		self.minconf  = NonNegativeInt(minconf)
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
					'confs':   o['confirmations'],
					'skip':    ''})
				yield self.MMGenTwUnspentOutput(
					self.proto,
					**{k: v for k, v in o.items() if k in self.MMGenTwUnspentOutput.valid_attrs})

	async def get_rpc_data(self):
		wl = self.twctl.sorted_list
		minconf = int(self.minconf)
		block = self.twctl.rpc.get_block_from_minconf(minconf)
		if self.addrs:
			wl = [d for d in wl if d['addr'] in self.addrs]
		return [{
				'account': TwLabel(self.proto, d['mmid']+' '+d['comment']),
				'address': d['addr'],
				'amt': await self.twctl.get_balance(d['addr'], block=block),
				'confirmations': minconf,
				} for d in wl]

	def get_disp_data(self):

		for d in self.data:
			d.skip = ''

		if self.group and (e := self.sort_key) in self.groupable:
			data = self.data
			skip = self.groupable[e]
			for i in range(len(data) - 1):
				if getattr(data[i], e) == getattr(data[i + 1], e):
					data[i + 1].skip = skip

		return self.data

	def get_column_widths(self, data, *, wide):
		show_mmid = self.show_mmid or wide
		return self.column_widths_data(
			widths = { # fixed cols
				'num': max(2, len(str(len(data)))+1),
				'txid': 0,
				'vout': self.vout_w,
				'mmid': max(len(d.twmmid.disp) for d in data) if show_mmid else 0,
				'amt': self.amt_widths['amt'],
				'amt2': self.amt_widths.get('amt2', 0),
				'block': self.age_col_params['block'][0] if wide else 0,
				'date_time': self.age_col_params['date_time'][0] if wide else 0,
				'date': self.age_w,
				'spc': self.disp_spc + (2 * show_mmid) + self.has_amt2},
			maxws = { # expandable cols
				'addr': max(len(d.addr) for d in data),
				'comment': max(d.comment.screen_width for d in data) if show_mmid else 0,
			} | self.txid_max_w,
			minws = {
				'addr': 10,
				'comment': len('Comment') if show_mmid else 0,
			} | self.txid_min_w,
			maxws_nice = (
				self.nice_addr_w if show_mmid else {}
			) | self.txid_nice_w)

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
				t = (d.txid.fmtc('|' + '.'*(cw.txid-1), cw.txid, color=color) if d.skip  == 'txid'
					else d.txid.truncate(cw.txid, color=color)) if cw.txid else None,
				v = ' ' + d.vout.fmt(cw.vout-1, color=color) if cw.vout else None,
				a = d.addr.fmtc('|' + '.'*(cw.addr-1), cw.addr, color=color) if d.skip == 'addr'
					else d.addr.fmt(self.addr_view_pref, cw.addr, color=color),
				m = (d.twmmid.fmtc('.'*cw.mmid, cw.mmid, color=color) if d.skip == 'addr'
					else d.twmmid.fmt(cw.mmid, color=color)) if cw.mmid else None,
				c = d.comment.fmt2(cw.comment, color=color, nullrepl='-') if cw.comment else None,
				A = d.amt.fmt(cw.iwidth, color=color, prec=self.disp_prec),
				B = d.amt2.fmt(cw.iwidth2, color=color, prec=self.disp_prec) if cw.amt2 else None,
				d = self.age_disp(d, self.age_fmt))

	def gen_detail_display(self, data, cw, fs, color, fmt_method):

		for n, d in enumerate(data):
			yield fs.format(
				n = str(n+1) + ')',
				t = d.txid.fmt(cw.txid, color=color) if cw.txid else None,
				v = ' ' + d.vout.fmt(cw.vout-1, color=color) if cw.vout else None,
				a = d.addr.fmt(self.addr_view_pref, cw.addr, color=color),
				m = d.twmmid.fmt(cw.mmid, color=color),
				A = d.amt.fmt(cw.iwidth, color=color, prec=self.disp_prec),
				B = d.amt2.fmt(cw.iwidth2, color=color, prec=self.disp_prec) if cw.amt2 else None,
				b = self.age_disp(d, 'block'),
				D = self.age_disp(d, 'date_time'),
				c = d.comment.fmt2(cw.comment, color=color, nullrepl='-'))

	def display_total(self):
		msg('\nTotal unspent: {} {} ({} {}{})'.format(
			self.total.hl(),
			self.proto.dcoin,
			len(self.data),
			self.item_desc,
			suf(self.data)))

	async def set_dates(self, us):
		if not self.dates_set:
			# 'blocktime' differs from 'time', is same as getblockheader['time']
			dates = [o.get('blocktime', 0)
				for o in await self.rpc.gathered_icall(
					'gettransaction',
					[(o.txid, True, False) for o in us])]
			for idx, o in enumerate(us):
				o.date = dates[idx]
			self.dates_set = True

	class sort_action(TwView.sort_action):

		def s_twmmid(self, parent):
			parent.sort_data('twmmid')
			parent.show_mmid = True

	class display_action(TwView.display_action):

		def d_mmid(self, parent):
			parent.show_mmid = not parent.show_mmid

		def d_group(self, parent):
			if parent.groupable:
				parent.group = not parent.group
