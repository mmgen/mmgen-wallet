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
util.py:  Low-level routines imported by other modules in the MMGen suite
"""

import sys,os,time,re
from hashlib import sha256
from string import hexdigits,digits

from .color import *
from .globalvars import g
from .opts import opt

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

def die(ev=0,s=''):
	assert isinstance(ev,int)
	if s:
		msg(s)
	sys.exit(ev)

def die_wait(delay,ev=0,s=''):
	assert isinstance(delay,int)
	assert isinstance(ev,int)
	if s:
		msg(s)
	time.sleep(delay)
	sys.exit(ev)

def die_pause(ev=0,s=''):
	assert isinstance(ev,int)
	if s:
		msg(s)
	input('Press ENTER to exit')
	sys.exit(ev)

def Die(ev=0,s=''):
	assert isinstance(ev,int)
	if s:
		Msg(s)
	sys.exit(ev)

def rdie(ev=0,s=''):
	die(ev,red(s))

def ydie(ev=0,s=''):
	die(ev,yellow(s))

def pp_fmt(d):
	import pprint
	return pprint.PrettyPrinter(indent=4,compact=False).pformat(d)

def pp_msg(d):
	msg(pp_fmt(d))

def fmt(s,indent='',strip_char=None):
	"de-indent multiple lines of text, or indent with specified string"
	return indent + ('\n'+indent).join([l.strip(strip_char) for l in s.strip().splitlines()]) + '\n'

def fmt_list(l,fmt='dfl',indent=''):
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
	return lq + sep.join(l) + rq

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

def exit_if_mswin(feature):
	if g.platform == 'win':
		m = capfirst(feature) + ' not supported on the MSWin / MSYS2 platform'
		ydie(1,m)

def warn_altcoins(coinsym,trust_level):
	if trust_level > 3:
		return

	tl_str = (
		red('COMPLETELY UNTESTED'),
		red('LOW'),
		yellow('MEDIUM'),
		green('HIGH'),
	)[trust_level]

	m = """
		Support for coin {!r} is EXPERIMENTAL.  The {pn} project
		assumes no responsibility for any loss of funds you may incur.
		This coin’s {pn} testing status: {}
		Are you sure you want to continue?
	"""
	m = fmt(m).strip().format(coinsym.upper(),tl_str,pn=g.proj_name)

	if g.test_suite:
		qmsg(m)
		return

	if not keypress_confirm(m,default_yes=True):
		sys.exit(0)

def get_keccak():

	from .opts import opt
	# called in opts.init() via CoinProtocol, so must use getattr():
	if getattr(opt,'use_internal_keccak_module',False):
		from .keccak import keccak_256
		qmsg('Using internal keccak module by user request')
		return keccak_256

	try:
		from sha3 import keccak_256
	except:
		from .keccak import keccak_256

	return keccak_256

# From 'man dd':
# c=1, w=2, b=512, kB=1000, K=1024, MB=1000*1000, M=1024*1024,
# GB=1000*1000*1000, G=1024*1024*1024, and so on for T, P, E, Z, Y.
bytespec_map = (
	('c',  1),
	('w',  2),
	('b',  512),
	('kB', 1000),
	('K',  1024),
	('MB', 1000000),
	('M',  1048576),
	('GB', 1000000000),
	('G',  1073741824),
	('TB', 1000000000000),
	('T',  1099511627776),
	('PB', 1000000000000000),
	('P',  1125899906842624),
	('EB', 1000000000000000000),
	('E',  1152921504606846976),
)

def int2bytespec(n,spec,fmt,print_sym=True):
	def spec2int(spec):
		for k,v in bytespec_map:
			if k == spec:
				return v
		else:
			die('{spec}: unrecognized bytespec')
	return '{:{}f}{}'.format( n / spec2int(spec), fmt, spec if print_sym else '' )

def parse_bytespec(nbytes):
	import re
	m = re.match(r'([0123456789.]+)(.*)',nbytes)
	if m:
		if m.group(2):
			for k,v in bytespec_map:
				if k == m.group(2):
					from decimal import Decimal
					return int(Decimal(m.group(1)) * v)
			else:
				msg("Valid byte specifiers: '{}'".format("' '".join([i[0] for i in bytespec_map])))
		elif '.' in nbytes:
			raise ValueError('fractional bytes not allowed')
		else:
			return int(nbytes)

	die(1,f'{nbytes!r}: invalid byte specifier')

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
	s = sha256(sha256(s).digest()).hexdigest().upper()
	sep = ('',' ')[bool(sep)]
	return sep.join([s[i*4:i*4+4] for i in range(nchars//4)])

def make_chksum_8(s,sep=False):
	from .obj import HexStr
	s = HexStr(sha256(sha256(s).digest()).hexdigest()[:8].upper(),case='upper')
	return '{} {}'.format(s[:4],s[4:]) if sep else s
def make_chksum_6(s):
	from .obj import HexStr
	if isinstance(s,str):
		s = s.encode()
	return HexStr(sha256(s).hexdigest()[:6])

def is_chksum_6(s):
	return len(s) == 6 and is_hex_str_lc(s)

def make_iv_chksum(s):
	return sha256(s).hexdigest()[:8].upper()

def splitN(s,n,sep=None): # always return an n-element list
	ret = s.split(sep,n-1)
	return ret + ['' for i in range(n-len(ret))]

def split2(s,sep=None):
	return splitN(s,2,sep) # always return a 2-element list

def split3(s,sep=None):
	return splitN(s,3,sep) # always return a 3-element list

def split_into_cols(col_wid,s):
	return ' '.join([s[col_wid*i:col_wid*(i+1)] for i in range(len(s)//col_wid+1)]).rstrip()

def capfirst(s): # different from str.capitalize() - doesn't downcase any uc in string
	return s if len(s) == 0 else s[0].upper() + s[1:]

def decode_timestamp(s):
#	tz_save = open('/etc/timezone').read().rstrip()
	os.environ['TZ'] = 'UTC'
	ts = time.strptime(s,'%Y%m%d_%H%M%S')
	t = time.mktime(ts)
#	os.environ['TZ'] = tz_save
	return int(t)

def make_timestamp(secs=None):
	t = int(secs) if secs else time.time()
	return '{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}'.format(*time.gmtime(t)[:6])

def make_timestr(secs=None):
	t = int(secs) if secs else time.time()
	return '{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(*time.gmtime(t)[:6])

def secs_to_dhms(secs):
	dsecs = secs // 3600
	return '{}{:02d}:{:02d}:{:02d} h/m/s'.format(
		('{} day{}, '.format(dsecs//24,suf(dsecs//24)) if dsecs > 24 else ''),
		dsecs % 24,
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

def is_hex_str(s):
	return set(list(s.lower())) <= set(list(hexdigits.lower()))

def is_hex_str_lc(s):
	return set(list(s)) <= set(list(hexdigits.lower()))

def is_utf8(s):
	try:    s.decode('utf8')
	except: return False
	else:   return True

def remove_whitespace(s,ws='\t\r\n '):
	return s.translate(dict((ord(e),None) for e in ws))

def pretty_format(s,width=80,pfx=''):
	out = []
	while(s):
		if len(s) <= width:
			out.append(s)
			break
		i = s[:width].rfind(' ')
		out.append(s[:i])
		s = s[i+1:]
	return pfx + ('\n'+pfx).join(out)

def block_format(data,gw=2,cols=8,line_nums=None,data_is_hex=False):
	assert line_nums in (None,'hex','dec'),"'line_nums' must be one of None, 'hex' or 'dec'"
	ln_fs = '{:06x}: ' if line_nums == 'hex' else '{:06}: '
	bytes_per_chunk = gw
	if data_is_hex:
		gw *= 2
	nchunks = len(data)//gw + bool(len(data)%gw)
	return ''.join(
		('' if (line_nums == None or i % cols) else ln_fs.format(i*bytes_per_chunk))
		+ data[i*gw:i*gw+gw]
		+ (' ' if (not cols or (i+1) % cols) else '\n')
			for i in range(nchunks)
	).rstrip() + '\n'

def pretty_hexdump(data,gw=2,cols=8,line_nums=None):
	return block_format(data.hex(),gw,cols,line_nums,data_is_hex=True)

def decode_pretty_hexdump(data):
	from string import hexdigits
	pat = re.compile(fr'^[{hexdigits}]+:\s+')
	lines = [pat.sub('',line) for line in data.splitlines()]
	try:
		return bytes.fromhex(''.join((''.join(lines).split())))
	except:
		msg('Data not in hexdump format')
		return False

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

def check_wallet_extension(fn):
	from .wallet import Wallet
	if not Wallet.ext_to_type(get_extension(fn)):
		from .exception import BadFileExtension
		raise BadFileExtension(f'{fn!r}: unrecognized seed source file extension')

def make_full_path(outdir,outfile):
	return os.path.normpath(os.path.join(outdir, os.path.basename(outfile)))

def confirm_or_raise(message,q,expect='YES',exit_msg='Exiting at user request'):
	if message.strip():
		msg(message.strip())
	a = f'{q}  ' if q[0].isupper() else f'Are you sure you want to {q}?\n'
	b = f'Type uppercase {expect!r} to confirm: '
	if line_input(a+b).strip() != expect:
		from .exception import UserNonConfirmation
		raise UserNonConfirmation(exit_msg)

def get_words_from_user(prompt):
	words = line_input(prompt, echo=opt.echo_passphrase).split()
	dmsg('Sanitized input: [{}]'.format(' '.join(words)))
	return words

def get_data_from_user(desc='data'): # user input MUST be UTF-8
	data = line_input(f'Enter {desc}: ',echo=opt.echo_passphrase)
	dmsg(f'User input: [{data}]')
	return data

class oneshot_warning:

	color = 'nocolor'

	def __init__(self,div=None,fmt_args=[],reverse=False):
		self.do(type(self),div,fmt_args,reverse)

	def do(self,wcls,div,fmt_args,reverse):

		def do_warning():
			message = getattr(wcls,'message')
			color = globals()[getattr(wcls,'color')]
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

class pwfile_reuse_warning(oneshot_warning):
	message = 'Reusing passphrase from file {!r} at user request'
	def __init__(self,fn):
		oneshot_warning.__init__(self,div=fn,fmt_args=[fn],reverse=True)

def line_input(prompt,echo=True,insert_txt=''):
	"""
	multi-line prompts OK
	one-line prompts must begin at beginning of line
	empty prompts forbidden due to interactions with readline
	"""
	assert prompt,'calling line_input() with an empty prompt forbidden'

	def init_readline():
		try:
			import readline
		except ImportError:
			return False
		else:
			if insert_txt:
				readline.set_startup_hook(lambda: readline.insert_text(insert_txt))
				return True
			else:
				return False

	if not sys.stdout.isatty():
		msg_r(prompt)
		prompt = ''

	from .term import kb_hold_protect
	kb_hold_protect()

	if g.test_suite_popen_spawn:
		msg(prompt)
		sys.stderr.flush()
		reply = os.read(0,4096).decode().rstrip('\n') # strip NL to mimic behavior of input()
	elif echo or not sys.stdin.isatty():
		clear_buffer = init_readline() if sys.stdin.isatty() else False
		reply = input(prompt)
		if clear_buffer:
			import readline
			readline.set_startup_hook(lambda: readline.insert_text(''))
	else:
		from getpass import getpass
		if g.platform == 'win':
			# MSWin hack - getpass('foo') doesn't flush stderr
			msg_r(prompt.strip()) # getpass('') adds a space
			sys.stderr.flush()
			reply = getpass('')
		else:
			reply = getpass(prompt)

	kb_hold_protect()

	return reply.strip()

def keypress_confirm(prompt,default_yes=False,verbose=False,no_nl=False,complete_prompt=False):

	if not complete_prompt:
		prompt = '{} {}: '.format( prompt, '(Y/n)' if default_yes else '(y/N)' )

	nl = f'\r{" "*len(prompt)}\r' if no_nl else '\n'

	if g.accept_defaults:
		msg(prompt)
		return default_yes

	from .term import get_char
	while True:
		reply = get_char(prompt,immed_chars='yYnN').strip('\n\r')
		if not reply:
			msg_r(nl)
			return True if default_yes else False
		elif reply in 'yYnN':
			msg_r(nl)
			return True if reply in 'yY' else False
		else:
			msg_r('\nInvalid reply\n' if verbose else '\r')

def do_pager(text):

	pagers = ['less','more']
	end_msg = '\n(end of text)\n\n'
	# --- Non-MSYS Windows code deleted ---
	# raw, chop, horiz scroll 8 chars, disable buggy line chopping in MSYS
	os.environ['LESS'] = (('--shift 8 -RS'),('-cR -#1'))[g.platform=='win']

	if 'PAGER' in os.environ and os.environ['PAGER'] != pagers[0]:
		pagers = [os.environ['PAGER']] + pagers

	from subprocess import run
	for pager in pagers:
		try:
			m = text + ('' if pager == 'less' else end_msg)
			p = run([pager],input=m.encode(),check=True)
			msg_r('\r')
		except:
			pass
		else:
			break
	else:
		Msg(text+end_msg)

def do_license_msg(immed=False):

	if opt.quiet or g.no_license or opt.yes or not g.stdin_tty:
		return

	import mmgen.license as gpl
	msg(gpl.warning)

	from .term import get_char
	prompt = "Press 'w' for conditions and warranty info, or 'c' to continue: "
	while True:
		reply = get_char(prompt, immed_chars=('','wc')[bool(immed)])
		if reply == 'w':
			do_pager(gpl.conditions)
		elif reply == 'c':
			msg('')
			break
		else:
			msg_r('\r')
	msg('')

def format_par(s,indent=0,width=80,as_list=False):
	words,lines = s.split(),[]
	assert width >= indent + 4,'width must be >= indent + 4'
	while words:
		line = ''
		while len(line) <= (width-indent) and words:
			if line and len(line) + len(words[0]) + 1 > width-indent: break
			line += ('',' ')[bool(line)] + words.pop(0)
		lines.append(' '*indent + line)
	return lines if as_list else '\n'.join(lines) + '\n'

def get_subclasses(cls,names=False):
	def gen(cls):
		for i in cls.__subclasses__():
			yield i
			for j in gen(i):
				yield j
	return tuple((c.__name__ for c in gen(cls)) if names else gen(cls))

def altcoin_subclass(cls,proto,mod_dir):
	"""
	magic module loading and class retrieval
	"""
	from .protocol import CoinProtocol
	if isinstance(proto,CoinProtocol.Bitcoin):
		return cls

	modname = f'mmgen.altcoins.{proto.base_coin.lower()}.{mod_dir}'

	import importlib
	if mod_dir == 'tx': # nested classes
		outer_clsname,inner_clsname = (
			proto.mod_clsname
			+ ('Token' if proto.tokensym else '')
			+ cls.__qualname__ ).split('.')
		return getattr(getattr(importlib.import_module(modname),outer_clsname),inner_clsname)
	else:
		clsname = (
			proto.mod_clsname
			+ ('Token' if proto.tokensym else '')
			+ cls.__name__ )
		return getattr(importlib.import_module(modname),clsname)

# decorator for TrackingWallet
def write_mode(orig_func):
	def f(self,*args,**kwargs):
		if self.mode != 'w':
			die(1,'{} opened in read-only mode: cannot execute method {}()'.format(
				type(self).__name__,
				locals()['orig_func'].__name__
			))
		return orig_func(self,*args,**kwargs)
	return f

def run_session(callback,backend=None):

	async def do():
		if (backend or opt.rpc_backend) == 'aiohttp':
			import aiohttp
			async with aiohttp.ClientSession(
				headers = { 'Content-Type': 'application/json' },
				connector = aiohttp.TCPConnector(limit_per_host=g.aiohttp_rpc_queue_len),
			) as g.session:
				return await callback
		else:
			return await callback

	import asyncio
	return asyncio.run(do())
