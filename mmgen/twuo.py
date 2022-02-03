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

from .globalvars import g
from .color import red,yellow,green
from .util import (
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
	altcoin_subclass
)
from .base_obj import AsyncInit
from .objmethods import MMGenObject
from .obj import ImmutableAttr,ListItemAttr,MMGenListItem,TwComment,get_obj,HexStr,CoinTxID
from .addr import CoinAddr,MMGenID,AddrIdx
from .rpc import rpc_init
from .tw import TwCommon,TwMMGenID,get_tw_label

class TwUnspentOutputs(MMGenObject,TwCommon,metaclass=AsyncInit):

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(altcoin_subclass(cls,proto,'twuo'))

	txid_w = 64
	disp_type = 'btc'
	can_group = True
	hdr_fmt = 'UNSPENT OUTPUTS (sort order: {}) Total {}: {}'
	desc = 'unspent outputs'
	item_desc = 'unspent output'
	dump_fn_pfx = 'listunspent'
	prompt_fs = 'Total to spend, excluding fees: {} {}\n\n'
	prompt = """
Sort options: [t]xid, [a]mount, a[d]dress, [A]ge, [r]everse, [M]mgen addr
Display options: toggle [D]ays/date, show [g]roup, show [m]mgen addr, r[e]draw
Actions: [q]uit view, [p]rint to file, pager [v]iew, [w]ide view, add [l]abel:
"""
	key_mappings = {
		't':'s_txid','a':'s_amt','d':'s_addr','A':'s_age','r':'d_reverse','M':'s_twmmid',
		'D':'d_days','g':'d_group','m':'d_mmid','e':'d_redraw',
		'q':'a_quit','p':'a_print','v':'a_view','w':'a_view_wide','l':'a_lbl_add' }
	col_adj = 38
	age_fmts_date_dependent = ('days','date','date_time')
	age_fmts_interactive = ('confs','block','days','date')
	_age_fmt = 'confs'

	class MMGenTwOutputList(list,MMGenObject): pass

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

		# required by gen_unspent(); setting valid_attrs explicitly is also more efficient
		valid_attrs = {'txid','vout','amt','amt2','label','twmmid','addr','confs','date','scriptPubKey','skip'}
		invalid_attrs = {'proto'}

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
		self.unspent      = self.MMGenTwOutputList()
		self.fmt_display  = ''
		self.fmt_print    = ''
		self.cols         = None
		self.reverse      = False
		self.group        = False
		self.show_mmid    = True
		self.minconf      = minconf
		self.addrs        = addrs
		self.sort_key     = 'age'
		self.disp_prec    = self.get_display_precision()
		self.rpc          = await rpc_init(proto)

		from .twctl import TrackingWallet
		self.wallet = await TrackingWallet(proto,mode='w')
		if self.disp_type == 'token':
			self.proto.tokensym = self.wallet.symbol

	@property
	def age_fmt(self):
		return self._age_fmt

	@age_fmt.setter
	def age_fmt(self,val):
		if val not in self.age_fmts:
			from .exception import BadAgeFormat
			raise BadAgeFormat(f'{val!r}: invalid age format (must be one of {self.age_fmts!r})')
		self._age_fmt = val

	def get_display_precision(self):
		return self.proto.coin_amt.max_prec

	@property
	def total(self):
		return sum(i.amt for i in self.unspent)

	async def get_unspent_rpc(self):
		# bitcoin-cli help listunspent:
		# Arguments:
		# 1. minconf        (numeric, optional, default=1) The minimum confirmations to filter
		# 2. maxconf        (numeric, optional, default=9999999) The maximum confirmations to filter
		# 3. addresses      (json array, optional, default=empty array) A json array of bitcoin addresses
		# 4. include_unsafe (boolean, optional, default=true) Include outputs that are not safe to spend
		# 5. query_options  (json object, optional) JSON with query options

		# for now, self.addrs is just an empty list for Bitcoin and friends
		add_args = (9999999,self.addrs) if self.addrs else ()
		return await self.rpc.call('listunspent',self.minconf,*add_args)

	async def get_unspent_data(self,sort_key=None,reverse_sort=False):

		us_raw = await self.get_unspent_rpc()

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

		self.unspent = self.MMGenTwOutputList(gen_unspent())

		if not self.unspent:
			die(1, f'No tracked {self.item_desc}s in tracking wallet!')

		self.do_sort(key=sort_key,reverse=reverse_sort)

	def do_sort(self,key=None,reverse=False):
		sort_funcs = {
			'addr':  lambda i: i.addr,
			'age':   lambda i: 0 - i.confs,
			'amt':   lambda i: i.amt,
			'txid':  lambda i: f'{i.txid} {i.vout:04}',
			'twmmid':  lambda i: i.twmmid.sort_key
		}
		key = key or self.sort_key
		if key not in sort_funcs:
			die(1,f'{key!r}: invalid sort key.  Valid options: {" ".join(sort_funcs.keys())}')
		self.sort_key = key
		assert type(reverse) == bool
		self.unspent.sort(key=sort_funcs[key],reverse=reverse or self.reverse)

	def sort_info(self,include_group=True):
		ret = ([],['Reverse'])[self.reverse]
		ret.append(capfirst(self.sort_key).replace('Twmmid','MMGenID'))
		if include_group and self.group and (self.sort_key in ('addr','txid','twmmid')):
			ret.append('Grouped')
		return ret

	def set_term_columns(self):
		from .term import get_terminal_size
		while True:
			self.cols = g.terminal_width or get_terminal_size().width
			if self.cols >= g.min_screen_width:
				break
			line_input(
				'Screen too narrow to display the tracking wallet\n'
				+ f'Please resize your screen to at least {g.min_screen_width} characters and hit ENTER ' )

	def get_display_constants(self):
		unsp = self.unspent
		for i in unsp:
			i.skip = ''

		# allow for 7-digit confirmation nums
		col1_w = max(3,len(str(len(unsp)))+1) # num + ')'
		mmid_w = max(len(('',i.twmmid)[i.twmmid.type=='mmgen']) for i in unsp) or 12 # DEADBEEF:S:1
		max_acct_w = max(i.label.screen_width for i in unsp) + mmid_w + 1
		max_btcaddr_w = max(len(i.addr) for i in unsp)
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
		unsp = self.unspent
		if self.age_fmt in self.age_fmts_date_dependent:
			await self.set_dates(self.rpc,unsp)
		self.set_term_columns()

		c = getattr(self,'display_constants',None)
		if not c:
			c = self.display_constants = self.get_display_constants()

		if self.group and (self.sort_key in ('addr','txid','twmmid')):
			for a,b in [(unsp[i],unsp[i+1]) for i in range(len(unsp)-1)]:
				for k in ('addr','txid','twmmid'):
					if self.sort_key == k and getattr(a,k) == getattr(b,k):
						b.skip = (k,'addr')[k=='twmmid']

		def gen_output():
			yield self.hdr_fmt.format(' '.join(self.sort_info()),self.proto.dcoin,self.total.hl())
			if self.proto.chain_name != 'mainnet':
				yield 'Chain: '+green(self.proto.chain_name.upper())
			fs = {  'btc':   ' {n:%s} {t:%s} {v:2} {a} {A} {c:<}' % (c.col1_w,c.tx_w),
					'eth':   ' {n:%s} {a} {A}' % c.col1_w,
					'token': ' {n:%s} {a} {A} {A2}' % c.col1_w }[self.disp_type]
			fs_hdr = ' {n:%s} {t:%s} {a} {A} {c:<}' % (c.col1_w,c.tx_w) if self.disp_type == 'btc' else fs
			date_hdr = {
				'confs':     'Confs',
				'block':     'Block',
				'days':      'Age(d)',
				'date':      'Date',
				'date_time': 'Date',
			}
			yield fs_hdr.format(
				n  = 'Num',
				t  = 'TXid'.ljust(c.tx_w - 2) + ' Vout',
				a  = 'Address'.ljust(c.addr_w),
				A  = f'Amt({self.proto.dcoin})'.ljust(self.disp_prec+5),
				A2 = f' Amt({self.proto.coin})'.ljust(self.disp_prec+4),
				c  =  date_hdr[self.age_fmt],
				).rstrip()

			for n,i in enumerate(unsp):
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
		await self.set_dates(self.rpc,self.unspent)
		addr_w = max(len(i.addr) for i in self.unspent)
		mmid_w = max(len(('',i.twmmid)[i.twmmid.type=='mmgen']) for i in self.unspent) or 12 # DEADBEEF:S:1
		amt_w = self.proto.coin_amt.max_prec + 5
		cfs = '{c:<8} ' if show_confs else ''
		fs = {
			'btc': (' {n:4} {t:%s} {a} {m} {A:%s} ' + cfs + '{b:<8} {D:<19} {l}') % (self.txid_w+3,amt_w),
			'eth':   ' {n:4} {a} {m} {A:%s} {l}' % amt_w,
			'token': ' {n:4} {a} {m} {A:%s} {A2:%s} {l}' % (amt_w,amt_w)
			}[self.disp_type]

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

			max_lbl_len = max([len(i.label) for i in self.unspent if i.label] or [2])
			for n,i in enumerate(self.unspent):
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
			len(self.unspent),
			suf(self.unspent) ))

	def get_idx_from_user(self,action):
		msg('')
		while True:
			ret = line_input(f'Enter {self.item_desc} number (or RETURN to return to main menu): ')
			if ret == '':
				return (None,None) if action == 'a_lbl_add' else None
			n = get_obj(AddrIdx,n=ret,silent=True)
			if not n or n < 1 or n > len(self.unspent):
				msg(f'Choice must be a single number between 1 and {len(self.unspent)}')
			else:
				if action == 'a_lbl_add':
					cur_lbl = self.unspent[n-1].label
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

	async def view_and_sort(self,tx):
		from .term import get_char
		prompt = self.prompt.strip() + '\b'
		no_output,oneshot_msg = False,None
		from .opts import opt
		CUR_HOME,ERASE_ALL = '\033[H','\033[0J'
		CUR_RIGHT = lambda n: f'\033[{n}C'

		while True:
			msg_r('' if no_output else '\n\n' if opt.no_blank else CUR_HOME+ERASE_ALL)
			reply = get_char(
				'' if no_output else await self.format_for_display()+'\n'+(oneshot_msg or '')+prompt,
				immed_chars=''.join(self.key_mappings.keys())
			)
			no_output = False
			oneshot_msg = '' if oneshot_msg else None # tristate, saves previous state
			if reply not in self.key_mappings:
				msg_r('\ninvalid keypress ')
				time.sleep(0.5)
				continue

			action = self.key_mappings[reply]
			if action[:2] == 's_':
				self.do_sort(action[2:])
				if action == 's_twmmid': self.show_mmid = True
			elif action == 'd_days':
				af = self.age_fmts_interactive
				self.age_fmt = af[(af.index(self.age_fmt) + 1) % len(af)]
			elif action == 'd_mmid':
				self.show_mmid = not self.show_mmid
			elif action == 'd_group':
				if self.can_group:
					self.group = not self.group
			elif action == 'd_redraw':
				pass
			elif action == 'd_reverse':
				self.unspent.reverse()
				self.reverse = not self.reverse
			elif action == 'a_quit':
				msg('')
				return self.unspent
			elif action == 'a_balance_refresh':
				idx = self.get_idx_from_user(action)
				if idx:
					e = self.unspent[idx-1]
					bal = await self.wallet.get_balance(e.addr,force_rpc=True)
					await self.get_unspent_data()
					oneshot_msg = yellow(f'{self.proto.dcoin} balance for account #{idx} refreshed\n\n')
				self.display_constants = self.get_display_constants()
			elif action == 'a_lbl_add':
				idx,lbl = self.get_idx_from_user(action)
				if idx:
					e = self.unspent[idx-1]
					if await self.wallet.add_label(e.twmmid,lbl,addr=e.addr):
						await self.get_unspent_data()
						oneshot_msg = yellow('Label {} {} #{}\n\n'.format(
							('added to' if lbl else 'removed from'),
							self.item_desc,
							idx ))
					else:
						oneshot_msg = red('Label could not be added\n\n')
				self.display_constants = self.get_display_constants()
			elif action == 'a_addr_delete':
				idx = self.get_idx_from_user(action)
				if idx:
					e = self.unspent[idx-1]
					if await self.wallet.remove_address(e.addr):
						await self.get_unspent_data()
						oneshot_msg = yellow(f'{capfirst(self.item_desc)} #{idx} removed\n\n')
					else:
						oneshot_msg = red('Address could not be removed\n\n')
				self.display_constants = self.get_display_constants()
			elif action == 'a_print':
				of = '{}-{}[{}].out'.format(
					self.dump_fn_pfx,
					self.proto.dcoin,
					','.join(self.sort_info(include_group=False)).lower() )
				msg('')
				from .fileutil import write_data_to_file
				try:
					write_data_to_file(
						of,
						await self.format_for_printing(),
						desc = f'{self.desc} listing' )
				except UserNonConfirmation as e:
					oneshot_msg = red(f'File {of!r} not overwritten by user request\n\n')
				else:
					oneshot_msg = yellow(f'Data written to {of!r}\n\n')
			elif action in ('a_view','a_view_wide'):
				do_pager(
					self.fmt_display if action == 'a_view' else
					await self.format_for_printing(color=True) )
				if g.platform == 'linux' and oneshot_msg == None:
					msg_r(CUR_RIGHT(len(prompt.split('\n')[-1])-2))
					no_output = True
