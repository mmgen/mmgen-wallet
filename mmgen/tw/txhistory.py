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
tw.txhistory: Tracking wallet transaction history class for the MMGen suite
"""

from collections import namedtuple

from ..util import fmt
from ..base_obj import AsyncInit
from ..objmethods import MMGenObject
from ..obj import CoinTxID,MMGenList,Int
from ..rpc import rpc_init
from .common import TwCommon

class TwTxHistory(MMGenObject,TwCommon,metaclass=AsyncInit):

	class display_type(TwCommon.display_type):

		class detail(TwCommon.display_type.detail):
			need_column_widths = False
			item_separator = '\n\n'

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(proto.base_proto_subclass(cls,'tw','txhistory'))

	txid_w = 64
	show_txid = False
	show_unconfirmed = False
	show_total_amt = False
	age_fmts_interactive = ('confs','block','days','date','date_time')
	update_widths_on_age_toggle = True
	print_output_types = ('squeezed','detail')
	filters = ('show_unconfirmed',)

	async def __init__(self,proto,sinceblock=0):
		self.proto        = proto
		self.data         = MMGenList()
		self.rpc          = await rpc_init(proto)
		self.sinceblock   = Int( sinceblock if sinceblock >= 0 else self.rpc.blockcount + sinceblock )

	@property
	def no_rpcdata_errmsg(self):
		return 'No transaction history {}found!'.format(
			f'from block {self.sinceblock} ' if self.sinceblock else '')

	def get_column_widths(self,data,wide=False):

		# var cols: addr1 addr2 comment [txid]
		if not hasattr(self,'varcol_maxwidths'):
			self.varcol_maxwidths = {
				'addr1': max(len(d.vouts_disp('inputs',width=None,color=False)) for d in data),
				'addr2': max(len(d.vouts_disp('outputs',width=None,color=False)) for d in data),
				'comment': max(len(d.comment) for d in data),
			}

		maxws = self.varcol_maxwidths.copy()
		minws = {
			'addr1': 15,
			'addr2': 15,
			'comment': len('Comment'),
		}
		if self.show_txid:
			maxws['txid'] = self.txid_w
			minws['txid'] = 8
			maxws_nice = {'txid': 20}
		else:
			maxws_nice = {}

		widths = { # fixed cols
			'num': max(2,len(str(len(data)))+1),
			'age': self.age_w,
			'amt': self.disp_prec + 5,
			'spc': 6 + self.show_txid, # 5(6) spaces between cols + 1 leading space in fs
		}

		return self.compute_column_widths(widths,maxws,minws,maxws_nice,wide=wide)

	def gen_squeezed_display(self,data,cw,color):

		if self.sinceblock:
			yield f'Displaying transactions since block {self.sinceblock.hl(color=color)}'
		yield 'Only wallet-related outputs are shown'
		yield 'Comment is from first wallet address in outputs or inputs'
		if (cw.addr1 < self.varcol_maxwidths['addr1'] or
			cw.addr2 < self.varcol_maxwidths['addr2'] ):
			yield 'Due to screen width limitations, not all addresses could be displayed'
		yield ''

		hdr_fs = self.squeezed_hdr_fs_fs.format(
			nw = cw.num,
			dw = self.age_w,
			txid_fs = f'{{i:{cw.txid}}} ' if self.show_txid else '',
			aw = cw.addr1,
			a2w = cw.addr2 )

		fs = self.squeezed_fs_fs.format(
			nw = cw.num,
			dw = self.age_w,
			txid_fs = f'{{i:{cw.txid}}} ' if self.show_txid else '' )

		yield hdr_fs.format(
			n  = '',
			i  = 'TxID',
			d  = self.age_hdr,
			a1 = 'Inputs',
			A  = 'Amt({})'.format('TX' if self.show_total_amt else 'Wallet').ljust(cw.amt),
			a2 = 'Outputs',
			l  = 'Comment' ).rstrip()

		n = 0
		for d in data:
			if d.confirmations > 0 or self.show_unconfirmed:
				n += 1
				yield fs.format(
					n  = str(n) + ')',
					i  = d.txid_disp( width=cw.txid, color=color ) if hasattr(cw,'txid') else None,
					d  = d.age_disp( self.age_fmt, width=self.age_w, color=color ),
					a1 = d.vouts_disp( 'inputs', width=cw.addr1, color=color ),
					A  = d.amt_disp(self.show_total_amt).fmt( prec=self.disp_prec, color=color ),
					a2 = d.vouts_disp( 'outputs', width=cw.addr2, color=color ),
					l  = d.comment.fmt( width=cw.comment, color=color ) ).rstrip()

	def gen_detail_display(self,data,cw,color):

		yield (
			(f'Displaying transactions since block {self.sinceblock.hl(color=color)}\n'
				if self.sinceblock else '')
			+ 'Only wallet-related outputs are shown'
		)

		fs = fmt("""
		{n}
		    Block:        [{d}] {b}
		    TxID:         [{D}] {i}
		    Value:        {A1}
		    Wallet Value: {A2}
		    Fee:          {f}
		    Inputs:
		        {a1}
		    Outputs ({oc}):
		        {a2}
		""",strip_char='\t').strip()

		n = 0
		for d in data:
			if d.confirmations > 0 or self.show_unconfirmed:
				n += 1
				yield fs.format(
					n  = str(n) + ')',
					d  = d.age_disp( 'date_time', width=None, color=None ),
					b  = d.blockheight_disp(color=color),
					D  = d.txdate_disp( 'date_time' ),
					i  = d.txid_disp( width=None, color=color ),
					A1 = d.amt_disp(True).hl( color=color ),
					A2 = d.amt_disp(False).hl( color=color ),
					f  = d.fee_disp( color=color ),
					a1 = d.vouts_list_disp( 'inputs', color=color, indent=' '*8 ),
					oc = d.nOutputs,
					a2 = d.vouts_list_disp( 'outputs', color=color, indent=' '*8 ),
				)

	sort_disp = {
		'age':         'Age',
		'blockheight': 'Block Height',
		'amt':         'Wallet Amt',
		'total_amt':   'TX Amt',
		'txid':        'TxID',
	}

	sort_funcs = {
		'age':         lambda i: i.time,
		'blockheight': lambda i: 0 - abs(i.confirmations), # old/altcoin daemons return no 'blockheight' field
		'amt':         lambda i: i.wallet_outputs_total,
		'total_amt':   lambda i: i.outputs_total,
		'txid':        lambda i: i.txid,
	}

	async def set_dates(self,us):
		pass

	@property
	def dump_fn_pfx(self):
		return 'transaction-history' + (f'-since-block-{self.sinceblock}' if self.sinceblock else '')

	class action(TwCommon.action):

		def s_amt(self,parent):
			parent.do_sort('amt')
			parent.show_total_amt = False

		def s_total_amt(self,parent):
			parent.do_sort('total_amt')
			parent.show_total_amt = True

		def d_show_txid(self,parent):
			parent.show_txid = not parent.show_txid

		def d_show_unconfirmed(self,parent):
			parent.show_unconfirmed = not parent.show_unconfirmed

		def d_show_total_amt(self,parent):
			parent.show_total_amt = not parent.show_total_amt
