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
twuo: Tracking wallet unspent outputs class for the MMGen suite
"""

import time
from collections import namedtuple

from ..globalvars import g
from ..color import red,yellow,green
from ..util import (
	msg,
	msg_r,
	die,
	capfirst,
	suf,
	fmt,
	make_timestr,
	keypress_confirm,
	line_input,
	do_pager,
	base_proto_tw_subclass
)
from ..base_obj import AsyncInit
from ..objmethods import MMGenObject
from ..obj import ImmutableAttr,ListItemAttr,MMGenListItem,TwComment,get_obj,HexStr,CoinTxID,MMGenIdx,MMGenList
from ..addr import CoinAddr,MMGenID
from ..rpc import rpc_init
from .common import TwCommon,TwMMGenID,get_tw_label

class TwUnspentOutputs(MMGenObject,TwCommon,metaclass=AsyncInit):

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(base_proto_tw_subclass(cls,proto,'unspent'))

	txid_w = 64

	class MMGenTwUnspentOutput(MMGenListItem):
		txid         = ListItemAttr(CoinTxID)
		vout         = ListItemAttr(int,typeconv=False)
		amt          = ImmutableAttr(None)
		amt2         = ListItemAttr(None)
		label        = ListItemAttr(TwComment,reassign_ok=True)
		twmmid       = ImmutableAttr(TwMMGenID,include_proto=True)
		addr         = ImmutableAttr(CoinAddr,include_proto=True)
		confs        = ImmutableAttr(int,typeconv=False)
		date         = ListItemAttr(int,typeconv=False,reassign_ok=True)
		scriptPubKey = ImmutableAttr(HexStr)
		skip         = ListItemAttr(str,typeconv=False,reassign_ok=True)

		def __init__(self,proto,**kwargs):
			self.__dict__['proto'] = proto
			MMGenListItem.__init__(self,**kwargs)

		class conv_funcs:
			def amt(self,value):
				return self.proto.coin_amt(value)
			def amt2(self,value):
				return self.proto.coin_amt(value)

	async def __init__(self,proto,minconf=1,addrs=[]):
		self.proto        = proto
		self.data         = MMGenList()
		self.show_mmid    = True
		self.minconf      = minconf
		self.addrs        = addrs
		self.rpc          = await rpc_init(proto)

		from .ctl import TrackingWallet
		self.wallet = await TrackingWallet(proto,mode='w')

	@property
	def total(self):
		return sum(i.amt for i in self.data)

	async def get_data(self,sort_key=None,reverse_sort=False):

		us_raw = await self.get_rpc_data()

		if not us_raw:
			die(0,fmt(f"""
				No spendable outputs found!  Import addresses with balances into your
				watch-only wallet using '{g.proj_name.lower()}-addrimport' and then re-run this program.
			""").strip())

		lbl_id = ('account','label')['label_api' in self.rpc.caps]

		def gen_unspent():
			for o in us_raw:
				if not lbl_id in o:
					continue # coinbase outputs have no account field
				l = get_tw_label(self.proto,o[lbl_id])
				if l:
					o.update({
						'twmmid': l.mmid,
						'label':  l.comment or '',
						'amt':    self.proto.coin_amt(o['amount']),
						'addr':   CoinAddr(self.proto,o['address']),
						'confs':  o['confirmations']
					})
					yield self.MMGenTwUnspentOutput(
						self.proto,
						**{ k:v for k,v in o.items() if k in self.MMGenTwUnspentOutput.valid_attrs } )

		self.data = MMGenList(gen_unspent())

		if not self.data:
			die(1,self.no_data_errmsg)

		self.do_sort(key=sort_key,reverse=reverse_sort)

	def get_display_constants(self):
		data = self.data
		for i in data:
			i.skip = ''

		# allow for 7-digit confirmation nums
		col1_w = max(3,len(str(len(data)))+1) # num + ')'
		mmid_w = max(len(('',i.twmmid)[i.twmmid.type=='mmgen']) for i in data) or 12 # DEADBEEF:S:1
		max_acct_w = max(i.label.screen_width for i in data) + mmid_w + 1
		max_btcaddr_w = max(len(i.addr) for i in data)
		min_addr_w = self.cols - self.col_adj
		addr_w = min(max_btcaddr_w + (0,1+max_acct_w)[self.show_mmid],min_addr_w)
		acct_w = min(max_acct_w, max(24,addr_w-10))
		btaddr_w = addr_w - acct_w - 1
		label_w = acct_w - mmid_w - 1
		tx_w = min(self.txid_w,self.cols-addr_w-29-col1_w) # min=6 TODO
		txdots = ('','..')[tx_w < self.txid_w]

		dc = namedtuple('display_constants',['col1_w','mmid_w','addr_w','btaddr_w','label_w','tx_w','txdots'])
		return dc(col1_w,mmid_w,addr_w,btaddr_w,label_w,tx_w,txdots)

	async def format_for_display(self):
		data = self.data
		if self.has_age and self.age_fmt in self.age_fmts_date_dependent:
			await self.set_dates(self.rpc,data)
		self.set_term_columns()

		c = getattr(self,'display_constants',None)
		if not c:
			c = self.display_constants = self.get_display_constants()

		if self.group and (self.sort_key in ('addr','txid','twmmid')):
			for a,b in [(data[i],data[i+1]) for i in range(len(data)-1)]:
				for k in ('addr','txid','twmmid'):
					if self.sort_key == k and getattr(a,k) == getattr(b,k):
						b.skip = (k,'addr')[k=='twmmid']

		def gen_output():
			yield self.hdr_fmt.format(
				a = ' '.join(self.sort_info()),
				b = self.proto.dcoin,
				c = self.total.hl() if hasattr(self,'total') else None )
			if self.proto.chain_name != 'mainnet':
				yield 'Chain: '+green(self.proto.chain_name.upper())
			fs     = self.display_fs_fs.format(     cw=c.col1_w, tw=c.tx_w )
			hdr_fs = self.display_hdr_fs_fs.format( cw=c.col1_w, tw=c.tx_w )
			yield hdr_fs.format(
				n  = 'Num',
				t  = 'TXid'.ljust(c.tx_w - 2) + ' Vout',
				a  = 'Address'.ljust(c.addr_w),
				A  = f'Amt({self.proto.dcoin})'.ljust(self.disp_prec+5),
				A2 = f' Amt({self.proto.coin})'.ljust(self.disp_prec+4),
				c  = {
						'confs':     'Confs',
						'block':     'Block',
						'days':      'Age(d)',
						'date':      'Date',
						'date_time': 'Date',
					}[self.age_fmt],
				).rstrip()

			for n,i in enumerate(data):
				addr_dots = '|' + '.'*(c.addr_w-1)
				mmid_disp = MMGenID.fmtc(
					(
						'.'*c.mmid_w if i.skip == 'addr' else
						i.twmmid if i.twmmid.type == 'mmgen' else
						f'Non-{g.proj_name}'
					),
					width = c.mmid_w,
					color = True )

				if self.show_mmid:
					addr_out = '{} {}{}'.format((
						type(i.addr).fmtc(addr_dots,width=c.btaddr_w,color=True) if i.skip == 'addr' else
						i.addr.fmt(width=c.btaddr_w,color=True)
					),
						mmid_disp,
						(' ' + i.label.fmt(width=c.label_w,color=True)) if c.label_w > 0 else ''
					)
				else:
					addr_out = (
						type(i.addr).fmtc(addr_dots,width=c.addr_w,color=True) if i.skip=='addr' else
						i.addr.fmt(width=c.addr_w,color=True) )

				yield fs.format(
					n  = str(n+1)+')',
					t  = (
						'' if not i.txid else
						' ' * (c.tx_w-4) + '|...' if i.skip  == 'txid' else
						i.txid[:c.tx_w-len(c.txdots)] + c.txdots ),
					v  = i.vout,
					a  = addr_out,
					A  = i.amt.fmt(color=True,prec=self.disp_prec),
					A2 = (i.amt2.fmt(color=True,prec=self.disp_prec) if i.amt2 is not None else ''),
					c  = self.age_disp(i,self.age_fmt),
					).rstrip()

		self.fmt_display = '\n'.join(gen_output()) + '\n'
		return self.fmt_display

	async def format_for_printing(self,color=False,show_confs=True):
		if self.has_age:
			await self.set_dates(self.rpc,self.data)
		addr_w = max(len(i.addr) for i in self.data)
		mmid_w = max(len(('',i.twmmid)[i.twmmid.type=='mmgen']) for i in self.data) or 12 # DEADBEEF:S:1
		fs = self.print_fs_fs.format(
			tw = self.txid_w + 3,
			cf = '{c:<8} ' if show_confs else '',
			aw = self.proto.coin_amt.max_prec + 5 )

		def gen_output():
			yield fs.format(
				n  = 'Num',
				t  = 'Tx ID,Vout',
				a  = 'Address'.ljust(addr_w),
				m  = 'MMGen ID'.ljust(mmid_w),
				A  = f'Amount({self.proto.dcoin})',
				A2 = f'Amount({self.proto.coin})',
				c  = 'Confs',  # skipped for eth
				b  = 'Block',  # skipped for eth
				D  = 'Date',
				l  = 'Label' )

			max_lbl_len = max([len(i.label) for i in self.data if i.label] or [2])
			for n,i in enumerate(self.data):
				yield fs.format(
					n  = str(n+1) + ')',
					t  = '{},{}'.format(
							('|'+'.'*63 if i.skip == 'txid' and self.group else i.txid),
							i.vout ),
					a  = (
						'|'+'.' * addr_w if i.skip == 'addr' and self.group else
						i.addr.fmt(color=color,width=addr_w) ),
					m  = MMGenID.fmtc(
							(i.twmmid if i.twmmid.type == 'mmgen' else f'Non-{g.proj_name}'),
							width = mmid_w,
							color = color ),
					A  = i.amt.fmt(color=color),
					A2 = ( i.amt2.fmt(color=color) if i.amt2 is not None else '' ),
					c  = i.confs,
					b  = self.rpc.blockcount - (i.confs - 1),
					D  = self.age_disp(i,'date_time'),
					l  = i.label.hl(color=color) if i.label else
						TwComment.fmtc(
							s        = '',
							color    = color,
							nullrepl = '-',
							width    = max_lbl_len )
					).rstrip()

		fs2 = '{} (block #{}, {} UTC)\n{}Sort order: {}\n{}\n\nTotal {}: {}\n'
		self.fmt_print = fs2.format(
			capfirst(self.desc),
			self.rpc.blockcount,
			make_timestr(self.rpc.cur_date),
			('' if self.proto.chain_name == 'mainnet' else
			'Chain: {}\n'.format(green(self.proto.chain_name.upper())) ),
			' '.join(self.sort_info(include_group=False)),
			'\n'.join(gen_output()),
			self.proto.dcoin,
			self.total.hl(color=color) )

		return self.fmt_print

	def display_total(self):
		msg('\nTotal unspent: {} {} ({} output{})'.format(
			self.total.hl(),
			self.proto.dcoin,
			len(self.data),
			suf(self.data) ))

	def get_idx_from_user(self,action):
		msg('')
		while True:
			ret = line_input(f'Enter {self.item_desc} number (or RETURN to return to main menu): ')
			if ret == '':
				return (None,None) if action == 'a_lbl_add' else None
			n = get_obj(MMGenIdx,n=ret,silent=True)
			if not n or n < 1 or n > len(self.data):
				msg(f'Choice must be a single number between 1 and {len(self.data)}')
			else:
				if action == 'a_lbl_add':
					cur_lbl = self.data[n-1].label
					msg('Current label: {}'.format(cur_lbl.hl() if cur_lbl else '(none)'))
					while True:
						s = line_input(
							"Enter label text (or 'q' to return to main menu): ",
							insert_txt = cur_lbl )
						if s == 'q':
							return None,None
						elif s == '':
							if keypress_confirm(
									f'Removing label for {self.item_desc} #{n}.  Is this what you want?'):
								return n,s
						elif s:
							if get_obj(TwComment,s=s):
								return n,s
				else:
					if action == 'a_addr_delete':
						fs = 'Removing {} #{} from tracking wallet.  Is this what you want?'
					elif action == 'a_balance_refresh':
						fs = 'Refreshing tracking wallet {} #{}.  Is this what you want?'
					if keypress_confirm(fs.format(self.item_desc,n)):
						return n
