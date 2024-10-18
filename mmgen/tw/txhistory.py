#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
tw.txhistory: Tracking wallet transaction history class for the MMGen suite
"""

from collections import namedtuple

from ..util import fmt
from ..obj import NonNegativeInt
from .view import TwView

class TwTxHistory(TwView):

	class display_type(TwView.display_type):

		class squeezed(TwView.display_type.squeezed):
			cols = ('num', 'txid', 'date', 'inputs', 'amt', 'outputs', 'comment')
			subhdr_fmt_method = 'gen_squeezed_subheader'

		class detail(TwView.display_type.detail):
			need_column_widths = False
			subhdr_fmt_method = 'gen_detail_subheader'
			colhdr_fmt_method = None
			item_separator = '\n\n'

	has_wallet = False
	show_txid = False
	show_unconfirmed = False
	show_total_amt = False
	update_widths_on_age_toggle = True
	print_output_types = ('squeezed', 'detail')
	filters = ('show_unconfirmed',)
	mod_subpath = 'tw.txhistory'

	async def __init__(self, cfg, proto, sinceblock=0):
		await super().__init__(cfg, proto)
		self.sinceblock = NonNegativeInt(sinceblock if sinceblock >= 0 else self.rpc.blockcount + sinceblock)

	@property
	def no_rpcdata_errmsg(self):
		return 'No transaction history {}found!'.format(
			f'from block {self.sinceblock} ' if self.sinceblock else '')

	def filter_data(self):
		return (d for d in self.data if d.confirmations > 0 or self.show_unconfirmed)

	def set_amt_widths(self, data):
		amts_tuple = namedtuple('amts_data', ['amt'])
		return super().set_amt_widths([amts_tuple(d.amt_disp(self.show_total_amt)) for d in data])

	def get_column_widths(self, data, wide, interactive):

		# var cols: inputs outputs comment [txid]
		if not hasattr(self, 'varcol_maxwidths'):
			self.varcol_maxwidths = {
				'inputs': max(len(d.vouts_disp(
					'inputs', width=None, color=False, addr_view_pref=self.addr_view_pref)) for d in data),
				'outputs': max(len(d.vouts_disp(
					'outputs', width=None, color=False, addr_view_pref=self.addr_view_pref)) for d in data),
				'comment': max(len(d.comment) for d in data),
			}

		maxws = self.varcol_maxwidths.copy()
		minws = {
			'inputs': 15,
			'outputs': 15,
			'comment': len('Comment'),
		}
		if self.show_txid:
			maxws['txid'] = self.txid_w
			minws['txid'] = 8
			maxws_nice = {'txid': 20}
		else:
			maxws['txid'] = 0
			minws['txid'] = 0
			maxws_nice = {}

		widths = { # fixed cols
			'num': max(2, len(str(len(data)))+1),
			'date': self.age_w,
			'amt': self.amt_widths['amt'],
			'spc': 6 + self.show_txid, # 5(6) spaces between cols + 1 leading space in fs
		}

		return self.compute_column_widths(
			widths,
			maxws,
			minws,
			maxws_nice,
			wide        = wide,
			interactive = interactive)

	def gen_squeezed_subheader(self, cw, color):
		# keep these shorter than min screen width (currently prompt width, or 65 chars)
		if self.sinceblock:
			yield f'Displaying transactions since block {self.sinceblock.hl(color=color)}'
		yield 'Only wallet-related outputs are shown'
		yield 'Comment is from first wallet address in outputs or inputs'
		if (cw.inputs < self.varcol_maxwidths['inputs'] or
			cw.outputs < self.varcol_maxwidths['outputs']):
			yield 'Note: screen is too narrow to display all inputs and outputs'

	def gen_detail_subheader(self, cw, color):
		if self.sinceblock:
			yield f'Displaying transactions since block {self.sinceblock.hl(color=color)}'
		yield 'Only wallet-related outputs are shown'

	def squeezed_col_hdr(self, cw, fs, color):
		return fs.format(
			n = '',
			t = 'TxID',
			d = self.age_hdr,
			i = 'Inputs',
			A = 'Amt({})'.format('TX' if self.show_total_amt else 'Wallet'),
			o = 'Outputs',
			c = 'Comment')

	def gen_squeezed_display(self, data, cw, fs, color, fmt_method):

		for n, d in enumerate(data, 1):
			yield fs.format(
				n = str(n) + ')',
				t = d.txid_disp(width=cw.txid, color=color) if hasattr(cw, 'txid') else None,
				d = d.age_disp(self.age_fmt, width=self.age_w, color=color),
				i = d.vouts_disp('inputs', width=cw.inputs, color=color, addr_view_pref=self.addr_view_pref),
				A = d.amt_disp(self.show_total_amt).fmt(iwidth=cw.iwidth, prec=self.disp_prec, color=color),
				o = d.vouts_disp('outputs', width=cw.outputs, color=color, addr_view_pref=self.addr_view_pref),
				c = d.comment.fmt2(width=cw.comment, color=color, nullrepl='-'))

	def gen_detail_display(self, data, cw, fs, color, fmt_method):

		fs = fmt("""
		{n}
		    Block:        [{d}] {b}
		    TxID:         [{D}] {t}
		    Value:        {A}
		    Wallet Value: {B}
		    Fee:          {f}
		    Inputs:
		        {i}
		    Outputs ({N}):
		        {o}
		""", strip_char='\t').strip()

		for n, d in enumerate(data, 1):
			yield fs.format(
				n = str(n) + ')',
				d = d.age_disp('date_time', width=None, color=None),
				b = d.blockheight_disp(color=color),
				D = d.txdate_disp('date_time'),
				t = d.txid_disp(color=color),
				A = d.amt_disp(show_total_amt=True).hl(color=color),
				B = d.amt_disp(show_total_amt=False).hl(color=color),
				f = d.fee_disp(color=color),
				i = d.vouts_list_disp('inputs', color=color, indent=' '*8, addr_view_pref=self.addr_view_pref),
				N = d.nOutputs,
				o = d.vouts_list_disp('outputs', color=color, indent=' '*8, addr_view_pref=self.addr_view_pref),
			)

	sort_disp = {
		'age':         'Age',
		'blockheight': 'Block Height',
		'amt':         'Wallet Amt',
		'total_amt':   'TX Amt',
		'txid':        'TxID',
	}

	sort_funcs = {
		'age':         lambda i: '{:010}.{:010}'.format(0xffffffff - abs(i.confirmations), i.time_received or 0),
		'blockheight': lambda i: 0 - abs(i.confirmations), # old/altcoin daemons return no 'blockheight' field
		'amt':         lambda i: i.wallet_outputs_total,
		'total_amt':   lambda i: i.outputs_total,
		'txid':        lambda i: i.txid,
	}

	async def set_dates(self, _):
		pass

	@property
	def dump_fn_pfx(self):
		return 'transaction-history' + (f'-since-block-{self.sinceblock}' if self.sinceblock else '')

	class sort_action(TwView.sort_action):

		def s_blockheight(self, parent):
			parent.do_sort('blockheight')

		def s_amt(self, parent):
			parent.do_sort('amt')
			parent.show_total_amt = False

		def s_total_amt(self, parent):
			parent.do_sort('total_amt')
			parent.show_total_amt = True

	class display_action(TwView.display_action):

		def d_show_txid(self, parent):
			parent.show_txid = not parent.show_txid

		def d_show_unconfirmed(self, parent):
			parent.show_unconfirmed = not parent.show_unconfirmed

		def d_show_total_amt(self, parent):
			parent.show_total_amt = not parent.show_total_amt
