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
from ..color import red,yellow
from ..util import (
	msg,
	die,
	capfirst,
	suf,
	fmt,
	keypress_confirm,
	line_input,
	base_proto_tw_subclass
)
from ..base_obj import AsyncInit
from ..objmethods import MMGenObject
from ..obj import ImmutableAttr,ListItemAttr,MMGenListItem,TwComment,get_obj,HexStr,CoinTxID,MMGenList
from ..addr import CoinAddr,MMGenID
from ..rpc import rpc_init
from .common import TwCommon,TwMMGenID,get_tw_label

class TwUnspentOutputs(MMGenObject,TwCommon,metaclass=AsyncInit):

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(base_proto_tw_subclass(cls,proto,'unspent'))

	txid_w = 64
	print_hdr_fs = '{a} (block #{b}, {c} UTC)\n{d}Sort order: {e}\n{f}\n\nTotal {g}: {h}\n'
	no_rpcdata_errmsg = f"""
		No spendable outputs found!  Import addresses with balances into your
		watch-only wallet using 'mmgen-addrimport' and then re-run this program.
	"""

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

	def gen_data(self,rpc_data,lbl_id):
		for o in rpc_data:
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

	def gen_display_output(self,c):
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

		for n,i in enumerate(self.data):
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

	def gen_print_output(self,color,show_confs):
		addr_w = max(len(i.addr) for i in self.data)
		mmid_w = max(len(('',i.twmmid)[i.twmmid.type=='mmgen']) for i in self.data) or 12 # DEADBEEF:S:1
		fs = self.print_fs_fs.format(
			tw = self.txid_w + 3,
			cf = '{c:<8} ' if show_confs else '',
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

	def display_total(self):
		msg('\nTotal unspent: {} {} ({} output{})'.format(
			self.total.hl(),
			self.proto.dcoin,
			len(self.data),
			suf(self.data) ))

	class item_action:

		async def a_balance_refresh(self,uo,idx):
			if not keypress_confirm(
					f'Refreshing tracking wallet {uo.item_desc} #{idx}.  Is this what you want?'):
				return 'redo'
			await uo.wallet.get_balance( uo.data[idx-1].addr, force_rpc=True )
			await uo.get_data()
			uo.oneshot_msg = yellow(f'{uo.proto.dcoin} balance for account #{idx} refreshed\n\n')

		async def a_addr_delete(self,uo,idx):
			if not keypress_confirm(
					f'Removing {uo.item_desc} #{idx} from tracking wallet.  Is this what you want?'):
				return 'redo'
			if await uo.wallet.remove_address( uo.data[idx-1].addr ):
				await uo.get_data()
				uo.oneshot_msg = yellow(f'{capfirst(uo.item_desc)} #{idx} removed\n\n')
			else:
				import asyncio
				await asyncio.sleep(3)
				uo.oneshot_msg = red('Address could not be removed\n\n')

		async def a_lbl_add(self,uo,idx):

			async def do_lbl_add(lbl):
				e = uo.data[idx-1]
				if await uo.wallet.add_label( e.twmmid, lbl, addr=e.addr ):
					await uo.get_data()
					uo.oneshot_msg = yellow('Label {} {} #{}\n\n'.format(
						('added to' if lbl else 'removed from'),
						uo.item_desc,
						idx ))
				else:
					import asyncio
					await asyncio.sleep(3)
					uo.oneshot_msg = red('Label could not be added\n\n')

			cur_lbl = uo.data[idx-1].label
			msg('Current label: {}'.format(cur_lbl.hl() if cur_lbl else '(none)'))

			res = line_input(
				"Enter label text (or ENTER to return to main menu): ",
				insert_txt = cur_lbl )
			if res == cur_lbl:
				return None
			elif res == '':
				return (await do_lbl_add(res)) if keypress_confirm(
					f'Removing label for {uo.item_desc} #{idx}.  Is this what you want?') else 'redo'
			else:
				return (await do_lbl_add(res)) if get_obj(TwComment,s=res) else 'redo'
