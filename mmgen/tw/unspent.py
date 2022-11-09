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

import asyncio
from collections import namedtuple

from ..globalvars import g
from ..color import red,yellow
from ..util import msg,die,capfirst,suf,fmt
from ..base_obj import AsyncInit
from ..objmethods import MMGenObject
from ..obj import ImmutableAttr,ListItemAttr,MMGenListItem,TwComment,get_obj,HexStr,CoinTxID,MMGenList
from ..addr import CoinAddr,MMGenID
from ..rpc import rpc_init
from .common import TwCommon,TwMMGenID,get_tw_label

class TwUnspentOutputs(MMGenObject,TwCommon,metaclass=AsyncInit):

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(proto.base_proto_subclass(cls,'tw','unspent'))

	txid_w = 64
	no_rpcdata_errmsg = """
		No spendable outputs found!  Import addresses with balances into your
		watch-only wallet using 'mmgen-addrimport' and then re-run this program.
	"""
	update_widths_on_age_toggle = False
	print_output_types = ('detail',)

	class MMGenTwUnspentOutput(MMGenListItem):
		txid         = ListItemAttr(CoinTxID)
		vout         = ListItemAttr(int,typeconv=False)
		amt          = ImmutableAttr(None)
		amt2         = ListItemAttr(None) # the ETH balance for token account
		comment      = ListItemAttr(TwComment,reassign_ok=True)
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
		self.min_cols     = g.min_screen_width

		from .ctl import TrackingWallet
		self.wallet = await TrackingWallet(proto,mode='w')

	@property
	def total(self):
		return sum(i.amt for i in self.data)

	def gen_data(self,rpc_data,lbl_id):
		for o in rpc_data:
			if not lbl_id in o:
				continue # coinbase outputs have no account field
			l = get_tw_label(self.proto,o[lbl_id])
			if l:
				o.update({
					'twmmid':  l.mmid,
					'comment': l.comment or '',
					'amt':     self.proto.coin_amt(o['amount']),
					'addr':    CoinAddr(self.proto,o['address']),
					'confs':   o['confirmations']
				})
				yield self.MMGenTwUnspentOutput(
					self.proto,
					**{ k:v for k,v in o.items() if k in self.MMGenTwUnspentOutput.valid_attrs } )

	def filter_data(self):

		data = self.data

		for d in data:
			d.skip = ''

		gkeys = {'addr':'addr','twmmid':'addr','txid':'txid'}
		if self.group and self.sort_key in gkeys:
			for a,b in [(data[i],data[i+1]) for i in range(len(data)-1)]:
				for k in gkeys:
					if self.sort_key == k and getattr(a,k) == getattr(b,k):
						b.skip = gkeys[k]

		return data

	def get_column_widths(self,data,wide=False):

		self.cols = self.get_term_columns(g.min_screen_width)

		# allow for 7-digit confirmation nums
		col1_w = max(3,len(str(len(data)))+1) # num + ')'
		mmid_w = max(len(('',i.twmmid)[i.twmmid.type=='mmgen']) for i in data) or 12 # DEADBEEF:S:1
		max_acct_w = max(i.comment.screen_width for i in data) + mmid_w + 1
		max_btcaddr_w = max(len(i.addr) for i in data)
		min_addr_w = self.cols - self.col_adj
		addr_w = min(max_btcaddr_w + (0,1+max_acct_w)[self.show_mmid],min_addr_w)
		acct_w = min(max_acct_w, max(24,addr_w-10))
		btaddr_w = addr_w - acct_w - 1
		comment_w = acct_w - mmid_w - 1
		tx_w = min(self.txid_w,self.cols-addr_w-29-col1_w) # min=6 TODO

		return namedtuple(
			'column_widths',
			['num','mmid','addr','btaddr','comment','tx']
			)(col1_w,  mmid_w,  addr_w,  btaddr_w,  comment_w,  tx_w)

	def gen_squeezed_display(self,data,cw,color):
		fs     = self.squeezed_fs_fs.format(     cw=cw.num, tw=cw.tx )
		hdr_fs = self.squeezed_hdr_fs_fs.format( cw=cw.num, tw=cw.tx )
		yield hdr_fs.format(
			n  = 'Num',
			t  = 'TXid'.ljust(cw.tx - 2) + ' Vout',
			a  = 'Address'.ljust(cw.addr),
			A  = f'Amt({self.proto.dcoin})'.ljust(self.disp_prec+5),
			A2 = f' Amt({self.proto.coin})'.ljust(self.disp_prec+4),
			c  = self.age_hdr ).rstrip()

		for n,i in enumerate(data):
			addr_dots = '|' + '.'*(cw.addr-1)
			mmid_disp = MMGenID.fmtc(
				(
					'.'*cw.mmid if i.skip == 'addr' else
					i.twmmid if i.twmmid.type == 'mmgen' else
					f'Non-{g.proj_name}'
				),
				width = cw.mmid,
				color = color )

			if self.show_mmid:
				addr_out = '{} {}{}'.format((
					type(i.addr).fmtc(addr_dots,width=cw.btaddr,color=color) if i.skip == 'addr' else
					i.addr.fmt(width=cw.btaddr,color=color)
				),
					mmid_disp,
					(' ' + i.comment.fmt(width=cw.comment,color=color)) if cw.comment > 0 else ''
				)
			else:
				addr_out = (
					type(i.addr).fmtc(addr_dots,width=cw.addr,color=color) if i.skip=='addr' else
					i.addr.fmt(width=cw.addr,color=color) )

			yield fs.format(
				n  = str(n+1)+')',
				t  = (
					'' if not i.txid else
					' ' * (cw.tx-4) + '|...' if i.skip  == 'txid' else
					i.txid.truncate(width=cw.tx,color=True) ),
				v  = i.vout,
				a  = addr_out,
				A  = i.amt.fmt(color=color,prec=self.disp_prec),
				A2 = (i.amt2.fmt(color=color,prec=self.disp_prec) if i.amt2 is not None else ''),
				c  = self.age_disp(i,self.age_fmt),
				).rstrip()

	def gen_detail_display(self,data,cw,color):

		addr_w = max(len(i.addr) for i in data)
		mmid_w = max(len(('',i.twmmid)[i.twmmid.type=='mmgen']) for i in data) or 12 # DEADBEEF:S:1

		fs = self.wide_fs_fs.format(
			tw = self.txid_w + 3,
			cf = '{c:<8} ',
			aw = self.proto.coin_amt.max_prec + 5 )

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

		max_comment_len = max([len(i.comment) for i in data if i.comment] or [2])

		for n,i in enumerate(data):
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
				l  = i.comment.hl(color=color) if i.comment else
					TwComment.fmtc(
						s        = '',
						color    = color,
						nullrepl = '-',
						width    = max_comment_len )
				).rstrip()

	def display_total(self):
		msg('\nTotal unspent: {} {} ({} output{})'.format(
			self.total.hl(),
			self.proto.dcoin,
			len(self.data),
			suf(self.data) ))

	class action(TwCommon.action):

		def s_twmmid(self,parent):
			parent.do_sort('twmmid')
			parent.show_mmid = True

		def d_mmid(self,parent):
			parent.show_mmid = not parent.show_mmid

		def d_group(self,parent):
			if parent.can_group:
				parent.group = not parent.group

	class item_action(TwCommon.item_action):

		async def a_balance_refresh(self,uo,idx):
			from ..ui import keypress_confirm
			if not keypress_confirm(
					f'Refreshing tracking wallet {uo.item_desc} #{idx}.  Is this what you want?'):
				return 'redo'
			await uo.wallet.get_balance( uo.data[idx-1].addr, force_rpc=True )
			await uo.get_data()
			uo.oneshot_msg = yellow(f'{uo.proto.dcoin} balance for account #{idx} refreshed\n\n')

		async def a_addr_delete(self,uo,idx):
			from ..ui import keypress_confirm
			if not keypress_confirm(
					f'Removing {uo.item_desc} #{idx} from tracking wallet.  Is this what you want?'):
				return 'redo'
			if await uo.wallet.remove_address( uo.data[idx-1].addr ):
				await uo.get_data()
				uo.oneshot_msg = yellow(f'{capfirst(uo.item_desc)} #{idx} removed\n\n')
			else:
				await asyncio.sleep(3)
				uo.oneshot_msg = red('Address could not be removed\n\n')

		async def a_comment_add(self,uo,idx):

			async def do_comment_add(comment):
				e = uo.data[idx-1]
				if await uo.wallet.add_comment( e.twmmid, comment, coinaddr=e.addr ):
					await uo.get_data()
					uo.oneshot_msg = yellow('Label {a} {b}{c}\n\n'.format(
						a = 'to' if cur_comment and comment else 'added to' if comment else 'removed from',
						b = desc,
						c = ' edited' if cur_comment and comment else '' ))
				else:
					await asyncio.sleep(3)
					uo.oneshot_msg = red('Label could not be {}\n\n'.format(
						'edited' if cur_comment and comment else
						'added' if comment else
						'removed' ))

			desc = f'{uo.item_desc} #{idx}'
			cur_comment = uo.data[idx-1].comment
			msg('Current label: {}'.format(cur_comment.hl() if cur_comment else '(none)'))

			from ..ui import line_input
			res = line_input(
				"Enter label text (or ENTER to return to main menu): ",
				insert_txt = cur_comment )

			if res == cur_comment:
				return None
			elif res == '':
				from ..ui import keypress_confirm
				return (await do_comment_add('')) if keypress_confirm(
					f'Removing label for {desc}.  Is this what you want?') else 'redo'
			else:
				return (await do_comment_add(res)) if get_obj(TwComment,s=res) else 'redo'
