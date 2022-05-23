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

import sys,time

from ..globalvars import g
from ..objmethods import Hilite,InitErrors,MMGenObject
from ..obj import TwComment,get_obj,MMGenIdx,MMGenList
from ..color import nocolor,red,yellow,green
from ..util import msg,msg_r,fmt,die,line_input,do_pager,capfirst,make_timestr
from ..addr import MMGenID

# mixin class for TwUnspentOutputs,TwAddrList:
class TwCommon:

	fmt_display = ''
	fmt_print   = ''
	cols        = None
	reverse     = False
	group       = False
	sort_key    = 'age'
	interactive = False

	age_fmts = ('confs','block','days','date','date_time')
	age_fmts_date_dependent = ('days','date','date_time')
	age_fmts_interactive = ('confs','block','days','date')
	_age_fmt = 'confs'

	date_formatter = {
		'days': lambda rpc,secs: (rpc.cur_date - secs) // 86400 if secs else 0,
		'date': (
			lambda rpc,secs: '{}-{:02}-{:02}'.format(*time.gmtime(secs)[:3])[2:]
				if secs else '--------' ),
		'date_time': (
			lambda rpc,secs: '{}-{:02}-{:02} {:02}:{:02}'.format(*time.gmtime(secs)[:5])
				if secs else '---------- -----' ),
	}

	def age_disp(self,o,age_fmt):
		if age_fmt == 'confs':
			return o.confs
		elif age_fmt == 'block':
			return self.rpc.blockcount - (o.confs - 1)
		else:
			return self.date_formatter[age_fmt](self.rpc,o.date)

	async def get_data(self,sort_key=None,reverse_sort=False):

		rpc_data = await self.get_rpc_data()

		if not rpc_data:
			die(0,fmt(self.no_rpcdata_errmsg).strip())

		lbl_id = ('account','label')['label_api' in self.rpc.caps]

		self.data = MMGenList(self.gen_data(rpc_data,lbl_id))

		if not self.data:
			die(1,self.no_data_errmsg)

		self.do_sort(key=sort_key,reverse=reverse_sort)

	@staticmethod
	async def set_dates(rpc,us):
		if us and us[0].date is None:
			# 'blocktime' differs from 'time', is same as getblockheader['time']
			dates = [ o.get('blocktime',0)
				for o in await rpc.gathered_call('gettransaction',[(o.txid,) for o in us]) ]
			for idx,o in enumerate(us):
				o.date = dates[idx]

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
					die(1,
						f'\n--columns or MMGEN_COLUMNS value ({g.columns}) is too small to display the {self.desc}.\n'
						+ f'Minimum value for this configuration: {min_cols}' )
				else:
					get_char_raw(
						f'\nScreen is too narrow to display the {self.desc}\n'
						+ f'Please resize your screen to at least {min_cols} characters and hit any key: ' )
			else:
				return min_cols

	def sort_info(self,include_group=True):
		ret = ([],['Reverse'])[self.reverse]
		ret.append(capfirst(self.sort_key).replace('Twmmid','MMGenID'))
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

	async def format_for_display(self):
		data = self.data
		if self.has_age and self.age_fmt in self.age_fmts_date_dependent:
			await self.set_dates(self.rpc,data)

		if not getattr(self,'column_params',None):
			self.set_column_params()

		if self.group and (self.sort_key in ('addr','txid','twmmid')):
			for a,b in [(data[i],data[i+1]) for i in range(len(data)-1)]:
				for k in ('addr','txid','twmmid'):
					if self.sort_key == k and getattr(a,k) == getattr(b,k):
						b.skip = (k,'addr')[k=='twmmid']

		self.fmt_display = (
			self.hdr_fmt.format(
				a = ' '.join(self.sort_info()),
				b = self.proto.dcoin,
				c = self.total.hl() if hasattr(self,'total') else None )
			+ ('\nChain: '+green(self.proto.chain_name.upper()) if self.proto.chain_name != 'mainnet' else '')
			+ '\n' + '\n'.join(self.gen_display_output(self.column_params))
			+ '\n'
		)

		return self.fmt_display

	async def format_for_printing(self,color=False,show_confs=True):
		if self.has_age:
			await self.set_dates(self.rpc,self.data)

		self.fmt_print = self.print_hdr_fs.format(
			a = capfirst(self.desc),
			b = self.rpc.blockcount,
			c = make_timestr(self.rpc.cur_date),
			d = ('' if self.proto.chain_name == 'mainnet' else
				'Chain: {}\n'.format((nocolor,green)[color](self.proto.chain_name.upper())) ),
			e = ' '.join(self.sort_info(include_group=False)),
			f = '\n'.join(self.gen_print_output(color,show_confs)),
			g = self.proto.dcoin,
			h = self.total.hl(color=color) if hasattr(self,'total') else None )

		return self.fmt_print

	async def view_and_sort(self):
		from ..opts import opt
		from ..term import get_char
		self.prompt = type(self).prompt.strip() + '\b'
		self.no_output = False
		self.oneshot_msg = None
		self.interactive = True
		CUR_HOME  = '\033[H'
		ERASE_ALL = '\033[0J'

		while True:
			msg_r('' if self.no_output else '\n\n' if opt.no_blank else CUR_HOME+ERASE_ALL)
			reply = get_char(
				'' if self.no_output else (
					await self.format_for_display()
					+ '\n'
					+ (self.oneshot_msg or '')
					+ self.prompt
				),
				immed_chars = ''.join(self.key_mappings.keys())
			)
			self.no_output = False
			self.oneshot_msg = '' if self.oneshot_msg else None # tristate, saves previous state
			if reply not in self.key_mappings:
				msg_r('\ninvalid keypress ')
				time.sleep(0.5)
				continue

			action = self.key_mappings[reply]
			if action.startswith('s_'):
				self.do_sort(action[2:])
				if action == 's_twmmid':
					self.show_mmid = True
			elif action == 'd_days':
				af = self.age_fmts_interactive
				self.age_fmt = af[(af.index(self.age_fmt) + 1) % len(af)]
				if self.update_params_on_age_toggle:
					self.set_column_params()
			elif action == 'd_mmid':
				self.show_mmid = not self.show_mmid
			elif action == 'd_group':
				if self.can_group:
					self.group = not self.group
			elif action == 'd_redraw':
				self.set_column_params()
			elif action == 'd_reverse':
				self.data.reverse()
				self.reverse = not self.reverse
			elif action == 'a_quit':
				msg('')
				return self.data
			elif hasattr(self.action,action):
				await self.action(self).run(action)
			elif hasattr(self.item_action,action):
				await self.item_action(self).run(action)
				self.set_column_params()

	class action:

		def __init__(self,parent):
			self.parent = parent

		async def run(self,action):
			await getattr(self,action)(self.parent)

		async def a_print(self,parent):
			outfile = '{}-{}{}[{}].out'.format(
				parent.dump_fn_pfx,
				parent.proto.dcoin,
				('' if parent.proto.network == 'mainnet' else '-'+parent.proto.network.upper()),
				','.join(parent.sort_info(include_group=False)).lower() )
			msg('')
			from ..fileutil import write_data_to_file
			from ..exception import UserNonConfirmation
			try:
				write_data_to_file(
					outfile,
					await parent.format_for_printing(color=False),
					desc = f'{parent.desc} listing' )
			except UserNonConfirmation as e:
				parent.oneshot_msg = red(f'File {outfile!r} not overwritten by user request\n\n')
			else:
				parent.oneshot_msg = yellow(f'Data written to {outfile!r}\n\n')

		async def a_view(self,parent):
			do_pager(parent.fmt_display)
			self.post_view(parent)

		async def a_view_wide(self,parent):
			do_pager( await parent.format_for_printing(color=True) )
			self.post_view(parent)

		def post_view(self,parent):
			if g.platform == 'linux' and parent.oneshot_msg == None:
				CUR_RIGHT = lambda n: f'\033[{n}C'
				msg_r(CUR_RIGHT(len(parent.prompt.split('\n')[-1])-2))
				parent.no_output = True

	class item_action:

		def __init__(self,parent):
			self.parent = parent

		async def run(self,action):
			msg('')
			while True:
				ret = line_input(f'Enter {self.parent.item_desc} number (or RETURN to return to main menu): ')
				if ret == '':
					return None
				idx = get_obj(MMGenIdx,n=ret,silent=True)
				if not idx or idx < 1 or idx > len(self.parent.data):
					msg(f'Choice must be a single number between 1 and {len(self.parent.data)}')
				elif (await getattr(self,action)(self.parent,idx)) != 'redo':
					break

class TwMMGenID(str,Hilite,InitErrors,MMGenObject):
	color = 'orange'
	width = 0
	trunc_ok = False
	def __new__(cls,proto,id_str):
		if type(id_str) == cls:
			return id_str
		ret = None
		try:
			ret = MMGenID(proto,id_str)
			sort_key,idtype = ret.sort_key,'mmgen'
		except Exception as e:
			try:
				assert id_str.split(':',1)[0] == proto.base_coin.lower(),(
					f'not a string beginning with the prefix {proto.base_coin.lower()!r}:' )
				assert id_str.isascii() and id_str[4:].isalnum(), 'not an ASCII alphanumeric string'
				assert len(id_str) > 4,'not more that four characters long'
				ret,sort_key,idtype = str(id_str),'z_'+id_str,'non-mmgen'
			except Exception as e2:
				return cls.init_fail(e,id_str,e2=e2)

		me = str.__new__(cls,ret)
		me.obj = ret
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
