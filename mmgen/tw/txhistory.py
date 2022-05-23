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

from ..util import base_proto_subclass,fmt
from ..base_obj import AsyncInit
from ..objmethods import MMGenObject
from ..obj import CoinTxID,MMGenList,Int
from ..rpc import rpc_init
from .common import TwCommon

class TwTxHistory(MMGenObject,TwCommon,metaclass=AsyncInit):

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(base_proto_subclass(cls,proto,'tw','txhistory'))

	txid_w = 64
	show_txid = False
	show_unconfirmed = False
	show_total_amt = False
	print_hdr_fs = '{a} (block #{b}, {c} UTC)\n{d}Sort order: {e}\n{f}\n'
	age_fmts_interactive = ('confs','block','days','date','date_time')
	update_params_on_age_toggle = True
	detail_display_separator = '\n\n'
	print_output_types = ('squeezed','detail')

	async def __init__(self,proto,sinceblock=0):
		self.proto        = proto
		self.data         = MMGenList()
		self.rpc          = await rpc_init(proto)
		self.sinceblock   = Int( sinceblock if sinceblock >= 0 else self.rpc.blockcount + sinceblock )

	@property
	def no_rpcdata_errmsg(self):
		return 'No transaction history {}found!'.format(
			f'from block {self.sinceblock} ' if self.sinceblock else '')

	def set_column_params(self):
		data = self.data
		show_txid = self.show_txid
		for d in data:
			d.skip = ''

		if not hasattr(self,'varcol_maxwidths'):
			self.varcol_maxwidths = {
				'addr1': max(len(d.vouts_disp('inputs',width=None,color=False)) for d in data),
				'addr2': max(len(d.vouts_disp('outputs',width=None,color=False)) for d in data),
				'lbl':   max(len(d.label) for d in data),
			}

		# var cols: addr1 addr2 comment [txid]
		maxw = self.varcol_maxwidths

		if show_txid:
			txid_adj = 40 # we don't need much of the txid, so weight it less than other columns
			maxw.update({'txid': self.txid_w - txid_adj})
		elif 'txid' in maxw:
			del maxw['txid']

		minw = {
			'addr1': 15,
			'addr2': 15,
			'lbl': len('Comment'),
		}
		if show_txid:
			minw.update({'txid': 8})

		# fixed cols: num age amt
		col1_w = max(2,len(str(len(data)))+1) # num + ')'
		amt_w = self.disp_prec + 5
		fixed_w = col1_w + self.age_w + amt_w + sum(minw.values()) + (6 + show_txid) # one leading space in fs
		var_w = sum(maxw.values()) - sum(minw.values())

		# get actual screen width:
		self.all_maxw = fixed_w + var_w + (txid_adj if show_txid else 0)
		self.cols = min( self.get_term_columns(fixed_w), self.all_maxw )
		total_freew = self.cols - fixed_w
		varw = {k: max(maxw[k] - minw[k],0) for k in maxw}
		freew = {k: int(min(total_freew * (varw[k] / var_w), varw[k])) for k in maxw}

		varcols = set(maxw.keys())
		for k in maxw:
			freew[k] = min( total_freew - sum(freew[k2] for k2 in varcols-{k}), varw[k] )

		self.column_params = namedtuple('column_params',
			['col1','txid','addr1','amt','addr2','lbl'])(
				col1_w,
				min(
					# max txid was reduced by txid_adj, so stretch to fill available space, if any
					minw['txid'] + freew['txid'] + total_freew - sum(freew.values()),
					self.txid_w ) if 'txid' in minw else 0,
				minw['addr1'] + freew['addr1'],
				amt_w,
				minw['addr2'] + freew['addr2'],
				minw['lbl'] + freew['lbl'] )

	def gen_squeezed_display(self,cw,color):

		if self.sinceblock:
			yield f'Displaying transactions since block {self.sinceblock.hl(color=color)}'
		yield 'Only wallet-related outputs are shown'
		yield 'Comment is from first wallet address in outputs or inputs'
		if (cw.addr1 < self.varcol_maxwidths['addr1'] or
			cw.addr2 < self.varcol_maxwidths['addr2'] ):
			yield 'Due to screen width limitations, not all addresses could be displayed'
		yield ''

		hdr_fs = self.squeezed_hdr_fs_fs.format(
			nw = cw.col1,
			dw = self.age_w,
			txid_fs = f'{{i:{cw.txid}}} ' if self.show_txid else '',
			aw = cw.addr1,
			a2w = cw.addr2 )

		fs = self.squeezed_fs_fs.format(
			nw = cw.col1,
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
		for d in self.data:
			if d.confirmations > 0 or self.show_unconfirmed:
				n += 1
				yield fs.format(
					n  = str(n) + ')',
					i  = d.txid_disp( width=cw.txid, color=color ),
					d  = d.age_disp( self.age_fmt, width=self.age_w, color=color ),
					a1 = d.vouts_disp( 'inputs', width=cw.addr1, color=color ),
					A  = d.amt_disp(self.show_total_amt).fmt( prec=self.disp_prec, color=color ),
					a2 = d.vouts_disp( 'outputs', width=cw.addr2, color=color ),
					l  = d.label.fmt( width=cw.lbl, color=color ) ).rstrip()

	def gen_detail_display(self,color):

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
		for d in self.data:
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

	@staticmethod
	async def set_dates(rpc,us):
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
			parent.set_column_params()

		def d_show_unconfirmed(self,parent):
			parent.show_unconfirmed = not parent.show_unconfirmed

		def d_show_total_amt(self,parent):
			parent.show_total_amt = not parent.show_total_amt
