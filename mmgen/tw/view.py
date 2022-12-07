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
tw.view: base class for tracking wallet view classes
"""

import sys,time,asyncio
from collections import namedtuple

from ..globalvars import g
from ..opts import opt
from ..objmethods import Hilite,InitErrors,MMGenObject
from ..obj import get_obj,MMGenIdx,MMGenList
from ..color import nocolor,yellow,green,red,blue
from ..util import msg,msg_r,fmt,die,capfirst,make_timestr
from ..rpc import rpc_init
from ..base_obj import AsyncInit

CUR_HOME  = '\033[H'
CUR_RIGHT = lambda n: f'\033[{n}C'
ERASE_ALL = '\033[0J'

# base class for TwUnspentOutputs,TwAddresses,TwTxHistory:
class TwView(MMGenObject,metaclass=AsyncInit):

	class display_type:

		class squeezed:
			detail = False
			fmt_method = 'gen_squeezed_display'
			line_fmt_method = 'squeezed_format_line'
			hdr_fmt_method = 'squeezed_col_hdr'
			need_column_widths = True
			item_separator = '\n'
			print_header = '[screen print truncated to width {}]\n'

		class detail:
			detail = True
			fmt_method = 'gen_detail_display'
			line_fmt_method = 'detail_format_line'
			hdr_fmt_method = 'detail_col_hdr'
			need_column_widths = True
			item_separator = '\n'
			print_header = ''

	class line_processing:

		class print:
			def do(method,data,cw,fs,color,fmt_method):
				return [l.rstrip() for l in method(data,cw,fs,color,fmt_method)]

	has_wallet  = True
	has_amt2    = False
	dates_set   = False
	reverse     = False
	group       = False
	use_cached  = False
	txid_w      = 64
	sort_key    = 'age'
	display_hdr = ()
	display_body = ()
	nodata_msg = '[no data for requested parameters]'
	cols = 0
	term_height = 0
	term_width = 0
	filters = ()

	fp = namedtuple('fs_params',['fs_key','hdr_fs_repl','fs_repl','hdr_fs','fs'])
	fs_params = {
		'num':       fp('n', True, True,  ' {n:>%s}', ' {n:>%s}'),
		'txid':      fp('t', True, False, ' {t:%s}',  ' {t}'),
		'vout':      fp('v', True, False, '{v:%s}',   '{v}'),
		'used':      fp('u', True, False, ' {u:%s}',  ' {u}'),
		'addr':      fp('a', True, False, ' {a:%s}',  ' {a}'),
		'mmid':      fp('m', True, False, ' {m:%s}',  ' {m}'),
		'comment':   fp('c', True, False, ' {c:%s}',  ' {c}'),
		'amt':       fp('A', True, False, ' {A:%s}',  ' {A}'),
		'amt2':      fp('B', True, False, ' {B:%s}',  ' {B}'),
		'date':      fp('d', True, True,  ' {d:%s}',  ' {d:<%s}'),
		'date_time': fp('D', True, True,  ' {D:%s}',  ' {D:%s}'),
		'block':     fp('b', True, True,  ' {b:%s}',  ' {b:<%s}'),
		'inputs':    fp('i', True, False, ' {i:%s}',  ' {i}'),
		'outputs':   fp('o', True, False, ' {o:%s}',  ' {o}'),
	}

	age_fmts = ('confs','block','days','date','date_time')
	age_fmts_date_dependent = ('days','date','date_time')
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
	twidth_errmsg = """
		Screen is too narrow to display the {}
		Please resize your screen to at least {} characters and hit any key:
	"""

	squeezed_format_line = None
	detail_format_line = None

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(proto.base_proto_subclass(cls,cls.mod_subpath))

	async def __init__(self,proto):
		self.proto = proto
		self.rpc = await rpc_init(proto)
		if self.has_wallet:
			from .ctl import TwCtl
			self.twctl = await TwCtl(proto,mode='w')
		self.amt_keys = {'amt':'iwidth','amt2':'iwidth2'} if self.has_amt2 else {'amt':'iwidth'}

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
		if val not in self.age_fmts:
			die( 'BadAgeFormat', f'{val!r}: invalid age format (must be one of {self.age_fmts!r})' )
		self._age_fmt = val

	def age_disp(self,o,age_fmt):
		if age_fmt == 'confs':
			return o.confs or '-'
		elif age_fmt == 'block':
			return self.rpc.blockcount + 1 - o.confs if o.confs else '-'
		else:
			return self.date_formatter[age_fmt](self.rpc,o.date)

	def get_disp_prec(self,wide):
		return self.proto.coin_amt.max_prec

	sort_disp = {
		'addr':   'Addr',
		'age':    'Age',
		'amt':    'Amt',
		'txid':   'TxID',
		'twmmid': 'MMGenID',
	}

	sort_funcs = {
		'addr':   lambda i: i.addr,
		'age':    lambda i: 0 - i.confs,
		'amt':    lambda i: i.amt,
		'txid':   lambda i: f'{i.txid} {i.vout:04}',
		'twmmid': lambda i: i.twmmid.sort_key
	}

	def sort_info(self,include_group=True):
		ret = ([],['Reverse'])[self.reverse]
		ret.append(self.sort_disp[self.sort_key])
		if include_group and self.group and (self.sort_key in ('addr','txid','twmmid')):
			ret.append('Grouped')
		return ret

	def do_sort(self,key=None,reverse=False):
		key = key or self.sort_key
		if key not in self.sort_funcs:
			die(1,f'{key!r}: invalid sort key.  Valid options: {" ".join(self.sort_funcs)}')
		self.sort_key = key
		assert type(reverse) == bool
		self.data.sort(key=self.sort_funcs[key],reverse=reverse or self.reverse)

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

	def filter_data(self):
		return self.data.copy()

	def get_term_dimensions(self,min_cols):
		from ..term import get_terminal_size,get_char_raw,_term_dimensions
		while True:
			ts = get_terminal_size()
			cols = g.columns or ts.width
			if cols >= min_cols:
				return _term_dimensions(cols,ts.height)
			if sys.stdout.isatty():
				if g.columns:
					die(1,'\n'+fmt(self.tcols_errmsg.format(g.columns,self.desc,min_cols),indent='  '))
				else:
					get_char_raw('\n'+fmt(self.twidth_errmsg.format(self.desc,min_cols),append=''))
			else:
				return _term_dimensions(min_cols,ts.height)

	def compute_column_widths(self,widths,maxws,minws,maxws_nice={},wide=False):

		def do_ret(freews):
			widths.update({k:minws[k] + freews.get(k,0) for k in minws})
			widths.update({ikey: widths[key] - self.disp_prec - 1 for key,ikey in self.amt_keys.items()})
			return namedtuple('column_widths',widths.keys())(*widths.values())

		def do_ret_max():
			widths.update({k:max(minws[k],maxws[k]) for k in minws})
			widths.update({ikey: widths[key] - self.disp_prec - 1 for key,ikey in self.amt_keys.items()})
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

		varws = {k:maxws[k] - minws[k] for k in maxws if maxws[k] > minws[k]}
		minw = sum(widths.values()) + sum(minws.values())
		varw = sum(varws.values())

		td = self.get_term_dimensions(minw)
		self.term_height = td.height
		self.term_width = td.width

		self.cols = min(self.term_width,minw + varw)

		if wide or self.cols == minw + varw:
			return do_ret_max()

		if maxws_nice:
			# compute high-priority widths:
			varws_hp = {k: maxws_nice[k] - minws[k] if k in maxws_nice else varws[k] for k in varws}
			varw_hp = sum(varws_hp.values())
			widths_hp = get_freews(
				min(self.term_width,minw + varw_hp),
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

	def gen_subheader(self,color):
		return ()

	def gen_footer(self,color):
		if hasattr(self,'total'):
			yield 'TOTAL: {} {}'.format( self.total.hl(color=color), self.proto.dcoin )

	def set_amt_widths(self,data):
		# width of amts column: min(7,width of integer part) + len('.') + width of fractional part
		self.amt_widths = {k:
			min(7,max(len(str(getattr(d,k).to_integral_value())) for d in data)) + 1 + self.disp_prec
				for k in self.amt_keys}

	async def format(self,display_type,color=True,interactive=False,line_processing=None):

		async def make_display(color):

			def gen_display_hdr():

				Blue,Green = (blue,green) if color else (nocolor,nocolor)
				Yes,No,All = (green('yes'),red('no'),yellow('all')) if color else ('yes','no','all')
				sort_info = ' '.join(self.sort_info())

				def fmt_filter(k):
					return '{}:{}'.format(k,{0:No,1:Yes,2:All}[getattr(self,k)])

				yield '{} (sort order: {}){}'.format(
					self.hdr_lbl.upper(),
					Blue(sort_info),
					' ' * (self.cols - len('{} (sort order: {})'.format(self.hdr_lbl,sort_info))) )

				if self.filters:
					yield 'Filters: {}{}'.format(
						' '.join(map(fmt_filter,self.filters)),
						' ' * len(self.filters) )

				yield 'Network: {}'.format(Green(
					self.proto.coin + ' ' + self.proto.chain_name.upper() ))

				yield 'Block {} [{}]'.format(
					self.rpc.blockcount.hl(color=color),
					make_timestr(self.rpc.cur_date) )

				if hasattr(self,'total'):
					yield 'Total {}: {}'.format( self.proto.dcoin, self.total.hl(color=color) )

				yield from self.gen_subheader(color)

				yield ''

				if data:
					yield getattr(self,dt.hdr_fmt_method)(cw,hdr_fs,color)

			self.disp_prec = self.get_disp_prec(wide=dt.detail)

			if self.has_age and (self.age_fmt in self.age_fmts_date_dependent or dt.detail):
				await self.set_dates(self.data)

			data = self.disp_data = list(self.filter_data()) # method could be a generator

			if data and dt.need_column_widths:
				self.set_amt_widths(data)
				cw = self.get_column_widths(data,wide=dt.detail)
				cwh = cw._asdict()
				fp = self.fs_params
				hdr_fs = ''.join(fp[name].hdr_fs % ((),cwh[name])[fp[name].hdr_fs_repl]
					for name in dt.cols if cwh[name])
				fs = ''.join(fp[name].fs % ((),cwh[name])[fp[name].fs_repl]
					for name in dt.cols if cwh[name])
			else:
				cw = hdr_fs = fs = None

			def get_body(method):
				if line_processing:
					return getattr(self.line_processing,line_processing).do(
						method,data,cw,fs,color,getattr(self,dt.line_fmt_method))
				else:
					return method(data,cw,fs,color,getattr(self,dt.line_fmt_method))

			display_hdr = tuple(gen_display_hdr())

			display_body = tuple(
				get_body(getattr(self,dt.fmt_method)) if data else
				[(nocolor,yellow)[color](self.nodata_msg)] )

			return (display_hdr,display_body)

		dt = getattr(self.display_type,display_type)

		if self.use_cached:
			self.use_cached = False
			display_hdr = self.display_hdr
			display_body = self.display_body
		else:
			display_hdr,display_body = await make_display(color)
			if not dt.detail:
				self.display_hdr = display_hdr
				self.display_body = display_body

		if interactive:
			footer = ''
		else:
			footer = '\n'.join(self.gen_footer(color))
			footer = ('\n\n' + footer if footer else '') + '\n'

		return (
			'\n'.join(display_hdr) + '\n'
			+ dt.item_separator.join(display_body)
			+ footer
		)

	async def view_filter_and_sort(self):

		from ..term import get_char

		prompt = self.prompt.strip() + '\b'

		self.prompt_height = len(prompt.split('\n'))
		self.no_output = False
		self.oneshot_msg = None

		self.cursor_to_end_of_prompt = CUR_RIGHT( len(prompt.split('\n')[-1]) - 2 )
		clear_screen = '\n\n' if (opt.no_blank or g.test_suite) else CUR_HOME + ERASE_ALL

		while True:
			reply = get_char(
				'' if self.no_output else (
					clear_screen
					+ await self.format('squeezed',interactive=True)
					+ '\n\n'
					+ (self.oneshot_msg + '\n\n' if self.oneshot_msg else '')
					+ prompt
				),
				immed_chars = self.key_mappings )

			self.no_output = False
			self.oneshot_msg = '' if self.oneshot_msg else None # tristate, saves previous state

			if reply not in self.key_mappings:
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

	def keypress_confirm(self,*args,**kwargs):
		from ..ui import keypress_confirm
		if keypress_confirm(*args,**kwargs):
			return True
		else:
			return False

	class action:

		async def run(self,parent,action):
			ret = getattr(self,action)(parent)
			if type(ret).__name__ == 'coroutine':
				await ret

		def d_days(self,parent):
			af = parent.age_fmts
			parent.age_fmt = af[(af.index(parent.age_fmt) + 1) % len(af)]
			if parent.update_widths_on_age_toggle: # TODO
				pass

		def d_redraw(self,parent):
			msg_r(CUR_HOME+ERASE_ALL)

		def d_reverse(self,parent):
			parent.data.reverse()
			parent.reverse = not parent.reverse

		async def a_print_detail(self,parent):
			return await self._print(parent,output_type='detail')

		async def a_print_squeezed(self,parent):
			return await self._print(parent,output_type='squeezed')

		async def _print(self,parent,output_type):

			if not parent.disp_data:
				return None

			outfile = '{}{}-{}{}[{}].out'.format(
				parent.dump_fn_pfx,
				f'-{output_type}' if len(parent.print_output_types) > 1 else '',
				parent.proto.dcoin,
				('' if parent.proto.network == 'mainnet' else '-'+parent.proto.network.upper()),
				','.join(parent.sort_info(include_group=False)).replace(' ','') )
			msg('')
			from ..fileutil import write_data_to_file
			from ..exception import UserNonConfirmation
			print_hdr = getattr(parent.display_type,output_type).print_header.format(parent.cols)
			try:
				write_data_to_file(
					outfile = outfile,
					data = print_hdr + await parent.format(
						display_type = output_type,
						line_processing = 'print',
						color = False ),
					desc = f'{parent.desc} listing' )
			except UserNonConfirmation as e:
				parent.oneshot_msg = yellow(f'File {outfile!r} not overwritten by user request')
			else:
				parent.oneshot_msg = green(f'Data written to {outfile!r}')

		async def a_view(self,parent):
			from ..ui import do_pager
			parent.use_cached = True
			do_pager( await parent.format('squeezed',color=True) )
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

			if not parent.disp_data:
				return None

			msg('')
			from ..ui import line_input
			while True:
				ret = line_input(f'Enter {parent.item_desc} number (or ENTER to return to main menu): ')
				if ret == '':
					return None
				idx = get_obj(MMGenIdx,n=ret,silent=True)
				if not idx or idx < 1 or idx > len(parent.disp_data):
					msg_r(f'Choice must be a single number between 1 and {len(parent.disp_data)}{nl}')
				else:
					ret = await getattr(self,action)(parent,idx)
					if ret == 'redo':
						await asyncio.sleep(0.5)
						continue
					else:
						break

		async def a_balance_refresh(self,parent,idx):
			if not parent.keypress_confirm(
					f'Refreshing tracking wallet {parent.item_desc} #{idx}.  Is this what you want?'):
				return 'redo'
			await parent.twctl.get_balance( parent.disp_data[idx-1].addr, force_rpc=True )
			await parent.get_data()
			parent.oneshot_msg = yellow(f'{parent.proto.dcoin} balance for account #{idx} refreshed')

		async def a_addr_delete(self,parent,idx):
			if not parent.keypress_confirm(
					'Removing {} {} from tracking wallet.  Is this what you want?'.format(
						parent.item_desc, red(f'#{idx}') )):
				return 'redo'
			if await parent.twctl.remove_address( parent.disp_data[idx-1].addr ):
				await parent.get_data()
				parent.oneshot_msg = yellow(f'{capfirst(parent.item_desc)} #{idx} removed')
			else:
				await asyncio.sleep(3)
				parent.oneshot_msg = red('Address could not be removed')

		async def a_comment_add(self,parent,idx):

			async def do_comment_add(comment):

				if await parent.twctl.set_comment( entry.twmmid, comment, entry.addr, silent=True ):
					entry.comment = comment
					edited = cur_comment and comment
					parent.oneshot_msg = (green if comment else yellow)('Label {a} {b}{c}'.format(
						a = 'for' if edited else 'added to' if comment else 'removed from',
						b = desc,
						c = ' edited' if edited else '' ))
					return True
				else:
					await asyncio.sleep(3)
					parent.oneshot_msg = red('Label for {desc} could not be {action}'.format(
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
				parent.oneshot_msg = yellow(f'Label for {desc} unchanged')
				return None
			elif res == '':
				if not parent.keypress_confirm(f'Removing label for {desc}.  Is this what you want?'):
					return 'redo'

			return await do_comment_add(res)
