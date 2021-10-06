#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2021 The MMGen Project <mmgen@tuta.io>
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
tw: Tracking wallet methods for the MMGen suite
"""

import json
from collections import namedtuple
from .exception import *
from .common import *
from .obj import *
from .tx import is_mmgen_id,is_coin_addr
from .rpc import rpc_init

CUR_HOME,ERASE_ALL = '\033[H','\033[0J'

def CUR_RIGHT(n):
	return f'\033[{n}C'

def get_tw_label(proto,s):
	"""
	raise an exception on a malformed comment, return None on an empty or invalid label
	"""
	try:
		return TwLabel(proto,s)
	except BadTwComment:
		raise
	except:
		return None

class TwUnspentOutputs(MMGenObject,metaclass=AsyncInit):

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(altcoin_subclass(cls,proto,'tw'))

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
	age_fmts = ('confs','block','days','date','date_time')
	age_fmts_date_dependent = ('days','date','date_time')
	age_fmts_interactive = ('confs','block','days','date')
	_age_fmt = 'confs'

	class MMGenTwOutputList(list,MMGenObject): pass

	class MMGenTwUnspentOutput(MMGenListItem):
		txid         = ListItemAttr('CoinTxID')
		vout         = ListItemAttr(int,typeconv=False)
		amt          = ImmutableAttr(None)
		amt2         = ListItemAttr(None)
		label        = ListItemAttr('TwComment',reassign_ok=True)
		twmmid       = ImmutableAttr('TwMMGenID',include_proto=True)
		addr         = ImmutableAttr('CoinAddr',include_proto=True)
		confs        = ImmutableAttr(int,typeconv=False)
		date         = ListItemAttr(int,typeconv=False,reassign_ok=True)
		scriptPubKey = ImmutableAttr('HexStr')
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

		self.wallet = await TrackingWallet(proto,mode='w')
		if self.disp_type == 'token':
			self.proto.tokensym = self.wallet.symbol

	@property
	def age_fmt(self):
		return self._age_fmt

	@age_fmt.setter
	def age_fmt(self,val):
		if val not in self.age_fmts:
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
			my_raw_input(
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

	@staticmethod
	async def set_dates(rpc,us):
		if rpc.proto.base_proto != 'Bitcoin':
			return
		if us and us[0].date is None:
			# 'blocktime' differs from 'time', is same as getblockheader['time']
			dates = [o['blocktime'] for o in await rpc.gathered_call('gettransaction',[(o.txid,) for o in us])]
			for idx,o in enumerate(us):
				o.date = dates[idx]

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
			ret = my_raw_input(f'Enter {self.item_desc} number (or RETURN to return to main menu): ')
			if ret == '': return (None,None) if action == 'a_lbl_add' else None
			n = get_obj(AddrIdx,n=ret,silent=True)
			if not n or n < 1 or n > len(self.unspent):
				msg(f'Choice must be a single number between 1 and {len(self.unspent)}')
			else:
				if action == 'a_lbl_add':
					cur_lbl = self.unspent[n-1].label
					msg('Current label: {}'.format(cur_lbl.hl() if cur_lbl else '(none)'))
					while True:
						s = my_raw_input("Enter label text (or 'q' to return to main menu): ")
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

	def age_disp(self,o,age_fmt):
		if age_fmt == 'confs':
			return o.confs
		elif age_fmt == 'block':
			return self.rpc.blockcount - (o.confs - 1)
		else:
			return self.date_formatter[age_fmt](self.rpc,o.date)

	date_formatter = {
		'days':      lambda rpc,secs: (rpc.cur_date - secs) // 86400,
		'date':      lambda rpc,secs: '{}-{:02}-{:02}'.format(*time.gmtime(secs)[:3])[2:],
		'date_time': lambda rpc,secs: '{}-{:02}-{:02} {:02}:{:02}'.format(*time.gmtime(secs)[:5]),
	}


class TwAddrList(MMGenDict,metaclass=AsyncInit):
	has_age = True
	age_fmts = TwUnspentOutputs.age_fmts
	age_disp = TwUnspentOutputs.age_disp
	date_formatter = TwUnspentOutputs.date_formatter

	def __new__(cls,proto,*args,**kwargs):
		return MMGenDict.__new__(altcoin_subclass(cls,proto,'tw'),*args,**kwargs)

	async def __init__(self,proto,usr_addr_list,minconf,showempty,showbtcaddrs,all_labels,wallet=None):

		def check_dup_mmid(acct_labels):
			mmid_prev,err = None,False
			for mmid in sorted(a.mmid for a in acct_labels if a):
				if mmid == mmid_prev:
					err = True
					msg(f'Duplicate MMGen ID ({mmid}) discovered in tracking wallet!\n')
				mmid_prev = mmid
			if err: rdie(3,'Tracking wallet is corrupted!')

		def check_addr_array_lens(acct_pairs):
			err = False
			for label,addrs in acct_pairs:
				if not label: continue
				if len(addrs) != 1:
					err = True
					if len(addrs) == 0:
						msg(f'Label {label!r}: has no associated address!')
					else:
						msg(f'{addrs!r}: more than one {proto.coin} address in account!')
			if err: rdie(3,'Tracking wallet is corrupted!')

		self.rpc   = await rpc_init(proto)
		self.total = proto.coin_amt('0')
		self.proto = proto

		lbl_id = ('account','label')['label_api' in self.rpc.caps]
		for d in await self.rpc.call('listunspent',0):
			if not lbl_id in d: continue  # skip coinbase outputs with missing account
			if d['confirmations'] < minconf: continue
			label = get_tw_label(proto,d[lbl_id])
			if label:
				lm = label.mmid
				if usr_addr_list and (lm not in usr_addr_list):
					continue
				if lm in self:
					if self[lm]['addr'] != d['address']:
						die(2,'duplicate {} address ({}) for this MMGen address! ({})'.format(
							proto.coin,
							d['address'],
							self[lm]['addr'] ))
				else:
					lm.confs = d['confirmations']
					lm.txid = d['txid']
					lm.date = None
					self[lm] = {
						'amt': proto.coin_amt('0'),
						'lbl': label,
						'addr': CoinAddr(proto,d['address']) }
				amt = proto.coin_amt(d['amount'])
				self[lm]['amt'] += amt
				self.total += amt

		# We use listaccounts only for empty addresses, as it shows false positive balances
		if showempty or all_labels:
			# for compatibility with old mmids, must use raw RPC rather than native data for matching
			# args: minconf,watchonly, MUST use keys() so we get list, not dict
			if 'label_api' in self.rpc.caps:
				acct_list = await self.rpc.call('listlabels')
				aa = await self.rpc.batch_call('getaddressesbylabel',[(k,) for k in acct_list])
				acct_addrs = [list(a.keys()) for a in aa]
			else:
				acct_list = list((await self.rpc.call('listaccounts',0,True)).keys()) # raw list, no 'L'
				acct_addrs = await self.rpc.batch_call('getaddressesbyaccount',[(a,) for a in acct_list]) # use raw list here
			acct_labels = MMGenList([get_tw_label(proto,a) for a in acct_list])
			check_dup_mmid(acct_labels)
			assert len(acct_list) == len(acct_addrs),(
				'listaccounts() and getaddressesbyaccount() not equal in length')
			addr_pairs = list(zip(acct_labels,acct_addrs))
			check_addr_array_lens(addr_pairs)
			for label,addr_arr in addr_pairs:
				if not label: continue
				if all_labels and not showempty and not label.comment: continue
				if usr_addr_list and (label.mmid not in usr_addr_list): continue
				if label.mmid not in self:
					self[label.mmid] = { 'amt':proto.coin_amt('0'), 'lbl':label, 'addr':'' }
					if showbtcaddrs:
						self[label.mmid]['addr'] = CoinAddr(proto,addr_arr[0])

	def raw_list(self):
		return [((k if k.type == 'mmgen' else 'Non-MMGen'),self[k]['addr'],self[k]['amt']) for k in self]

	def coinaddr_list(self):
		return [self[k]['addr'] for k in self]

	async def format(self,showbtcaddrs,sort,show_age,age_fmt):
		if not self.has_age:
			show_age = False
		if age_fmt not in self.age_fmts:
			raise BadAgeFormat(f'{age_fmt!r}: invalid age format (must be one of {self.age_fmts!r})')
		fs = '{mid}' + ('',' {addr}')[showbtcaddrs] + ' {cmt} {amt}' + ('',' {age}')[show_age]
		mmaddrs = [k for k in self.keys() if k.type == 'mmgen']
		max_mmid_len = max(len(k) for k in mmaddrs) + 2 if mmaddrs else 10
		max_cmt_width = max(max(v['lbl'].comment.screen_width for v in self.values()),7)
		addr_width = max(len(self[mmid]['addr']) for mmid in self)

		max_fp_len = max([len(a.split('.')[1]) for a in [str(v['amt']) for v in self.values()] if '.' in a] or [1])

		def sort_algo(j):
			if sort and 'age' in sort:
				return '{}_{:>012}_{}'.format(
					j.obj.rsplit(':',1)[0],
					# Hack, but OK for the foreseeable future:
					(1000000000-(j.confs or 0) if hasattr(j,'confs') else 0),
					j.sort_key)
			else:
				return j.sort_key

		mmids = sorted(self,key=sort_algo,reverse=bool(sort and 'reverse' in sort))
		if show_age:
			await TwUnspentOutputs.set_dates(
				self.rpc,
				[o for o in mmids if hasattr(o,'confs')] )

		def gen_output():

			if self.proto.chain_name != 'mainnet':
				yield 'Chain: '+green(self.proto.chain_name.upper())

			yield fs.format(
					mid=MMGenID.fmtc('MMGenID',width=max_mmid_len),
					addr=(CoinAddr.fmtc('ADDRESS',width=addr_width) if showbtcaddrs else None),
					cmt=TwComment.fmtc('COMMENT',width=max_cmt_width+1),
					amt='BALANCE'.ljust(max_fp_len+4),
					age=age_fmt.upper(),
				).rstrip()

			al_id_save = None
			for mmid in mmids:
				if mmid.type == 'mmgen':
					if al_id_save and al_id_save != mmid.obj.al_id:
						yield ''
					al_id_save = mmid.obj.al_id
					mmid_disp = mmid
				else:
					if al_id_save:
						yield ''
						al_id_save = None
					mmid_disp = 'Non-MMGen'
				e = self[mmid]
				yield fs.format(
					mid=MMGenID.fmtc(mmid_disp,width=max_mmid_len,color=True),
					addr=(e['addr'].fmt(color=True,width=addr_width) if showbtcaddrs else None),
					cmt=e['lbl'].comment.fmt(width=max_cmt_width,color=True,nullrepl='-'),
					amt=e['amt'].fmt('4.{}'.format(max(max_fp_len,3)),color=True),
					age=self.age_disp(mmid,age_fmt) if show_age and hasattr(mmid,'confs') else '-'
					).rstrip()

			yield '\nTOTAL: {} {}'.format(
				self.total.hl(color=True),
				self.proto.dcoin )

		return '\n'.join(gen_output())

class TrackingWallet(MMGenObject,metaclass=AsyncInit):

	caps = ('rescan','batch')
	data_key = 'addresses'
	use_tw_file = False
	aggressive_sync = False
	importing = False

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(altcoin_subclass(cls,proto,'tw'))

	async def __init__(self,proto,mode='r',token_addr=None):

		assert mode in ('r','w','i'), f"{mode!r}: wallet mode must be 'r','w' or 'i'"
		if mode == 'i':
			self.importing = True
			mode = 'w'

		if g.debug:
			print_stack_trace(f'TW INIT {mode!r} {self!r}')

		self.rpc = await rpc_init(proto) # TODO: create on demand - only certain ops require RPC
		self.proto = proto
		self.mode = mode
		self.desc = self.base_desc = f'{self.proto.name} tracking wallet'

		if self.use_tw_file:
			self.init_from_wallet_file()
		else:
			self.init_empty()

		if self.data['coin'] != self.proto.coin: # TODO remove?
			raise WalletFileError(
				'Tracking wallet coin ({}) does not match current coin ({})!'.format(
					self.data['coin'],
					self.proto.coin ))

		self.conv_types(self.data[self.data_key])
		self.cur_balances = {} # cache balances to prevent repeated lookups per program invocation

	def init_empty(self):
		self.data = { 'coin': self.proto.coin, 'addresses': {} }

	def init_from_wallet_file(self):
		tw_dir = (
			os.path.join(g.data_dir) if self.proto.coin == 'BTC' else
			os.path.join(
				g.data_dir_root,
				'altcoins',
				self.proto.coin.lower(),
				('' if self.proto.network == 'mainnet' else 'testnet')
			))
		self.tw_fn = os.path.join(tw_dir,'tracking-wallet.json')

		check_or_create_dir(tw_dir)

		try:
			self.orig_data = get_data_from_file(self.tw_fn,quiet=True)
			self.data = json.loads(self.orig_data)
		except:
			try: os.stat(self.tw_fn)
			except:
				self.orig_data = ''
				self.init_empty()
				self.force_write()
			else:
				raise WalletFileError(f'File {self.tw_fn!r} exists but does not contain valid json data')
		else:
			self.upgrade_wallet_maybe()

		# ensure that wallet file is written when user exits via KeyboardInterrupt:
		if self.mode == 'w':
			import atexit
			def del_tw(tw):
				dmsg(f'Running exit handler del_tw() for {tw!r}')
				del tw
			atexit.register(del_tw,self)

	def __del__(self):
		"""
		TrackingWallet instances opened in write or import mode must be explicitly destroyed
		with 'del tw', 'del twuo.wallet' and the like to ensure the instance is deleted and
		wallet is written before global vars are destroyed by the interpreter at shutdown.

		Not that this code can only be debugged by examining the program output, as exceptions
		are ignored within __del__():

			/usr/share/doc/python3.6-doc/html/reference/datamodel.html#object.__del__

		Since no exceptions are raised, errors will not be caught by the test suite.
		"""
		if g.debug:
			print_stack_trace(f'TW DEL {self!r}')

		if getattr(self,'mode',None) == 'w': # mode attr might not exist in this state
			self.write()
		elif g.debug:
			msg('read-only wallet, doing nothing')

	def upgrade_wallet_maybe(self):
		pass

	def conv_types(self,ad):
		for k,v in ad.items():
			if k not in ('params','coin'):
				v['mmid'] = TwMMGenID(self.proto,v['mmid'])
				v['comment'] = TwComment(v['comment'])

	@property
	def data_root(self):
		return self.data[self.data_key]

	@property
	def data_root_desc(self):
		return self.data_key

	def cache_balance(self,addr,bal,session_cache,data_root,force=False):
		if force or addr not in session_cache:
			session_cache[addr] = str(bal)
			if addr in data_root:
				data_root[addr]['balance'] = str(bal)
				if self.aggressive_sync:
					self.write()

	def get_cached_balance(self,addr,session_cache,data_root):
		if addr in session_cache:
			return self.proto.coin_amt(session_cache[addr])
		if not g.cached_balances:
			return None
		if addr in data_root and 'balance' in data_root[addr]:
			return self.proto.coin_amt(data_root[addr]['balance'])

	async def get_balance(self,addr,force_rpc=False):
		ret = None if force_rpc else self.get_cached_balance(addr,self.cur_balances,self.data_root)
		if ret == None:
			ret = await self.rpc_get_balance(addr)
			self.cache_balance(addr,ret,self.cur_balances,self.data_root)
		return ret

	async def rpc_get_balance(self,addr):
		raise NotImplementedError('not implemented')

	@property
	def sorted_list(self):
		return sorted(
			[ { 'addr':x[0],
				'mmid':x[1]['mmid'],
				'comment':x[1]['comment'] }
					for x in self.data_root.items() if x[0] not in ('params','coin') ],
			key=lambda x: x['mmid'].sort_key+x['addr'] )

	@property
	def mmid_ordered_dict(self):
		return dict((x['mmid'],{'addr':x['addr'],'comment':x['comment']}) for x in self.sorted_list)

	@write_mode
	async def import_address(self,addr,label,rescan):
		return await self.rpc.call('importaddress',addr,label,rescan,timeout=(False,3600)[rescan])

	@write_mode
	def batch_import_address(self,arg_list):
		return self.rpc.batch_call('importaddress',arg_list)

	def force_write(self):
		mode_save = self.mode
		self.mode = 'w'
		self.write()
		self.mode = mode_save

	@write_mode
	def write_changed(self,data):
		write_data_to_file(
			self.tw_fn,
			data,
			desc              = f'{self.base_desc} data',
			ask_overwrite     = False,
			ignore_opt_outdir = True,
			quiet             = True,
			check_data        = True,
			cmp_data          = self.orig_data )

		self.orig_data = data

	def write(self): # use 'check_data' to check wallet hasn't been altered by another program
		if not self.use_tw_file:
			dmsg("'use_tw_file' is False, doing nothing")
			return
		dmsg(f'write(): checking if {self.desc} data has changed')
		wdata = json.dumps(self.data)

		if self.orig_data != wdata:
			if g.debug:
				print_stack_trace(f'TW DATA CHANGED {self!r}')
				print_diff(self.orig_data,wdata,from_json=True)
			self.write_changed(wdata)
		elif g.debug:
			msg('Data is unchanged\n')

	async def is_in_wallet(self,addr):
		return addr in (await TwAddrList(self.proto,[],0,True,True,True,wallet=self)).coinaddr_list()

	@write_mode
	async def set_label(self,coinaddr,lbl):
		# bitcoin-{abc,bchn} 'setlabel' RPC is broken, so use old 'importaddress' method to set label
		# broken behavior: new label is set OK, but old label gets attached to another address
		if 'label_api' in self.rpc.caps and self.proto.coin != 'BCH':
			args = ('setlabel',coinaddr,lbl)
		else:
			# NOTE: this works because importaddress() removes the old account before
			# associating the new account with the address.
			# RPC args: addr,label,rescan[=true],p2sh[=none]
			args = ('importaddress',coinaddr,lbl,False)

		try:
			return await self.rpc.call(*args)
		except Exception as e:
			rmsg(e.args[0])
			return False

	# returns on failure
	@write_mode
	async def add_label(self,arg1,label='',addr=None,silent=False,on_fail='return'):
		assert on_fail in ('return','raise'), 'add_label_chk1'
		mmaddr,coinaddr = None,None
		if is_coin_addr(self.proto,addr or arg1):
			coinaddr = get_obj(CoinAddr,proto=self.proto,addr=addr or arg1)
		if is_mmgen_id(self.proto,arg1):
			mmaddr = TwMMGenID(self.proto,arg1)

		if mmaddr and not coinaddr:
			from .addr import TwAddrData
			coinaddr = (await TwAddrData(self.proto)).mmaddr2coinaddr(mmaddr)

		try:
			if not is_mmgen_id(self.proto,arg1):
				assert coinaddr, f'Invalid coin address for this chain: {arg1}'
			assert coinaddr, f'{g.proj_name} address {mmaddr!r} not found in tracking wallet'
			assert await self.is_in_wallet(coinaddr), f'Address {coinaddr!r} not found in tracking wallet'
		except Exception as e:
			msg(str(e))
			return False

		# Allow for the possibility that BTC addr of MMGen addr was entered.
		# Do reverse lookup, so that MMGen addr will not be marked as non-MMGen.
		if not mmaddr:
			from .addr import TwAddrData
			mmaddr = (await TwAddrData(proto=self.proto)).coinaddr2mmaddr(coinaddr)

		if not mmaddr:
			mmaddr = f'{self.proto.base_coin.lower()}:{coinaddr}'

		mmaddr = TwMMGenID(self.proto,mmaddr)

		cmt = TwComment(label) if on_fail=='raise' else get_obj(TwComment,s=label)
		if cmt in (False,None):
			return False

		lbl_txt = mmaddr + (' ' + cmt if cmt else '')
		lbl = (
			TwLabel(self.proto,lbl_txt) if on_fail == 'raise' else
			get_obj(TwLabel,proto=self.proto,text=lbl_txt) )

		if await self.set_label(coinaddr,lbl) == False:
			if not silent:
				msg( 'Label could not be {}'.format('added' if label else 'removed') )
			return False
		else:
			desc = '{} address {} in tracking wallet'.format(
				mmaddr.type.replace('mmg','MMG'),
				mmaddr.replace(self.proto.base_coin.lower()+':','') )
			if label:
				msg(f'Added label {label!r} to {desc}')
			else:
				msg(f'Removed label from {desc}')
			return True

	@write_mode
	async def remove_label(self,mmaddr):
		await self.add_label(mmaddr,'')

	@write_mode
	async def remove_address(self,addr):
		raise NotImplementedError(f'address removal not implemented for coin {self.proto.coin}')

class TwGetBalance(MMGenObject,metaclass=AsyncInit):

	fs = '{w:13} {u:<16} {p:<16} {c}'

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(altcoin_subclass(cls,proto,'tw'))

	async def __init__(self,proto,minconf,quiet):

		self.minconf = minconf
		self.quiet = quiet
		self.data = {k:[proto.coin_amt('0')] * 4 for k in ('TOTAL','Non-MMGen','Non-wallet')}
		self.rpc = await rpc_init(proto)
		self.proto = proto
		await self.create_data()

	async def create_data(self):
		# 0: unconfirmed, 1: below minconf, 2: confirmed, 3: spendable (privkey in wallet)
		lbl_id = ('account','label')['label_api' in self.rpc.caps]
		for d in await self.rpc.call('listunspent',0):
			lbl = get_tw_label(self.proto,d[lbl_id])
			if lbl:
				if lbl.mmid.type == 'mmgen':
					key = lbl.mmid.obj.sid
					if key not in self.data:
						self.data[key] = [self.proto.coin_amt('0')] * 4
				else:
					key = 'Non-MMGen'
			else:
				lbl,key = None,'Non-wallet'

			amt = self.proto.coin_amt(d['amount'])

			if not d['confirmations']:
				self.data['TOTAL'][0] += amt
				self.data[key][0] += amt

			conf_level = (1,2)[d['confirmations'] >= self.minconf]

			self.data['TOTAL'][conf_level] += amt
			self.data[key][conf_level] += amt

			if d['spendable']:
				self.data[key][3] += amt

	def format(self):
		def gen_output():
			if self.proto.chain_name != 'mainnet':
				yield 'Chain: ' + green(self.proto.chain_name.upper())

			if self.quiet:
				yield str(self.data['TOTAL'][2] if self.data else 0)
			else:
				yield self.fs.format(
					w = 'Wallet',
					u = ' Unconfirmed',
					p = f' <{self.minconf} confirms',
					c = f' >={self.minconf} confirms' )

				for key in sorted(self.data):
					if not any(self.data[key]):
						continue
					yield self.fs.format(**dict(zip(
						('w','u','p','c'),
						[key+':'] + [a.fmt(color=True,suf=' '+self.proto.dcoin) for a in self.data[key]]
						)))

			for key,vals in list(self.data.items()):
				if key == 'TOTAL':
					continue
				if vals[3]:
					yield red(f'Warning: this wallet contains PRIVATE KEYS for {key} outputs!')

		return '\n'.join(gen_output()).rstrip()
