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

import time

from ..globalvars import g
from ..objmethods import Hilite,InitErrors,MMGenObject
from ..obj import TwComment,get_obj,MMGenIdx
from ..color import red,yellow
from ..util import msg,msg_r,die,line_input,do_pager,capfirst
from ..addr import MMGenID

# mixin class for TwUnspentOutputs,TwAddrList:
class TwCommon:

	fmt_display = ''
	fmt_print   = ''
	cols        = None
	reverse     = False
	group       = False
	sort_key    = 'age'

	age_fmts = ('confs','block','days','date','date_time')
	age_fmts_date_dependent = ('days','date','date_time')
	age_fmts_interactive = ('confs','block','days','date')
	_age_fmt = 'confs'

	date_formatter = {
		'days':      lambda rpc,secs: (rpc.cur_date - secs) // 86400,
		'date':      lambda rpc,secs: '{}-{:02}-{:02}'.format(*time.gmtime(secs)[:3])[2:],
		'date_time': lambda rpc,secs: '{}-{:02}-{:02} {:02}:{:02}'.format(*time.gmtime(secs)[:5]),
	}

	def age_disp(self,o,age_fmt):
		if age_fmt == 'confs':
			return o.confs
		elif age_fmt == 'block':
			return self.rpc.blockcount - (o.confs - 1)
		else:
			return self.date_formatter[age_fmt](self.rpc,o.date)

	@staticmethod
	async def set_dates(rpc,us):
		if us and us[0].date is None:
			# 'blocktime' differs from 'time', is same as getblockheader['time']
			dates = [o['blocktime'] for o in await rpc.gathered_call('gettransaction',[(o.txid,) for o in us])]
			for idx,o in enumerate(us):
				o.date = dates[idx]

	@property
	def age_fmt(self):
		return self._age_fmt

	@age_fmt.setter
	def age_fmt(self,val):
		if val not in self.age_fmts:
			die( 'BadAgeFormat', f'{val!r}: invalid age format (must be one of {self.age_fmts!r})' )
		self._age_fmt = val

	@property
	def disp_prec(self):
		return self.proto.coin_amt.max_prec

	def set_term_columns(self):
		from ..term import get_terminal_size
		while True:
			self.cols = g.terminal_width or get_terminal_size().width
			if self.cols >= g.min_screen_width:
				break
			line_input(
				'Screen too narrow to display the tracking wallet\n'
				+ f'Please resize your screen to at least {g.min_screen_width} characters and hit ENTER ' )

	def sort_info(self,include_group=True):
		ret = ([],['Reverse'])[self.reverse]
		ret.append(capfirst(self.sort_key).replace('Twmmid','MMGenID'))
		if include_group and self.group and (self.sort_key in ('addr','txid','twmmid')):
			ret.append('Grouped')
		return ret

	def do_sort(self,key=None,reverse=False):
		sort_funcs = {
			'addr':   lambda i: i.addr,
			'age':    lambda i: 0 - i.confs,
			'amt':    lambda i: i.amt,
			'txid':   lambda i: f'{i.txid} {i.vout:04}',
			'twmmid': lambda i: i.twmmid.sort_key
		}
		key = key or self.sort_key
		if key not in sort_funcs:
			die(1,f'{key!r}: invalid sort key.  Valid options: {" ".join(sort_funcs.keys())}')
		self.sort_key = key
		assert type(reverse) == bool
		self.data.sort(key=sort_funcs[key],reverse=reverse or self.reverse)

	async def item_action_loop(self,action):
		msg('')
		while True:
			ret = line_input(f'Enter {self.item_desc} number (or RETURN to return to main menu): ')
			if ret == '':
				return None
			idx = get_obj(MMGenIdx,n=ret,silent=True)
			if not idx or idx < 1 or idx > len(self.data):
				msg(f'Choice must be a single number between 1 and {len(self.data)}')
			elif (await action(self,idx)) != 'redo':
				break

	async def view_and_sort(self,tx):
		from ..opts import opt
		from ..term import get_char
		prompt = self.prompt.strip() + '\b'
		no_output = False
		self.oneshot_msg = None
		CUR_HOME  = '\033[H'
		ERASE_ALL = '\033[0J'
		CUR_RIGHT = lambda n: f'\033[{n}C'

		while True:
			msg_r('' if no_output else '\n\n' if opt.no_blank else CUR_HOME+ERASE_ALL)
			reply = get_char(
				'' if no_output else await self.format_for_display()+'\n'+(self.oneshot_msg or '')+prompt,
				immed_chars=''.join(self.key_mappings.keys())
			)
			no_output = False
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
			elif action == 'd_mmid':
				self.show_mmid = not self.show_mmid
			elif action == 'd_group':
				if self.can_group:
					self.group = not self.group
			elif action == 'd_redraw':
				pass
			elif action == 'd_reverse':
				self.data.reverse()
				self.reverse = not self.reverse
			elif action == 'a_quit':
				msg('')
				return self.data
			elif action == 'a_print':
				of = '{}-{}[{}].out'.format(
					self.dump_fn_pfx,
					self.proto.dcoin,
					','.join(self.sort_info(include_group=False)).lower() )
				msg('')
				from ..fileutil import write_data_to_file
				from ..exception import UserNonConfirmation
				try:
					write_data_to_file(
						of,
						await self.format_for_printing(color=False),
						desc = f'{self.desc} listing' )
				except UserNonConfirmation as e:
					self.oneshot_msg = red(f'File {of!r} not overwritten by user request\n\n')
				else:
					self.oneshot_msg = yellow(f'Data written to {of!r}\n\n')
			elif action in ('a_view','a_view_wide'):
				do_pager(
					self.fmt_display if action == 'a_view' else
					await self.format_for_printing(color=True) )
				if g.platform == 'linux' and self.oneshot_msg == None:
					msg_r(CUR_RIGHT(len(prompt.split('\n')[-1])-2))
					no_output = True
			elif hasattr(self,'item_action') and hasattr(self.item_action,action):
				await self.item_action_loop(getattr(self.item_action(),action))
				self.display_constants = self.get_display_constants()

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
