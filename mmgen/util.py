#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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
util: Frequently-used variables, classes and utility functions for the MMGen suite
"""

import sys, os, time, re

from .color import red, yellow, green, blue, purple
from .cfg import gv

ascii_lowercase = 'abcdefghijklmnopqrstuvwxyz'

digits = '0123456789'
hexdigits = '0123456789abcdefABCDEF'
hexdigits_uc = '0123456789ABCDEF'
hexdigits_lc = '0123456789abcdef'

def noop(*args, **kwargs):
	pass

class Util:

	def __init__(self, cfg):

		self.cfg = cfg

		if cfg.quiet:
			self.qmsg = self.qmsg_r = noop
		else:
			self.qmsg = msg
			self.qmsg_r = msg_r

		if cfg.verbose:
			self.vmsg = msg
			self.vmsg_r = msg_r
			self.Vmsg = Msg
			self.Vmsg_r = Msg_r
		else:
			self.vmsg = self.vmsg_r = self.Vmsg = self.Vmsg_r = noop

		self.dmsg = msg if cfg.debug else noop

		if cfg.pager:
			from .ui import do_pager
			self.stdout_or_pager = do_pager
		else:
			self.stdout_or_pager = Msg_r

	def compare_chksums(
			self,
			chk1,
			desc1,
			chk2,
			desc2,
			hdr         = '',
			die_on_fail = False,
			verbose     = False):

		if not chk1 == chk2:
			fs = "{} ERROR: {} checksum ({}) doesn't match {} checksum ({})"
			m = fs.format((hdr+':\n   ' if hdr else 'CHECKSUM'), desc2, chk2, desc1, chk1)
			if die_on_fail:
				die(3, m)
			else:
				if verbose or self.cfg.verbose:
					msg(m)
				return False

		if self.cfg.verbose:
			msg(f'{capfirst(desc1)} checksum OK ({chk1})')

		return True

	def compare_or_die(self, val1, desc1, val2, desc2, e='Error'):
		if val1 != val2:
			die(3, f"{e}: {desc2} ({val2}) doesn't match {desc1} ({val1})")
		if self.cfg.debug:
			msg(f'{capfirst(desc2)} OK ({val2})')
		return True

if sys.platform == 'win32':
	def msg_r(s):
		try:
			gv.stderr.write(s)
			gv.stderr.flush()
		except:
			os.write(2, s.encode())

	def msg(s):
		msg_r(s + '\n')

	def Msg_r(s):
		try:
			gv.stdout.write(s)
			gv.stdout.flush()
		except:
			os.write(1, s.encode())

	def Msg(s):
		Msg_r(s + '\n')
else:
	def msg(s):
		gv.stderr.write(s + '\n')

	def msg_r(s):
		gv.stderr.write(s)
		gv.stderr.flush()

	def Msg(s):
		gv.stdout.write(s + '\n')

	def Msg_r(s):
		gv.stdout.write(s)
		gv.stdout.flush()

def rmsg(s):
	msg(red(s))

def ymsg(s):
	msg(yellow(s))

def gmsg(s):
	msg(green(s))

def gmsg_r(s):
	msg_r(green(s))

def bmsg(s):
	msg(blue(s))

def pumsg(s):
	msg(purple(s))

def mmsg(*args):
	for d in args:
		Msg(repr(d))

def mdie(*args):
	mmsg(*args)
	sys.exit(0)

def die(ev, s='', stdout=False):
	if isinstance(ev, int):
		from .exception import MMGenSystemExit, MMGenError
		if ev <= 2:
			raise MMGenSystemExit(ev, s, stdout)
		else:
			raise MMGenError(ev, s, stdout)
	elif isinstance(ev, str):
		from . import exception
		raise getattr(exception, ev)(s)
	else:
		raise ValueError(f'{ev}: exit value must be string or int instance')

def Die(ev=0, s=''):
	die(ev=ev, s=s, stdout=True)

def pp_fmt(d):
	import pprint
	return pprint.PrettyPrinter(indent=4, compact=False).pformat(d)

def pp_msg(d):
	msg(pp_fmt(d))

def indent(s, indent='    ', append='\n'):
	"indent multiple lines of text with specified string"
	return indent + ('\n'+indent).join(s.strip().splitlines()) + append

def fmt(s, indent='', strip_char=None, append='\n'):
	"de-indent multiple lines of text, or indent with specified string"
	return indent + ('\n'+indent).join([l.lstrip(strip_char) for l in s.strip().splitlines()]) + append

def fmt_list(iterable, fmt='dfl', indent='', conv=None):
	"pretty-format a list"
	_conv, sep, lq, rq = {
		'dfl':       (str,  ", ", "'",  "'"),
		'utf8':      (str,  ", ", "“",  "”"),
		'bare':      (repr, " ",  "",   ""),
		'barest':    (str,  " ",  "",   ""),
		'fancy':     (str,  " ",  "‘",  "’"),
		'no_quotes': (str,  ", ", "",   ""),
		'compact':   (str,  ",",  "",   ""),
		'no_spc':    (str,  ",",  "'",  "'"),
		'min':       (str,  ",",  "",   ""),
		'repr':      (repr, ", ", "",   ""),
		'csv':       (repr, ",",  "",   ""),
		'col':       (str,  "\n", "",   ""),
	}[fmt]
	conv = conv or _conv
	return indent + (sep+indent).join(lq+conv(e)+rq for e in iterable)

def fmt_dict(mapping, fmt='dfl', kconv=None, vconv=None):
	"pretty-format a dict"
	kc, vc, sep, fs = {
		'dfl':           (str, str,  ", ",  "'{}' ({})"),
		'dfl_compact':   (str, str,  " ",   "{} ({})"),
		'square':        (str, str,  ", ",  "'{}' [{}]"),
		'square_compact':(str, str,  " ",   "{} [{}]"),
		'equal':         (str, str,  ", ",  "'{}'={}"),
		'equal_spaced':  (str, str,  ", ",  "'{}' = {}"),
		'equal_compact': (str, str,  " ",   "{}={}"),
		'kwargs':        (str, repr, ", ",  "{}={}"),
		'colon':         (str, repr, ", ",  "{}:{}"),
		'colon_compact': (str, str,  " ",   "{}:{}"),
	}[fmt]
	kconv = kconv or kc
	vconv = vconv or vc
	return sep.join(fs.format(kconv(k), vconv(v)) for k, v in mapping.items())

def list_gen(*data):
	"""
	Generate a list from an arg tuple of sublists
	- The last element of each sublist is a condition.  If it evaluates to true, the preceding
	  elements of the sublist are included in the result.  Otherwise the sublist is skipped.
	- If a sublist contains only one element, the condition defaults to true.
	"""
	assert type(data) in (list, tuple), f'{type(data).__name__} not in (list, tuple)'
	def gen():
		for d in data:
			assert isinstance(d, list), f'{type(d).__name__} != list'
			if len(d) == 1:
				yield d[0]
			elif d[-1]:
				for idx in range(len(d)-1):
					yield d[idx]
	return list(gen())

def remove_dups(iterable, edesc='element', desc='list', quiet=False, hide=False):
	"""
	Remove duplicate occurrences of iterable elements, preserving first occurrence
	If iterable is a generator, return a list, else type(iterable)
	"""
	ret = []
	for e in iterable:
		if e in ret:
			if not quiet:
				ymsg(f'Warning: removing duplicate {edesc} {"(hidden)" if hide else e} in {desc}')
		else:
			ret.append(e)
	return ret if type(iterable).__name__ == 'generator' else type(iterable)(ret)

def contains_any(target_list, source_list):
	return any(map(target_list.count, source_list))

def suf(arg, suf_type='s', verb='none'):
	suf_types = {
		'none': {
			's':   ('s',   ''),
			'es':  ('es',  ''),
			'ies': ('ies', 'y'),
		},
		'is': {
			's':   ('s are',   ' is'),
			'es':  ('es are',  ' is'),
			'ies': ('ies are', 'y is'),
		},
		'has': {
			's':   ('s have',   ' has'),
			'es':  ('es have',  ' has'),
			'ies': ('ies have', 'y has'),
		},
	}
	if isinstance(arg, int):
		n = arg
	elif isinstance(arg, (list, tuple, set, dict)):
		n = len(arg)
	else:
		die(2, f'{arg}: invalid parameter for suf()')
	return suf_types[verb][suf_type][n == 1]

def get_extension(fn):
	return os.path.splitext(fn)[1][1:]

def remove_extension(fn, ext):
	a, b = os.path.splitext(fn)
	return a if b[1:] == ext else fn

def make_chksum_N(s, nchars, sep=False, rounds=2, upper=True):
	if isinstance(s, str):
		s = s.encode()
	from hashlib import sha256
	for i in range(rounds):
		s = sha256(s).digest()
	ret = s.hex()[:nchars]
	if sep:
		assert 4 <= nchars <= 64 and (not nchars % 4), 'illegal ‘nchars’ value'
		ret = ' '.join(ret[i:i+4] for i in range(0, nchars, 4))
	else:
		assert 4 <= nchars <= 64, 'illegal ‘nchars’ value'
	return ret.upper() if upper else ret

def make_chksum_8(s, sep=False):
	from .obj import HexStr
	from hashlib import sha256
	s = HexStr(sha256(sha256(s).digest()).hexdigest()[:8].upper(), case='upper')
	return '{} {}'.format(s[:4], s[4:]) if sep else s

def make_chksum_6(s):
	from .obj import HexStr
	from hashlib import sha256
	if isinstance(s, str):
		s = s.encode()
	return HexStr(sha256(s).hexdigest()[:6])

def is_chksum_6(s):
	return len(s) == 6 and set(s) <= set(hexdigits_lc)

def split_into_cols(col_wid, s):
	return ' '.join([s[col_wid*i:col_wid*(i+1)] for i in range(len(s)//col_wid+1)]).rstrip()

def capfirst(s): # different from str.capitalize() - doesn't downcase any uc in string
	return s if len(s) == 0 else s[0].upper() + s[1:]

def decode_timestamp(s):
#	tz_save = open('/etc/timezone').read().rstrip()
	os.environ['TZ'] = 'UTC'
#	os.environ['TZ'] = tz_save
	return int(time.mktime(time.strptime(s, '%Y%m%d_%H%M%S')))

def make_timestamp(secs=None):
	return '{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}'.format(*time.gmtime(
		int(secs) if secs is not None else time.time())[:6])

def make_timestr(secs=None):
	return '{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(*time.gmtime(
		int(secs) if secs is not None else time.time())[:6])

def secs_to_dhms(secs):
	hrs = secs // 3600
	return '{}{:02d}:{:02d}:{:02d} h/m/s'.format(
		('{} day{}, '.format(hrs//24, suf(hrs//24)) if hrs > 24 else ''),
		hrs % 24,
		(secs // 60) % 60,
		secs % 60
	)

def secs_to_hms(secs):
	return '{:02d}:{:02d}:{:02d}'.format(secs//3600, (secs//60) % 60, secs % 60)

def secs_to_ms(secs):
	return '{:02d}:{:02d}'.format(secs//60, secs % 60)

def is_int(s): # actually is_nonnegative_int()
	return set(str(s)) <= set(digits)

def check_int_between(val, imin, imax, desc):
	if not imin <= int(val) <= imax:
		die(1, f'{val}: invalid value for {desc} (must be between {imin} and {imax})')
	return int(val)

def is_hex_str(s):
	return set(s) <= set(hexdigits)

def is_hex_str_lc(s):
	return set(s) <= set(hexdigits_lc)

def is_utf8(s):
	try:
		s.decode('utf8')
	except:
		return False
	else:
		return True

def remove_whitespace(s, ws='\t\r\n '):
	return s.translate(dict((ord(e), None) for e in ws))

def strip_comment(line):
	return re.sub('#.*', '', line).rstrip()

def strip_comments(lines):
	pat = re.compile('#.*')
	return [m for m in [pat.sub('', l).rstrip() for l in lines] if m != '']

def make_full_path(outdir, outfile):
	return os.path.normpath(os.path.join(outdir, os.path.basename(outfile)))

class oneshot_warning:

	color = 'nocolor'

	def __init__(self, div=None, fmt_args=[], reverse=False):
		self.do(type(self), div, fmt_args, reverse)

	def do(self, wcls, div, fmt_args, reverse):

		def do_warning():
			from . import color
			msg(getattr(color, getattr(wcls, 'color'))('WARNING: ' + getattr(wcls, 'message').format(*fmt_args)))

		if not hasattr(wcls, 'data'):
			setattr(wcls, 'data', [])

		data = getattr(wcls, 'data')
		condition = (div in data) if reverse else (not div in data)

		if not div in data:
			data.append(div)

		if condition:
			do_warning()
			self.warning_shown = True
		else:
			self.warning_shown = False

class oneshot_warning_group(oneshot_warning):

	def __init__(self, wcls, div=None, fmt_args=[], reverse=False):
		self.do(getattr(self, wcls), div, fmt_args, reverse)

def get_subclasses(cls, names=False):
	def gen(cls):
		for i in cls.__subclasses__():
			yield i
			yield from gen(i)
	return tuple((c.__name__ for c in gen(cls)) if names else gen(cls))

def async_run(coro):
	import asyncio
	return asyncio.run(coro)

def wrap_ripemd160(called=[]):
	if not called:
		try:
			import hashlib
			hashlib.new('ripemd160')
		except ValueError:
			def hashlib_new_wrapper(name, *args, **kwargs):
				if name == 'ripemd160':
					return ripemd160(*args, **kwargs)
				else:
					return hashlib_new(name, *args, **kwargs)
			from .contrib.ripemd160 import ripemd160
			hashlib_new = hashlib.new
			hashlib.new = hashlib_new_wrapper
		called.append(True)

def exit_if_mswin(feature):
	if sys.platform == 'win32':
		die(2, capfirst(feature) + ' not supported on the MSWin / MSYS2 platform')

def have_sudo(silent=False):
	from subprocess import run, DEVNULL
	redir = DEVNULL if silent else None
	try:
		run(['sudo', '--non-interactive', 'true'], stdout=redir, stderr=redir, check=True)
		return True
	except:
		return False
