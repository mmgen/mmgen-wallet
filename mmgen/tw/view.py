#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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

import sys, time, asyncio
from collections import namedtuple

from ..cfg import gv
from ..objmethods import MMGenObject
from ..obj import get_obj, MMGenIdx, MMGenList
from ..color import nocolor, yellow, orange, green, red, blue
from ..util import msg, msg_r, fmt, die, capfirst, suf, make_timestr, isAsync, is_int
from ..rpc import rpc_init
from ..base_obj import AsyncInit

# these are replaced by fake versions in overlay:
CUR_HOME  = '\033[H'
CUR_UP    = lambda n: f'\033[{n}A'
CUR_DOWN  = lambda n: f'\033[{n}B'
ERASE_ALL = '\033[0J'

# decorator for action.run():
def enable_echo(orig_func):
	async def f(self, parent, action_method):
		if parent.scroll:
			parent.term.set('echo')
		ret = await orig_func(self, parent, action_method)
		if parent.scroll:
			parent.term.set('noecho')
		return ret
	return f

# base class for TwUnspentOutputs, TwAddresses, TwTxHistory:
class TwView(MMGenObject, metaclass=AsyncInit):

	class display_type:

		class squeezed:
			detail = False
			fmt_method = 'gen_squeezed_display'
			line_fmt_method = 'squeezed_format_line'
			subhdr_fmt_method = 'gen_subheader'
			colhdr_fmt_method = 'squeezed_col_hdr'
			need_column_widths = True
			item_separator = '\n'
			print_header = '[screen print truncated to width {}]\n'

		class detail:
			detail = True
			fmt_method = 'gen_detail_display'
			line_fmt_method = 'detail_format_line'
			subhdr_fmt_method = 'gen_subheader'
			colhdr_fmt_method = 'detail_col_hdr' # set to None to disable
			need_column_widths = True
			item_separator = '\n'
			print_header = ''

	class line_processing:

		class print:
			@staticmethod
			def do(method, data, cw, fs, color, fmt_method):
				return [l.rstrip() for l in method(data, cw, fs, color, fmt_method)]

	is_account_based = False
	has_age     = False
	has_used    = False
	has_wallet  = True
	has_amt2    = False
	dates_set   = False
	reverse     = False
	group       = False
	groupable   = {}
	use_cached  = False
	minconf     = 1
	txid_w      = 0
	txid_max_w  = {}
	txid_min_w  = {}
	txid_nice_w = {}
	nice_addr_w = {'addr': 14}
	sort_key    = 'age'
	display_hdr = ()
	display_body = ()
	prompt_fs_repl = {}
	removed_key_mappings = {}
	nodata_msg = '[no data for requested parameters]'
	cols = 0
	term_height = 0
	term_width = 0
	scrollable_height = 0
	min_scrollable_height = 5
	addr_view_pref = 0
	pos = 0
	filters = ()

	column_widths_data = namedtuple('twview_column_widths', ['widths', 'maxws', 'minws', 'maxws_nice'])
	fp = namedtuple('fs_params', ['fs_key', 'hdr_fs_repl', 'fs_repl', 'hdr_fs', 'fs'])
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
		'addr_idx':  fp('I', True, False, ' {I:%s}',  ' {I}'),
		'date':      fp('d', True, True,  ' {d:%s}',  ' {d:<%s}'),
		'date_time': fp('D', True, True,  ' {D:%s}',  ' {D:%s}'),
		'block':     fp('b', True, True,  ' {b:%s}',  ' {b:<%s}'),
		'inputs':    fp('i', True, False, ' {i:%s}',  ' {i}'),
		'outputs':   fp('o', True, False, ' {o:%s}',  ' {o}')}

	age_fmts = ('confs', 'block', 'days', 'date', 'date_time')
	age_fmts_date_dependent = ('days', 'date', 'date_time')
	_age_fmt = 'confs'

	bch_addr_fmts = ('cashaddr', 'legacy')

	age_col_params = {
		'confs':     (0, 'Confs'),
		'block':     (0, 'Block'),
		'days':      (0, 'Age(d)'),
		'date':      (0, 'Date'),
		'date_time': (0, 'Date/Time')}

	date_formatter = {
		'days': lambda rpc, secs: (rpc.cur_date - secs) // 86400 if secs else 0,
		'date': (
			lambda rpc, secs: '{}-{:02}-{:02}'.format(*time.gmtime(secs)[:3])[2:]
				if secs else '-       '),
		'date_time': (
			lambda rpc, secs: '{}-{:02}-{:02} {:02}:{:02}'.format(*time.gmtime(secs)[:5])
				if secs else '-               ')}

	twidth_diemsg = """
		--columns or MMGEN_COLUMNS value ({}) is too small to display the {}
		Minimum value for this configuration: {}
	"""
	twidth_errmsg = """
		Screen is too narrow to display the {} with current configuration
		Please resize your screen to at least {} characters and hit any key:
	"""
	theight_errmsg = """
		Terminal window is too small to display the {} with current configuration
		Please resize it to at least {} lines and hit any key:
	"""

	squeezed_format_line = None
	detail_format_line = None
	scroll_keys = {
		'vi': {
			'k': 'm_cursor_up',
			'j': 'm_cursor_down',
			'b': 'm_pg_up',
			'f': 'm_pg_down',
			'g': 'm_top',
			'G': 'm_bot'},
		'linux': {
			'\x1b[A': 'm_cursor_up',
			'\x1b[B': 'm_cursor_down',
			'\x1b[5~': 'm_pg_up',
			'\x1b[6~': 'm_pg_down',
			'\x1b[7~': 'm_top',
			'\x1b[8~': 'm_bot'},
		'win32': {
			'\xe0H': 'm_cursor_up',
			'\xe0P': 'm_cursor_down',
			'\xe0I': 'm_pg_up',
			'\xe0Q': 'm_pg_down',
			'\xe0G': 'm_top',
			'\xe0O': 'm_bot'}}
	scroll_keys['darwin'] = scroll_keys['linux']
	extra_key_mappings = {}

	def __new__(cls, cfg, proto, *args, **kwargs):
		return MMGenObject.__new__(proto.base_proto_subclass(cls, cls.mod_subpath))

	async def __init__(self, cfg, proto):
		self.cfg = cfg
		self.proto = proto
		if have_rpc := 'rpc_init' in proto.mmcaps:
			self.rpc = await rpc_init(cfg, proto)
		if self.has_wallet:
			from .ctl import TwCtl
			self.twctl = await TwCtl(cfg, proto, mode='w', no_rpc=not have_rpc)
		self.amt_iwidth_keys = {'amt': 'iwidth'} | ({'amt2': 'iwidth2'} if self.has_amt2 else {})
		if repl_data := self.prompt_fs_repl.get(self.proto.coin):
			for repl in [repl_data] if isinstance(repl_data[0], int) else repl_data:
				self.prompt_fs_in[repl[0]] = repl[1]
		self.prompt_fs = '\n'.join(self.prompt_fs_in)
		for k, v in self.removed_key_mappings.items():
			if k in self.key_mappings and self.key_mappings[k] == v:
				del self.key_mappings[k]
			else:
				raise ValueError(f'{k}: {v}: unrecognized or invalid key mapping')
		self.key_mappings.update(self.extra_key_mappings)
		if self.proto.coin == 'BCH':
			self.key_mappings.update({'h': 'd_addr_view_pref'})
			self.addr_view_pref = 1 if not self.cfg.cashaddr else not self.proto.cashaddr

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
	def age_fmt(self, val):
		if val not in self.age_fmts:
			die('BadAgeFormat', f'{val!r}: invalid age format (must be one of {self.age_fmts!r})')
		self._age_fmt = val

	def age_disp(self, o, age_fmt):
		if self.has_age:
			match age_fmt:
				case 'confs':
					return o.confs or '-'
				case 'block':
					return self.rpc.blockcount + 1 - o.confs if o.confs else '-'
				case _:
					return self.date_formatter[age_fmt](self.rpc, o.date)

	def get_disp_prec(self, wide):
		return self.proto.coin_amt.max_prec

	sort_disp = {
		'addr':   'Addr',
		'age':    'Age',
		'amt':    'Amt',
		'txid':   'TxID',
		'twmmid': 'MMGenID'}

	sort_funcs = {
		'addr':   lambda i: i.addr,
		'age':    lambda i: 0 - i.confs,
		'amt':    lambda i: i.amt,
		'txid':   lambda i: f'{i.txid} {i.vout:04}',
		'twmmid': lambda i: i.twmmid.sort_key}

	def sort_info(self, *, include_group=True):
		ret = ([], ['Reverse'])[self.reverse]
		ret.append(self.sort_disp[self.sort_key])
		if include_group and self.group and self.sort_key in self.groupable:
			ret.append('Grouped')
		return ret

	def sort_data(self, key):
		if key == 'txid' and not self.txid_w:
			return
		if key not in self.sort_funcs:
			die(1, f'{key!r}: invalid sort key.  Valid options: {" ".join(self.sort_funcs)}')
		self.sort_key = key
		save = self.data.copy()
		self.data.sort(key=self.sort_funcs[key], reverse=self.reverse)
		if self.data != save:
			self.pos = 0

	async def get_data(self):

		rpc_data = await self.get_rpc_data()

		if not rpc_data:
			die(1, fmt(self.no_rpcdata_errmsg).strip())

		lbl_id = ('account', 'label')['label_api' in self.rpc.caps]

		self.data = MMGenList(
			await self.gen_data(rpc_data, lbl_id) if isAsync(self.gen_data) else
			self.gen_data(rpc_data, lbl_id))

		if not self.data:
			die(1, f'No {self.item_desc_pl} in tracking wallet!')

		self.sort_data(self.sort_key)

		self.disp_data = tuple(self.get_disp_data())

		# get_data() is immediately followed by display header, and get_rpc_data() produces output,
		# so add NL here (' ' required because CUR_HOME erases preceding blank lines)
		msg(' ')

	def get_term_dimensions(self, min_cols, *, min_lines=None):
		from ..term import get_terminal_size, get_char_raw, _term_dimensions
		user_resized = False
		while True:
			ts = get_terminal_size()
			cols = self.cfg.columns or ts.width
			lines = ts.height
			if cols >= min_cols and (min_lines is None or lines >= min_lines):
				if user_resized:
					msg_r(CUR_HOME + ERASE_ALL)
				return _term_dimensions(cols, ts.height)
			if sys.stdout.isatty():
				if self.cfg.columns and cols < min_cols:
					die(1, '\n'+fmt(
						self.twidth_diemsg.format(self.cfg.columns, self.desc, min_cols),
						indent = '  '))
				else:
					m, dim = (
						(self.twidth_errmsg, min_cols) if cols < min_cols else
						(self.theight_errmsg, min_lines))
					get_char_raw(CUR_HOME + ERASE_ALL + fmt(m.format(self.desc, dim), append=''))
					user_resized = True
			else:
				return _term_dimensions(min_cols, ts.height)

	def compute_column_widths(self, in_data, *, wide, interactive):

		def do_ret(freews):
			if freews:
				widths.update({k: minws[k] + freews.get(k, 0) for k in minws})
			else:
				widths.update({k: max(minws[k], maxws[k]) for k in minws})
			widths.update({
				ikey: widths[key] - self.disp_prec - 1
					for key, ikey in self.amt_iwidth_keys.items()})
			return namedtuple('column_widths', widths.keys())(*widths.values())

		def get_freews(cols, varws, varw, minw):
			freew = cols - minw
			if freew and varw:
				x = freew / varw
				freews = {k: int(varws[k] * x) for k in varws}
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

		widths, maxws, minws, maxws_nice = in_data
		varws = {k: maxws[k] - minws[k] for k in maxws if maxws[k] > minws[k]}
		minw = sum(widths.values()) + sum(minws.values())
		varw = sum(varws.values())

		self.min_term_width = 40 if wide else max(self.prompt_width, minw) if interactive else minw
		td = self.get_term_dimensions(self.min_term_width)
		self.term_height = td.height
		self.term_width = td.width

		self.cols = min(self.term_width, minw + varw)

		if wide or self.cols == minw + varw:
			return do_ret(None)

		if maxws_nice:
			# compute high-priority widths:
			varws_hp = {k: maxws_nice[k] - minws[k] if k in maxws_nice else varws[k] for k in varws}
			varw_hp = sum(varws_hp.values())
			widths_hp = get_freews(
				min(self.term_width, minw + varw_hp),
				varws_hp,
				varw_hp,
				minw)
			# compute low-priority (nice) widths:
			varws_lp = {k: varws[k] - varws_hp[k] for k in maxws_nice if k in varws}
			widths_lp = get_freews(
				self.cols,
				varws_lp,
				sum(varws_lp.values()),
				minw + sum(widths_hp.values()))
			# sum the two for each field:
			return do_ret({k: widths_hp[k] + widths_lp.get(k, 0) for k in varws})
		else:
			return do_ret(get_freews(self.cols, varws, varw, minw))

	def gen_subheader(self, cw, color):
		c_orange = (nocolor, orange)[color]
		c_yellow = (nocolor, yellow)[color]
		if self.rpc.is_remote:
			yield (
				c_orange(f'WARNING: Connecting to public {self.rpc.server_proto} node at ') +
				self.rpc.server_domain.hl(color=color))
			yield c_orange('         To improve anonymity, proxy requests via Tor or I2P')
		if self.twctl.use_cached_balances:
			yield c_yellow('Using cached balances. These may be out of date!')
		else:
			yield f'Displaying balances with {self.minconf} confirmation{suf(self.minconf)}'

	def gen_footer(self, color):
		if hasattr(self, 'total'):
			yield 'TOTAL: {} {}'.format(self.total.hl(color=color), self.proto.dcoin)

	def set_amt_widths(self, data):
		# width of amts column: min(7, width of integer part) + len('.') + width of fractional part
		self.amt_widths = {
			k: min(7, max(len(str(getattr(d, k).to_integral_value()))
				for d in data)) + 1 + self.disp_prec
					for k in self.amt_iwidth_keys}

	async def format(
			self,
			display_type,
			*,
			color           = True,
			interactive     = False,
			line_processing = None,
			scroll          = False):

		def make_display():

			def gen_hdr(spc):

				if color:
					Blue, Green = (blue, green)
					Yes, No, Only = (green('yes'), red('no'), yellow('only'))
				else:
					Blue, Green = (nocolor, nocolor)
					Yes, No, Only = ('yes', 'no', 'only')

				sort_info = ' '.join(self.sort_info())

				def fmt_filter(k):
					return '{}:{}'.format(k, {0: No, 1: Yes, 2: Only}[getattr(self, k)])

				yield '{} (sort order: {}){}'.format(
					self.hdr_lbl.upper(),
					Blue(sort_info),
					spc * (self.cols - len(f'{self.hdr_lbl} (sort order: {sort_info})')))

				if hasattr(self, 'sid'):
					yield f'Seed ID: {self.sid.hl(color=color)}'

				if self.filters:
					yield 'Filters: {}{}'.format(
						' '.join(map(fmt_filter, self.filters)),
						spc * len(self.filters))

				yield 'Network: {}'.format(Green(
					self.proto.coin + ' ' + self.proto.chain_name.upper()))

				if hasattr(self.rpc, 'blockcount'):
					yield 'Block {} [{}]'.format(
						self.rpc.blockcount.hl(color=color),
						make_timestr(self.rpc.cur_date))

				if hasattr(self, 'total'):
					if hasattr(self, 'unlocked_total') and self.total != self.unlocked_total:
						yield 'Total {}: {} {}'.format(
							self.proto.dcoin,
							self.unlocked_total.hl(color=color),
							self.total.hl3(color_override='orange', encl='[]'))
					else:
						yield 'Total {}: {}'.format(self.proto.dcoin, self.total.hl(color=color))

				yield from getattr(self, dt.subhdr_fmt_method)(cw, color)

				yield spc * self.term_width

				if self.disp_data and dt.colhdr_fmt_method:
					col_hdr = getattr(self, dt.colhdr_fmt_method)(cw, hdr_fs, color)
					yield col_hdr.rstrip() if line_processing == 'print' else col_hdr

			def get_body(method):
				if line_processing:
					return getattr(self.line_processing, line_processing).do(
						method, self.disp_data, cw, fs, color, getattr(self, dt.line_fmt_method))
				else:
					return method(self.disp_data, cw, fs, color, getattr(self, dt.line_fmt_method))

			if self.disp_data and dt.need_column_widths:
				self.set_amt_widths(self.disp_data)
				cw = self.compute_column_widths(
					self.get_column_widths(self.disp_data, wide=dt.detail),
					wide = dt.detail,
					interactive = interactive)
				cwh = cw._asdict()
				fp = self.fs_params
				rfill = ' ' * (self.term_width - self.cols) if scroll else ''
				hdr_fs = ''.join(fp[name].hdr_fs % ((), cwh[name])[fp[name].hdr_fs_repl]
					for name in dt.cols if cwh[name]) + rfill
				fs = ''.join(fp[name].fs % ((), cwh[name])[fp[name].fs_repl]
					for name in dt.cols if cwh[name]) + rfill
			else:
				cw = hdr_fs = fs = None

			return (
				tuple(gen_hdr(spc='' if line_processing == 'print' else ' ')),
				tuple(
					get_body(getattr(self, dt.fmt_method)) if self.disp_data else
					[(nocolor, yellow)[color](self.nodata_msg.ljust(self.term_width))]))

		if not gv.stdout.isatty():
			line_processing = 'print'

		dt = getattr(self.display_type, display_type)

		if self.use_cached:
			self.use_cached = False
			display_hdr = self.display_hdr
			display_body = self.display_body
		else:
			self.disp_prec = self.get_disp_prec(wide=dt.detail)

			if self.has_age and (self.age_fmt in self.age_fmts_date_dependent or dt.detail):
				await self.set_dates(self.data)

			disp_data_save = self.disp_data
			self.disp_data = tuple(self.get_disp_data()) # method could be a generator

			if self.disp_data != disp_data_save:
				self.pos = 0

			display_hdr, display_body = make_display()

			if scroll:
				fixed_height = len(display_hdr) + self.prompt_height + 1

				if self.term_height - fixed_height < self.min_scrollable_height:
					td = self.get_term_dimensions(
						self.min_term_width,
						min_lines = self.min_scrollable_height + fixed_height)
					self.term_height = td.height
					self.term_width = td.width
					display_hdr, display_body = make_display()

				self.scrollable_height = self.term_height - fixed_height
				self.max_pos = max(0, len(display_body) - self.scrollable_height)
				self.pos = min(self.pos, self.max_pos)

			if not dt.detail:
				self.display_hdr = display_hdr
				self.display_body = display_body

		if scroll:
			top = self.pos
			bot = self.pos + self.scrollable_height
			fill = ('\n' + ''.ljust(self.term_width)) * (self.scrollable_height - len(display_body))
		else:
			top, bot, fill = (None, None, '')

		if interactive:
			footer = ''
		else:
			footer = '\n'.join(self.gen_footer(color))
			footer = ('\n\n' + footer if footer else '') + '\n'

		return (
			'\n'.join(display_hdr) + '\n'
			+ dt.item_separator.join(display_body[top:bot])
			+ fill
			+ footer)

	async def view_filter_and_sort(self):

		action_map = {
			'a_': 'action',
			's_': 'sort_action',
			'd_': 'display_action',
			'm_': 'scroll_action',
			'i_': 'item_action'}

		def make_key_mappings(scroll):
			if scroll:
				for k in self.scroll_keys['vi']:
					assert k not in self.key_mappings, f'{k!r} is in key_mappings'
				self.key_mappings.update(self.scroll_keys['vi'])
				self.key_mappings.update(self.scroll_keys[sys.platform])
			return self.key_mappings

		scroll = self.scroll = self.cfg.scroll

		key_mappings = make_key_mappings(scroll)
		action_classes = {k: getattr(self, action_map[v[:2]])() for k, v in key_mappings.items()}
		action_methods = {k: getattr(v, key_mappings[k]) for k, v in action_classes.items()}
		prompt = self.prompt_fs.strip().format(
			s='\nScrolling: k=up, j=down, b=pgup, f=pgdown, g=top, G=bottom' if scroll else '')

		self.prompt_width = max(len(l) for l in prompt.split('\n'))
		self.prompt_height = len(prompt.split('\n'))
		self.oneshot_msg = ''
		prompt += '\b'

		clear_screen = '\n\n' if self.cfg.no_blank else CUR_HOME + ('' if scroll else ERASE_ALL)

		from ..term import get_term, get_char, get_char_raw

		if scroll:
			self.term = get_term()
			self.term.register_cleanup()
			self.term.set('noecho')
			get_char = get_char_raw
			msg_r(CUR_HOME + ERASE_ALL)

		while True:

			if self.oneshot_msg and scroll:
				msg_r(self.blank_prompt + self.oneshot_msg + ' ') # oneshot_msg must be a one-liner
				await asyncio.sleep(2)
				msg_r('\r' + ''.ljust(self.term_width))

			reply = get_char(
				clear_screen
				+ await self.format('squeezed', interactive=True, scroll=scroll)
				+ '\n\n'
				+ (self.oneshot_msg + '\n\n' if self.oneshot_msg and not scroll else '')
				+ prompt,
				immed_chars = key_mappings)

			self.oneshot_msg = ''

			match reply:
				case ch if ch in key_mappings:
					func = action_classes[ch].run
					arg = action_methods[ch]
					await func(self, arg) if isAsync(func) else func(self, arg)
				case 'q':
					msg('')
					if self.scroll:
						self.term.set('echo')
					return
				case _:
					if not scroll:
						msg_r('\ninvalid keypress ')
					await asyncio.sleep(0.3)

	@property
	def blank_prompt(self):
		return CUR_HOME + CUR_DOWN(self.term_height - self.prompt_height) + ERASE_ALL

	def keypress_confirm(self, *args, **kwargs):
		from ..ui import keypress_confirm
		if keypress_confirm(self.cfg, *args, no_nl=self.scroll, **kwargs):
			return True
		else:
			if self.scroll:
				msg_r('\r'+''.ljust(self.term_width)+'\r'+yellow('Canceling! '))
			return False

	async def get_idx_from_user(self):
		return await self.get_idx(f'{self.item_desc} number', self.disp_data)

	async def get_idx(self, desc, data, *, is_addr_idx=False):

		async def do_error_msg():
			msg_r(
				'Choice must be a single number between {n} and {m} inclusive{s}'.format(
					n = list(data.keys())[0] if is_addr_idx else 1,
					m = list(data.keys())[-1] if is_addr_idx else len(data),
					s = ' ' if self.scroll else ''))
			if self.scroll:
				await asyncio.sleep(1.5)
				msg_r(CUR_UP(1) + '\r' + ERASE_ALL)

		from ..ui import line_input
		ur = namedtuple('usr_idx_data', ['idx', 'acct_addr_idx'])
		while True:
			msg_r(self.blank_prompt if self.scroll else '\n')
			usr_ret = line_input(
				self.cfg,
				f'Enter {desc} (or ENTER to return to main menu): ')
			if usr_ret == '':
				if self.scroll:
					msg_r(CUR_UP(1) + '\r' + ''.ljust(self.term_width))
				return None
			if is_addr_idx:
				if is_int(usr_ret) and int(usr_ret) in data:
					return ur(MMGenIdx(data[int(usr_ret)].disp_data_idx + 1), int(usr_ret))
			else:
				idx = get_obj(MMGenIdx, n=usr_ret, silent=True)
				if idx and idx <= len(data):
					return ur(idx, None)
			await do_error_msg()

	class action:

		@enable_echo
		async def run(self, parent, action_method):
			return await action_method(parent)

		async def a_print_detail(self, parent):
			return await self._print(parent, output_type='detail')

		async def a_print_squeezed(self, parent):
			return await self._print(parent, output_type='squeezed')

		async def _print(self, parent, output_type):

			if not parent.disp_data:
				return None

			outfile = '{a}{b}-{c}{d}[{e}].out'.format(
				a = parent.dump_fn_pfx,
				b = f'-{output_type}' if len(parent.print_output_types) > 1 else '',
				c = parent.proto.dcoin,
				d = ('' if parent.proto.network == 'mainnet' else '-'+parent.proto.network.upper()),
				e = ','.join(parent.sort_info(include_group=False)).replace(' ', ''))

			print_hdr = getattr(parent.display_type, output_type).print_header.format(parent.cols)

			msg_r(parent.blank_prompt if parent.scroll else '\n')

			from ..fileutil import write_data_to_file
			from ..exception import UserNonConfirmation
			try:
				write_data_to_file(
					cfg     = parent.cfg,
					outfile = outfile,
					data    = print_hdr + await parent.format(
						display_type    = output_type,
						line_processing = 'print',
						color           = False),
					desc    = f'{parent.desc} listing')
			except UserNonConfirmation:
				parent.oneshot_msg = yellow(f'File {outfile!r} not overwritten by user request')
			else:
				parent.oneshot_msg = green(f'Data written to {outfile!r}')

		async def a_view(self, parent):
			from ..ui import do_pager
			parent.use_cached = True
			msg_r(CUR_HOME)
			do_pager(await parent.format('squeezed', color=True))

		async def a_view_detail(self, parent):
			from ..ui import do_pager
			msg_r(CUR_HOME)
			do_pager(await parent.format('detail', color=True))

	class item_action:

		@enable_echo
		async def run(self, parent, action_method):

			if not parent.disp_data:
				return

			while True:
				# action_method return values:
				#  True:   action successfully performed
				#  False:  an error occurred
				#  None:   action aborted by user or no action performed
				#  'redo': user will be re-prompted for item number
				#  'redraw': action successfully performed, screen will be redrawn
				if usr_ret := await parent.get_idx_from_user():
					ret = await action_method(parent, usr_ret.idx, usr_ret.acct_addr_idx)
				else:
					ret = None
				if ret != 'redo':
					break
				await asyncio.sleep(0.5)

			if parent.scroll and (ret is False or ret == 'redraw'):
				# error messages could leave screen in messy state, so do complete redraw:
				msg_r(
					CUR_HOME + ERASE_ALL +
					await parent.format(display_type='squeezed', interactive=True, scroll=True))

		async def i_balance_refresh(self, parent, idx, acct_addr_idx=None):
			if not parent.keypress_confirm(
					f'Refreshing tracking wallet {parent.item_desc} #{idx}. OK?'):
				return 'redo'
			msg_r('Refreshing balance...')
			res = await parent.twctl.get_balance(parent.disp_data[idx-1].addr, force_rpc=True)
			if res is None:
				parent.oneshot_msg = red(
					f'Unable to refresh {parent.proto.dcoin} balance for {parent.item_desc} #{idx}')
				return False
			else:
				await parent.get_data()
				parent.oneshot_msg = yellow(
					f'{parent.proto.dcoin} balance for {parent.item_desc} #{idx} refreshed')
				if res == 0:
					return 'redraw' # zeroing balance may mess up display

		async def i_addr_delete(self, parent, idx, acct_addr_idx=None):
			if not parent.keypress_confirm(
					'Removing {} {} from tracking wallet. OK?'.format(
						parent.item_desc, red(f'#{idx}'))):
				return 'redo'
			if await parent.twctl.remove_address(parent.disp_data[idx-1].addr):
				await parent.get_data()
				parent.oneshot_msg = yellow(f'{capfirst(parent.item_desc)} #{idx} removed')
				return True
			else:
				await asyncio.sleep(3)
				parent.oneshot_msg = red('Address could not be removed')
				return False

		async def i_comment_add(self, parent, idx, acct_addr_idx=None):

			async def do_comment_add(comment_in):
				from ..obj import TwComment
				new_comment = await parent.twctl.set_comment(
					addrspec     = None,
					comment      = comment_in,
					trusted_pair = (entry.twmmid, entry.addr),
					silent       = parent.scroll)

				edited = old_comment and new_comment
				if isinstance(new_comment, TwComment):
					entry.comment = new_comment
					parent.oneshot_msg = (green if new_comment else yellow)('Label {a} {b}{c}'.format(
						a = 'for' if edited else 'added to' if new_comment else 'removed from',
						b = desc,
						c = ' edited' if edited else ''))
					return 'redraw' if parent.cfg.coin == 'XMR' else True
				else:
					await asyncio.sleep(3)
					parent.oneshot_msg = red('Label for {desc} could not be {action}'.format(
						desc = desc,
						action = 'edited' if edited else 'added' if new_comment else 'removed'))
					return False

			if acct_addr_idx is None:
				desc       = f'{parent.item_desc} #{idx}'
				color_desc = f'{parent.item_desc} {red("#" + str(idx))}'
			else:
				desc       = f'address #{acct_addr_idx}'
				color_desc = f'address {red("#" + str(acct_addr_idx))}'

			entry = parent.disp_data[idx-1]
			old_comment = entry.comment
			msg('Current label: {}'.format(old_comment.hl() if old_comment else '(none)'))

			from ..ui import line_input
			match res:= line_input(
					parent.cfg,
					f'Enter label text for {color_desc}: ',
					insert_txt = old_comment):
				case s if s == old_comment:
					parent.oneshot_msg = yellow(f'Label for {desc} unchanged')
					return None
				case '':
					if not parent.keypress_confirm(f'Removing label for {color_desc}. OK?'):
						return 'redo'

			return await do_comment_add(res)

	class scroll_action:

		def run(self, parent, action_method):
			self.use_cached = True
			return action_method(parent)

		def m_cursor_up(self, parent):
			parent.pos -= min(parent.pos - 0, 1)

		def m_cursor_down(self, parent):
			parent.pos += min(parent.max_pos - parent.pos, 1)

		def m_pg_up(self, parent):
			parent.pos -= min(parent.scrollable_height, parent.pos - 0)

		def m_pg_down(self, parent):
			parent.pos += min(parent.scrollable_height, parent.max_pos - parent.pos)

		def m_top(self, parent):
			parent.pos = 0

		def m_bot(self, parent):
			parent.pos = parent.max_pos

	class sort_action:

		def run(self, parent, action_method):
			return action_method(parent)

		def s_addr(self, parent):
			parent.sort_data('addr')

		def s_age(self, parent):
			parent.sort_data('age')

		def s_amt(self, parent):
			parent.sort_data('amt')

		def s_txid(self, parent):
			parent.sort_data('txid')

		def s_twmmid(self, parent):
			parent.sort_data('twmmid')

		def s_reverse(self, parent):
			parent.data.reverse()
			parent.reverse = not parent.reverse

	class display_action:

		def run(self, parent, action_method):
			return action_method(parent)

		def d_days(self, parent):
			af = parent.age_fmts
			parent.age_fmt = af[(af.index(parent.age_fmt) + 1) % len(af)]
			if parent.update_widths_on_age_toggle: # TODO
				pass

		def d_redraw(self, parent):
			msg_r(CUR_HOME + ERASE_ALL)

		def d_addr_view_pref(self, parent):
			parent.addr_view_pref = (parent.addr_view_pref + 1) % len(parent.bch_addr_fmts)
