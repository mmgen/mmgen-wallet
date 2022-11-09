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
tw: Tracking wallet dependency classes and helper functions
"""

import sys,time,asyncio
from collections import namedtuple

from ..globalvars import g
from ..objmethods import Hilite,InitErrors,MMGenObject
from ..obj import TwComment,get_obj,MMGenIdx,MMGenList
from ..color import nocolor,yellow,green,red,blue
from ..util import msg,msg_r,fmt,die,capfirst,make_timestr
from ..addr import MMGenID

# mixin class for TwUnspentOutputs,TwAddresses,TwTxHistory:
class TwCommon:

	dates_set   = False
	cols        = None
	reverse     = False
	group       = False
	sort_key    = 'age'
	interactive = False
	_display_data = {}
	filters = ()

	age_fmts = ('confs','block','days','date','date_time')
	age_fmts_date_dependent = ('days','date','date_time')
	age_fmts_interactive = ('confs','block','days','date')
	_age_fmt = 'confs'

	age_col_params = {
		'confs':     (7,  'Confs'),
		'block':     (8,  'Block'),
		'days':      (6,  'Age(d)'),
		'date':      (8,  'Date'),
		'date_time': (16, 'Date/Time'),
	}

	date_formatter = {
		'days': lambda rpc,secs: (rpc.cur_date - secs) // 86400 if secs else 0,
		'date': (
			lambda rpc,secs: '{}-{:02}-{:02}'.format(*time.gmtime(secs)[:3])[2:]
				if secs else '-       '),
		'date_time': (
			lambda rpc,secs: '{}-{:02}-{:02} {:02}:{:02}'.format(*time.gmtime(secs)[:5])
				if secs else '-               '),
	}

	tcols_errmsg = """
		--columns or MMGEN_COLUMNS value ({}) is too small to display the {}.
		Minimum value for this configuration: {}
	"""
	twid_errmsg = """
		Screen is too narrow to display the {}
		Please resize your screen to at least {} characters and hit any key:
	"""

	class display_type:

		class squeezed:
			detail = False
			fmt_method = 'gen_squeezed_display'
			need_column_widths = True
			item_separator = '\n'
			print_header = '[screen print truncated to width {}]\n'

		class detail:
			detail = True
			fmt_method = 'gen_detail_display'
			need_column_widths = True
			item_separator = '\n'
			print_header = ''

	def age_disp(self,o,age_fmt):
		if age_fmt == 'confs':
			return o.confs or '-'
		elif age_fmt == 'block':
			return self.rpc.blockcount + 1 - o.confs if o.confs else '-'
		else:
			return self.date_formatter[age_fmt](self.rpc,o.date)

	async def get_data(self,sort_key=None,reverse_sort=False):

		rpc_data = await self.get_rpc_data()

		if not rpc_data:
			die(0,fmt(self.no_rpcdata_errmsg).strip())

		lbl_id = ('account','label')['label_api' in self.rpc.caps]

		res = self.gen_data(rpc_data,lbl_id)
		self.data = MMGenList(await res if type(res).__name__ == 'coroutine' else res)
		self.disp_data = list(self.filter_data())

		if not self.data:
			die(1,self.no_data_errmsg)

		self.do_sort(key=sort_key,reverse=reverse_sort)

	@property
	def age_w(self):
		return self.age_col_params[self.age_fmt][0]

	@property
	def age_hdr(self):
		return self.age_col_params[self.age_fmt][1]

	@property
	def age_fmt(self):
		return self._age_fmt

	@age_fmt.setter
	def age_fmt(self,val):
		ok_vals,op_desc = (
			(self.age_fmts_interactive,'interactive') if self.interactive else
			(self.age_fmts,'non-interactive') )
		if val not in ok_vals:
			die('BadAgeFormat',
				f'{val!r}: invalid age format for {op_desc} operation (must be one of {ok_vals!r})' )
		self._age_fmt = val

	@property
	def disp_prec(self):
		return self.proto.coin_amt.max_prec

	def get_term_columns(self,min_cols):
		from ..term import get_terminal_size,get_char_raw
		while True:
			cols = g.columns or get_terminal_size().width
			if cols >= min_cols:
				return cols
			if sys.stdout.isatty():
				if g.columns:
					die(1,'\n'+fmt(self.tcols_errmsg.format(g.columns,self.desc,min_cols),indent='  '))
				else:
					get_char_raw('\n'+fmt(self.twid_errmsg.format(self.desc,min_cols),append=''))
			else:
				return min_cols

	sort_disp = {
		'addr':   'Addr',
		'age':    'Age',
		'amt':    'Amt',
		'txid':   'TxID',
		'twmmid': 'MMGenID',
	}

	def sort_info(self,include_group=True):
		ret = ([],['Reverse'])[self.reverse]
		ret.append(self.sort_disp[self.sort_key])
		if include_group and self.group and (self.sort_key in ('addr','txid','twmmid')):
			ret.append('Grouped')
		return ret

	sort_funcs = {
		'addr':   lambda i: i.addr,
		'age':    lambda i: 0 - i.confs,
		'amt':    lambda i: i.amt,
		'txid':   lambda i: f'{i.txid} {i.vout:04}',
		'twmmid': lambda i: i.twmmid.sort_key
	}

	def do_sort(self,key=None,reverse=False):
		key = key or self.sort_key
		if key not in self.sort_funcs:
			die(1,f'{key!r}: invalid sort key.  Valid options: {" ".join(self.sort_funcs)}')
		self.sort_key = key
		assert type(reverse) == bool
		self.data.sort(key=self.sort_funcs[key],reverse=reverse or self.reverse)

	def compute_column_widths(self,widths,maxws,minws,maxws_nice={},wide=False):

		def do_ret(freews):
			widths.update({k:minws[k] + freews.get(k,0) for k in minws})
			return namedtuple('column_widths',widths.keys())(*widths.values())

		def do_ret_max():
			widths.update({k:max(minws[k],maxws[k]) for k in minws})
			return namedtuple('column_widths',widths.keys())(*widths.values())

		def get_freews(cols,varws,varw,minw):
			freew = cols - minw
			if freew and varw:
				x = freew / varw
				freews = {k:int(varws[k] * x) for k in varws}
				remainder = freew - sum(freews.values())
				for k in varws:
					if not remainder:
						break
					if freews[k] < varws[k]:
						freews[k] += 1
						remainder -= 1
				return freews
			else:
				return {k:0 for k in varws}

		if wide:
			return do_ret_max()

		varws = {k:maxws[k] - minws[k] for k in maxws if maxws[k] > minws[k]}
		minw = sum(widths.values()) + sum(minws.values())
		varw = sum(varws.values())

		term_cols = self.get_term_columns(minw)
		self.cols = min(term_cols,minw + varw)

		if self.cols == minw + varw:
			return do_ret_max()

		if maxws_nice:
			# compute high-priority widths:
			varws_hp = {k: maxws_nice[k] - minws[k] if k in maxws_nice else varws[k] for k in varws}
			varw_hp = sum(varws_hp.values())
			widths_hp = get_freews(
				min(term_cols,minw + varw_hp),
				varws_hp,
				varw_hp,
				minw )
			# compute low-priority (nice) widths:
			varws_lp = {k: varws[k] - varws_hp[k] for k in maxws_nice if k in varws}
			widths_lp = get_freews(
				self.cols,
				varws_lp,
				sum(varws_lp.values()),
				minw + sum(widths_hp.values()) )
			# sum the two for each field:
			return do_ret({k:widths_hp[k] + widths_lp.get(k,0) for k in varws})
		else:
			return do_ret(get_freews(self.cols,varws,varw,minw))

	def header(self,color):

		Blue,Green = (blue,green) if color else (nocolor,nocolor)
		Yes,No,All = (green('yes'),red('no'),yellow('all')) if color else ('yes','no','all')

		def fmt_filter(k):
			return '{}:{}'.format(k,{0:No,1:Yes,2:All}[getattr(self,k)])

		return '{h} (sort order: {s}){f}\nNetwork: {n}\nBlock {b} [{d}]\n{t}'.format(
			h = self.hdr_lbl.upper(),
			f = '\nFilters: '+' '.join(fmt_filter(k) for k in self.filters) if self.filters else '',
			s = Blue(' '.join(self.sort_info())),
			n = Green(self.proto.coin + ' ' + self.proto.chain_name.upper()),
			b = self.rpc.blockcount.hl(color=color),
			d = make_timestr(self.rpc.cur_date),
			t = f'Total {self.proto.dcoin}: {self.total.hl(color=color)}\n' if hasattr(self,'total') else '',
		)

	def subheader(self,color):
		return ''

	def filter_data(self):
		return self.data.copy()

	async def format(self,display_type,color=True,cached=False,interactive=False):

		if not cached:

			dt = getattr(self.display_type,display_type)

			if self.has_age and (self.age_fmt in self.age_fmts_date_dependent or dt.detail):
				await self.set_dates(self.data)

			data = self.disp_data = list(self.filter_data()) # method could be a generator

			cw = self.get_column_widths(data,wide=dt.detail) if data and dt.need_column_widths else None

			self._display_data[display_type] = '{a}{b}\n{c}\n'.format(
				a = self.header(color),
				b = self.subheader(color),
				c = dt.item_separator.join(getattr(self,dt.fmt_method)(data,cw,color=color))
					if data else (nocolor,yellow)[color]('[no data for requested parameters]')
			)

		return self._display_data[display_type] + ('' if interactive else self.footer(color))

	def footer(self,color):
		return '\nTOTAL: {} {}\n'.format(
			self.total.hl(color=color) if hasattr(self,'total') else None,
			self.proto.dcoin
		) if hasattr(self,'total') else ''

	async def view_filter_and_sort(self):
		from ..opts import opt
		from ..term import get_char
		prompt = self.prompt.strip() + '\b'
		self.no_output = False
		self.oneshot_msg = None
		self.interactive = True
		immed_chars = ''.join(self.key_mappings.keys())

		CUR_RIGHT = lambda n: f'\033[{n}C'
		CUR_HOME  = '\033[H'
		ERASE_ALL = '\033[0J'
		self.cursor_to_end_of_prompt = CUR_RIGHT( len(prompt.split('\n')[-1]) - 2 )
		clear_screen = '\n\n' if (opt.no_blank or g.test_suite) else CUR_HOME + ERASE_ALL

		while True:
			reply = get_char(
				'' if self.no_output else (
					clear_screen
					+ await self.format('squeezed',interactive=True)
					+ '\n'
					+ (self.oneshot_msg or '')
					+ prompt
				),
				immed_chars = immed_chars )
			self.no_output = False
			self.oneshot_msg = '' if self.oneshot_msg else None # tristate, saves previous state
			if reply not in immed_chars:
				msg_r('\ninvalid keypress ')
				await asyncio.sleep(0.3)
				continue

			action = self.key_mappings[reply]
			if hasattr(self.action,action):
				await self.action().run(self,action)
			elif action.startswith('s_'): # put here to allow overriding by action method
				self.do_sort(action[2:])
			elif hasattr(self.item_action,action):
				await self.item_action().run(self,action)
			elif action == 'a_quit':
				msg('')
				return self.disp_data

	class action:

		async def run(self,parent,action):
			ret = getattr(self,action)(parent)
			if type(ret).__name__ == 'coroutine':
				await ret

		def d_days(self,parent):
			af = parent.age_fmts_interactive
			parent.age_fmt = af[(af.index(parent.age_fmt) + 1) % len(af)]
			if parent.update_widths_on_age_toggle: # TODO
				pass

		def d_redraw(self,parent):
			pass

		def d_reverse(self,parent):
			parent.data.reverse()
			parent.reverse = not parent.reverse

		async def a_print_detail(self,parent):
			return await self._print(parent,output_type='detail')

		async def a_print_squeezed(self,parent):
			return await self._print(parent,output_type='squeezed')

		async def _print(self,parent,output_type):
			outfile = '{}{}-{}{}[{}].out'.format(
				parent.dump_fn_pfx,
				f'-{output_type}' if len(parent.print_output_types) > 1 else '',
				parent.proto.dcoin,
				('' if parent.proto.network == 'mainnet' else '-'+parent.proto.network.upper()),
				','.join(parent.sort_info(include_group=False)).replace(' ','') )
			msg('')
			from ..fileutil import write_data_to_file
			from ..exception import UserNonConfirmation
			hdr = getattr(parent.display_type,output_type).print_header.format(parent.cols)
			try:
				write_data_to_file(
					outfile = outfile,
					data    = hdr + await parent.format(display_type=output_type,color=False),
					desc    = f'{parent.desc} listing' )
			except UserNonConfirmation as e:
				parent.oneshot_msg = yellow(f'File {outfile!r} not overwritten by user request\n\n')
			else:
				parent.oneshot_msg = green(f'Data written to {outfile!r}\n\n')

		async def a_view(self,parent):
			from ..ui import do_pager
			do_pager( await parent.format('squeezed',color=True,cached=True) )
			self.post_view(parent)

		async def a_view_detail(self,parent):
			from ..ui import do_pager
			do_pager( await parent.format('detail',color=True) )
			self.post_view(parent)

		def post_view(self,parent):
			if g.platform == 'linux' and parent.oneshot_msg == None:
				msg_r(parent.cursor_to_end_of_prompt)
				parent.no_output = True

	class item_action:

		async def run(self,parent,action):
			msg('')
			from ..ui import line_input
			while True:
				ret = line_input(f'Enter {parent.item_desc} number (or ENTER to return to main menu): ')
				if ret == '':
					return None
				idx = get_obj(MMGenIdx,n=ret,silent=True)
				if not idx or idx < 1 or idx > len(parent.disp_data):
					msg(f'Choice must be a single number between 1 and {len(parent.disp_data)}')
				elif (await getattr(self,action)(parent,idx)) != 'redo':
					break

		async def a_balance_refresh(self,parent,idx):
			from ..ui import keypress_confirm
			if not keypress_confirm(
					f'Refreshing tracking wallet {parent.item_desc} #{idx}.  Is this what you want?'):
				return 'redo'
			await parent.wallet.get_balance( parent.disp_data[idx-1].addr, force_rpc=True )
			await parent.get_data()
			parent.oneshot_msg = yellow(f'{parent.proto.dcoin} balance for account #{idx} refreshed\n\n')

		async def a_addr_delete(self,parent,idx):
			from ..ui import keypress_confirm
			if not keypress_confirm(
					'Removing {} {} from tracking wallet.  Is this what you want?'.format(
						parent.item_desc, red(f'#{idx}') )):
				return 'redo'
			if await parent.wallet.remove_address( parent.disp_data[idx-1].addr ):
				await parent.get_data()
				parent.oneshot_msg = yellow(f'{capfirst(parent.item_desc)} #{idx} removed\n\n')
			else:
				await asyncio.sleep(3)
				parent.oneshot_msg = red('Address could not be removed\n\n')

		async def a_comment_add(self,parent,idx):

			async def do_comment_add(comment):
				if await parent.wallet.set_comment( entry.twmmid, comment, entry.addr ):
					entry.comment = comment
					parent.oneshot_msg = yellow('Label {a} {b}{c}\n\n'.format(
						a = 'for' if cur_comment and comment else 'added to' if comment else 'removed from',
						b = desc,
						c = ' edited' if cur_comment and comment else '' ))
					return True
				else:
					await asyncio.sleep(3)
					parent.oneshot_msg = red('Label for {desc} could not be {action}\n\n'.format(
						desc = desc,
						action = 'edited' if cur_comment and comment else 'added' if comment else 'removed'
					))
					return False

			entry = parent.disp_data[idx-1]
			desc = f'{parent.item_desc} #{idx}'
			cur_comment = parent.disp_data[idx-1].comment
			msg('Current label: {}'.format(cur_comment.hl() if cur_comment else '(none)'))

			from ..ui import line_input
			res = line_input(
				'Enter label text for {} {}: '.format(parent.item_desc,red(f'#{idx}')),
				insert_txt = cur_comment )

			if res == cur_comment:
				parent.oneshot_msg = green(f'Label for {desc} unchanged\n\n')
				return None
			elif res == '':
				from ..ui import keypress_confirm
				if not keypress_confirm(f'Removing label for {desc}.  Is this what you want?'):
					return None

			return await do_comment_add(res)

class TwMMGenID(str,Hilite,InitErrors,MMGenObject):
	color = 'orange'
	width = 0
	trunc_ok = False
	def __new__(cls,proto,id_str):
		if type(id_str) == cls:
			return id_str
		try:
			ret = addr = disp = MMGenID(proto,id_str)
			sort_key,idtype = (ret.sort_key,'mmgen')
		except Exception as e:
			try:
				coin,addr = id_str.split(':',1)
				assert coin == proto.base_coin.lower(),(
					f'not a string beginning with the prefix {proto.base_coin.lower()!r}:' )
				assert addr.isascii() and addr.isalnum(), 'not an ASCII alphanumeric string'
				ret,sort_key,idtype,disp = (id_str,'z_'+id_str,'non-mmgen','non-MMGen')
				addr = proto.coin_addr(addr)
			except Exception as e2:
				return cls.init_fail(e,id_str,e2=e2)

		me = str.__new__(cls,ret)
		me.obj = ret
		me.disp = disp
		me.addr = addr
		me.sort_key = sort_key
		me.type = idtype
		me.proto = proto
		return me

# non-displaying container for TwMMGenID,TwComment
class TwLabel(str,InitErrors,MMGenObject):
	exc = 'BadTwLabel'
	passthru_excs = ('BadTwComment',)
	def __new__(cls,proto,text):
		if type(text) == cls:
			return text
		try:
			ts = text.split(None,1)
			mmid = TwMMGenID(proto,ts[0])
			comment = TwComment(ts[1] if len(ts) == 2 else '')
			me = str.__new__( cls, mmid + (' ' + comment if comment else '') )
			me.mmid = mmid
			me.comment = comment
			me.proto = proto
			return me
		except Exception as e:
			return cls.init_fail(e,text)

def get_tw_label(proto,s):
	"""
	raise an exception on a malformed comment, return None on an empty or invalid label
	"""
	try:
		return TwLabel(proto,s)
	except Exception as e:
		if type(e).__name__ == 'BadTwComment': # do it this way to avoid importing .exception
			raise
		else:
			return None
