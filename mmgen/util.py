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
util: Frequently-used variables, classes and utility functions for the MMGen suite
"""

import sys,os,time,re

from .color import *
from .globalvars import g
from .opts import opt

ascii_lowercase = 'abcdefghijklmnopqrstuvwxyz'

hexdigits = '0123456789abcdefABCDEF'
hexdigits_uc = '0123456789ABCDEF'
hexdigits_lc = '0123456789abcdef'

if g.platform == 'win':
	def msg_r(s):
		try:
			g.stderr.write(s)
			g.stderr.flush()
		except:
			os.write(2,s.encode())

	def msg(s):
		msg_r(s + '\n')

	def Msg_r(s):
		try:
			g.stdout.write(s)
			g.stdout.flush()
		except:
			os.write(1,s.encode())

	def Msg(s):
		Msg_r(s + '\n')
else:
	def msg(s):
		g.stderr.write(s + '\n')

	def msg_r(s):
		g.stderr.write(s)
		g.stderr.flush()

	def Msg(s):
		g.stdout.write(s + '\n')

	def Msg_r(s):
		g.stdout.write(s)
		g.stdout.flush()

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

def qmsg(s):
	if not opt.quiet:
		msg(s)

def qmsg_r(s):
	if not opt.quiet:
		msg_r(s)

def vmsg(s,force=False):
	if opt.verbose or force:
		msg(s)

def vmsg_r(s,force=False):
	if opt.verbose or force:
		msg_r(s)

def Vmsg(s,force=False):
	if opt.verbose or force:
		Msg(s)

def Vmsg_r(s,force=False):
	if opt.verbose or force:
		Msg_r(s)

def dmsg(s):
	if opt.debug:
		msg(s)

def mmsg(*args):
	for d in args:
		Msg(repr(d))

def mdie(*args):
	mmsg(*args)
	sys.exit(0)

def die(ev,s='',stdout=False):
	if isinstance(ev,int):
		from .exception import MMGenSystemExit,MMGenError
		if ev <= 2:
			raise MMGenSystemExit(ev,s,stdout)
		else:
			raise MMGenError(ev,s,stdout)
	elif isinstance(ev,str):
		import mmgen.exception
		raise getattr(mmgen.exception,ev)(s)
	else:
		raise ValueError(f'{ev}: exit value must be string or int instance')

def Die(ev=0,s=''):
	die(ev=ev,s=s,stdout=True)

def pp_fmt(d):
	import pprint
	return pprint.PrettyPrinter(indent=4,compact=False).pformat(d)

def pp_msg(d):
	msg(pp_fmt(d))

def fmt(s,indent='',strip_char=None,append='\n'):
	"de-indent multiple lines of text, or indent with specified string"
	return indent + ('\n'+indent).join([l.strip(strip_char) for l in s.strip().splitlines()]) + append

def fmt_list(iterable,fmt='dfl',indent=''):
	"pretty-format a list"
	sep,lq,rq = {
		'utf8':      ("“, ”",      "“",    "”"),
		'dfl':       ("', '",      "'",    "'"),
		'bare':      (' ',         '',     '' ),
		'no_quotes': (', ',        '',     '' ),
		'no_spc':    ("','",       "'",    "'"),
		'min':       (",",         "'",    "'"),
		'col':       ('\n'+indent, indent, '' ),
	}[fmt]
	return lq + sep.join(str(i) for i in iterable) + rq

def list_gen(*data):
	"""
	add element to list if condition is true or absent
	"""
	assert type(data) in (list,tuple), f'{type(data).__name__} not in (list,tuple)'
	def gen():
		for i in data:
			assert type(i) == list, f'{type(i).__name__} != list'
			assert len(i) in (1,2), f'{len(i)} not in (1,2)'
			if len(i) == 1 or i[1]:
				yield i[0]
	return list(gen())

def remove_dups(iterable,edesc='element',desc='list',quiet=False,hide=False):
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

def suf(arg,suf_type='s',verb='none'):
	suf_types = {
		'none': {
			's':   ('s',  ''),
			'es':  ('es', ''),
			'ies': ('ies','y'),
		},
		'is': {
			's':   ('s are',  ' is'),
			'es':  ('es are', ' is'),
			'ies': ('ies are','y is'),
		},
		'has': {
			's':   ('s have',  ' has'),
			'es':  ('es have', ' has'),
			'ies': ('ies have','y has'),
		},
	}
	if isinstance(arg,int):
		n = arg
	elif isinstance(arg,(list,tuple,set,dict)):
		n = len(arg)
	else:
		die(2,f'{arg}: invalid parameter for suf()')
	return suf_types[verb][suf_type][n == 1]

def get_extension(fn):
	return os.path.splitext(fn)[1][1:]

def remove_extension(fn,ext):
	a,b = os.path.splitext(fn)
	return a if b[1:] == ext else fn

def make_chksum_N(s,nchars,sep=False):
	if isinstance(s,str):
		s = s.encode()
	if nchars%4 or not (4 <= nchars <= 64):
		return False
	from hashlib import sha256
	s = sha256(sha256(s).digest()).hexdigest().upper()
	sep = ('',' ')[bool(sep)]
	return sep.join([s[i*4:i*4+4] for i in range(nchars//4)])

def make_chksum_8(s,sep=False):
	from .obj import HexStr
	from hashlib import sha256
	s = HexStr(sha256(sha256(s).digest()).hexdigest()[:8].upper(),case='upper')
	return '{} {}'.format(s[:4],s[4:]) if sep else s

def make_chksum_6(s):
	from .obj import HexStr
	from hashlib import sha256
	if isinstance(s,str):
		s = s.encode()
	return HexStr(sha256(s).hexdigest()[:6])

def is_chksum_6(s):
	return len(s) == 6 and set(s) <= set(hexdigits_lc)

def split_into_cols(col_wid,s):
	return ' '.join([s[col_wid*i:col_wid*(i+1)] for i in range(len(s)//col_wid+1)]).rstrip()

def capfirst(s): # different from str.capitalize() - doesn't downcase any uc in string
	return s if len(s) == 0 else s[0].upper() + s[1:]

def decode_timestamp(s):
#	tz_save = open('/etc/timezone').read().rstrip()
	os.environ['TZ'] = 'UTC'
#	os.environ['TZ'] = tz_save
	return int(time.mktime( time.strptime(s,'%Y%m%d_%H%M%S') ))

def make_timestamp(secs=None):
	return '{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}'.format(*time.gmtime(
		int(secs) if secs != None else time.time() )[:6])

def make_timestr(secs=None):
	return '{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(*time.gmtime(
		int(secs) if secs != None else time.time() )[:6])

def secs_to_dhms(secs):
	hrs = secs // 3600
	return '{}{:02d}:{:02d}:{:02d} h/m/s'.format(
		('{} day{}, '.format(hrs//24,suf(hrs//24)) if hrs > 24 else ''),
		hrs % 24,
		(secs // 60) % 60,
		secs % 60
	)

def secs_to_hms(secs):
	return '{:02d}:{:02d}:{:02d}'.format(secs//3600, (secs//60) % 60, secs % 60)

def secs_to_ms(secs):
	return '{:02d}:{:02d}'.format(secs//60, secs % 60)

def is_int(s):
	try:
		int(str(s))
		return True
	except:
		return False

def check_int_between(val,imin,imax,desc):
	if not imin <= int(val) <= imax:
		die(1,f'{val}: invalid value for {desc} (must be between {imin} and {imax})')
	return int(val)

def is_hex_str(s):
	return set(s) <= set(hexdigits)

def is_hex_str_lc(s):
	return set(s) <= set(hexdigits_lc)

def is_utf8(s):
	try:    s.decode('utf8')
	except: return False
	else:   return True

def remove_whitespace(s,ws='\t\r\n '):
	return s.translate(dict((ord(e),None) for e in ws))

def strip_comment(line):
	return re.sub('#.*','',line).rstrip()

def strip_comments(lines):
	pat = re.compile('#.*')
	return [m for m in [pat.sub('',l).rstrip() for l in lines] if m != '']

def compare_chksums(chk1,desc1,chk2,desc2,hdr='',die_on_fail=False,verbose=False):

	if not chk1 == chk2:
		fs = "{} ERROR: {} checksum ({}) doesn't match {} checksum ({})"
		m = fs.format((hdr+':\n   ' if hdr else 'CHECKSUM'),desc2,chk2,desc1,chk1)
		if die_on_fail:
			die(3,m)
		else:
			vmsg(m,force=verbose)
			return False

	vmsg(f'{capfirst(desc1)} checksum OK ({chk1})')
	return True

def compare_or_die(val1, desc1, val2, desc2, e='Error'):
	if val1 != val2:
		die(3,f"{e}: {desc2} ({val2}) doesn't match {desc1} ({val1})")
	dmsg(f'{capfirst(desc2)} OK ({val2})')
	return True

def make_full_path(outdir,outfile):
	return os.path.normpath(os.path.join(outdir, os.path.basename(outfile)))

class oneshot_warning:

	color = 'nocolor'

	def __init__(self,div=None,fmt_args=[],reverse=False):
		self.do(type(self),div,fmt_args,reverse)

	def do(self,wcls,div,fmt_args,reverse):

		def do_warning():
			import mmgen.color
			message = getattr(wcls,'message')
			color = getattr( mmgen.color, getattr(wcls,'color') )
			msg(color('WARNING: ' + message.format(*fmt_args)))

		if not hasattr(wcls,'data'):
			setattr(wcls,'data',[])

		data = getattr(wcls,'data')
		condition = (div in data) if reverse else (not div in data)

		if not div in data:
			data.append(div)

		if condition:
			do_warning()
			self.warning_shown = True
		else:
			self.warning_shown = False

class oneshot_warning_group(oneshot_warning):

	def __init__(self,wcls,div=None,fmt_args=[],reverse=False):
		self.do(getattr(self,wcls),div,fmt_args,reverse)

def stdout_or_pager(s):
	if opt.pager:
		from .ui import do_pager
		do_pager(s)
	else:
		Msg_r(s)

def get_subclasses(cls,names=False):
	def gen(cls):
		for i in cls.__subclasses__():
			yield i
			for j in gen(i):
				yield j
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
			def hashlib_new_wrapper(name,*args,**kwargs):
				if name == 'ripemd160':
					return ripemd160(*args,**kwargs)
				else:
					return hashlib_new(name,*args,**kwargs)
			from .contrib.ripemd160 import ripemd160
			hashlib_new = hashlib.new
			hashlib.new = hashlib_new_wrapper
		called.append(True)

def exit_if_mswin(feature):
	if g.platform == 'win':
		die(2, capfirst(feature) + ' not supported on the MSWin / MSYS2 platform' )
