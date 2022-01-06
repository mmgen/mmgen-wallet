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

import sys,os,time,stat,re
from subprocess import run,PIPE,DEVNULL
from hashlib import sha256
from string import hexdigits,digits
from .color import *
from .exception import *
from .globalvars import *

CUR_HIDE = '\033[?25l'
CUR_SHOW = '\033[?25h'

if g.platform == 'win':
	def msg_r(s):
		try:
			g.stderr.write(s)
			g.stderr.flush()
		except:
			os.write(2,s.encode())
	def Msg_r(s):
		try:
			g.stdout.write(s)
			g.stdout.flush()
		except:
			os.write(1,s.encode())
	def msg(s): msg_r(s + '\n')
	def Msg(s): Msg_r(s + '\n')
else:
	def msg_r(s):
		g.stderr.write(s)
		g.stderr.flush()
	def Msg_r(s):
		g.stdout.write(s)
		g.stdout.flush()
	def msg(s):   g.stderr.write(s + '\n')
	def Msg(s):   g.stdout.write(s + '\n')

def msgred(s): msg(red(s))
def rmsg(s):   msg(red(s))
def rmsg_r(s): msg_r(red(s))
def ymsg(s):   msg(yellow(s))
def ymsg_r(s): msg_r(yellow(s))
def gmsg(s):   msg(green(s))
def gmsg_r(s): msg_r(green(s))
def bmsg(s):   msg(blue(s))
def bmsg_r(s): msg_r(blue(s))

def mmsg(*args):
	for d in args: Msg(repr(d))
def mdie(*args):
	mmsg(*args); sys.exit(0)

def die_wait(delay,ev=0,s=''):
	assert isinstance(delay,int)
	assert isinstance(ev,int)
	if s: msg(s)
	time.sleep(delay)
	sys.exit(ev)
def die_pause(ev=0,s=''):
	assert isinstance(ev,int)
	if s: msg(s)
	input('Press ENTER to exit')
	sys.exit(ev)
def die(ev=0,s=''):
	assert isinstance(ev,int)
	if s: msg(s)
	sys.exit(ev)
def Die(ev=0,s=''):
	assert isinstance(ev,int)
	if s: Msg(s)
	sys.exit(ev)

def rdie(ev=0,s=''): die(ev,red(s))
def ydie(ev=0,s=''): die(ev,yellow(s))

def pp_fmt(d):
	import pprint
	return pprint.PrettyPrinter(indent=4,compact=True).pformat(d)
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

def set_for_type(val,refval,desc,invert_bool=False,src=None):

	if type(refval) == bool:
		v = str(val).lower()
		ret = (
			True  if v in ('true','yes','1','on') else
			False if v in ('false','no','none','0','off','') else
			None
		)
		if ret is not None:
			return not ret if invert_bool else ret
	else:
		try:
			return type(refval)(not val if invert_bool else val)
		except:
			pass

	die(1,'{!r}: invalid value for {!r}{} (must be of type {!r})'.format(
		val,
		desc,
		' in {!r}'.format(src) if src else '',
		type(refval).__name__) )

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

def check_or_create_dir(path):
	try:
		os.listdir(path)
	except:
		if os.getenv('MMGEN_TEST_SUITE'):
			try: # exception handling required for MSWin/MSYS2
				run(['/bin/rm','-rf',path])
			except:
				pass
		try:
			os.makedirs(path,0o700)
		except:
			die(2,f'ERROR: unable to read or create path {path!r}')

from .opts import opt

def qmsg(s,alt=None):
	if opt.quiet:
		if alt != None: msg(alt)
	else: msg(s)
def qmsg_r(s,alt=None):
	if opt.quiet:
		if alt != None: msg_r(alt)
	else: msg_r(s)
def vmsg(s,force=False):
	if opt.verbose or force: msg(s)
def vmsg_r(s,force=False):
	if opt.verbose or force: msg_r(s)
def Vmsg(s,force=False):
	if opt.verbose or force: Msg(s)
def Vmsg_r(s,force=False):
	if opt.verbose or force: Msg_r(s)
def dmsg(s):
	if opt.debug: msg(s)

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
	if isinstance(s,str): s = s.encode()
	if nchars%4 or not (4 <= nchars <= 64): return False
	s = sha256(sha256(s).digest()).hexdigest().upper()
	sep = ('',' ')[bool(sep)]
	return sep.join([s[i*4:i*4+4] for i in range(nchars//4)])

def make_chksum_8(s,sep=False):
	from .obj import HexStr
	s = HexStr(sha256(sha256(s).digest()).hexdigest()[:8].upper(),case='upper')
	return '{} {}'.format(s[:4],s[4:]) if sep else s
def make_chksum_6(s):
	from .obj import HexStr
	if isinstance(s,str): s = s.encode()
	return HexStr(sha256(s).hexdigest()[:6])
def is_chksum_6(s): return len(s) == 6 and is_hex_str_lc(s)

def make_iv_chksum(s): return sha256(s).hexdigest()[:8].upper()

def splitN(s,n,sep=None):                      # always return an n-element list
	ret = s.split(sep,n-1)
	return ret + ['' for i in range(n-len(ret))]
def split2(s,sep=None): return splitN(s,2,sep) # always return a 2-element list
def split3(s,sep=None): return splitN(s,3,sep) # always return a 3-element list

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

def is_hex_str(s):    return set(list(s.lower())) <= set(list(hexdigits.lower()))
def is_hex_str_lc(s): return set(list(s))         <= set(list(hexdigits.lower()))

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
	return re.sub(r'\s+$','',re.sub(r'#.*','',line))

def strip_comments(lines):
	return [m for m in [strip_comment(l) for l in lines] if m != '']

def get_hash_params(hash_preset):
	if hash_preset in g.hash_presets:
		return g.hash_presets[hash_preset] # N,r,p
	else: # Shouldn't be here
		die(3,f"{hash_preset}: invalid 'hash_preset' value")

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

def check_binary(args):
	try:
		run(args,stdout=DEVNULL,stderr=DEVNULL,check=True)
	except:
		rdie(2,f'{args[0]!r} binary missing, not in path, or not executable')

def shred_file(fn,verbose=False):
	check_binary(['shred','--version'])
	run(
		['shred','--force','--iterations=30','--zero','--remove=wipesync']
		+ (['--verbose'] if verbose else [])
		+ [fn],
		check=True )

def open_or_die(filename,mode,silent=False):
	try:
		return open(filename,mode)
	except:
		die(2,'' if silent else
			'Unable to open file {!r} for {}'.format(
				({0:'STDIN',1:'STDOUT',2:'STDERR'}[filename] if type(filename) == int else filename),
				('reading' if 'r' in mode else 'writing')
			))

def check_file_type_and_access(fname,ftype,blkdev_ok=False):

	access,op_desc = (
		(os.W_OK,'writ') if ftype in ('output file','output directory') else
		(os.R_OK,'read') )

	if ftype == 'output directory':
		ok_types = [(stat.S_ISDIR, 'output directory')]
	else:
		ok_types = [
			(stat.S_ISREG,'regular file'),
			(stat.S_ISLNK,'symbolic link')
		]
		if blkdev_ok:
			ok_types.append((stat.S_ISBLK,'block device'))

	try:
		mode = os.stat(fname).st_mode
	except:
		raise FileNotFound(f'Requested {ftype} {fname!r} not found')

	for t in ok_types:
		if t[0](mode):
			break
	else:
		ok_list = ' or '.join( t[1] for t in ok_types )
		die(1,f'Requested {ftype} {fname!r} is not a {ok_list}')

	if not os.access(fname,access):
		die(1,f'Requested {ftype} {fname!r} is not {op_desc}able by you')

	return True

def check_infile(f,blkdev_ok=False):
	return check_file_type_and_access(f,'input file',blkdev_ok=blkdev_ok)
def check_outfile(f,blkdev_ok=False):
	return check_file_type_and_access(f,'output file',blkdev_ok=blkdev_ok)
def check_outdir(f):
	return check_file_type_and_access(f,'output directory')
def check_wallet_extension(fn):
	from .wallet import Wallet
	if not Wallet.ext_to_type(get_extension(fn)):
		raise BadFileExtension(f'{fn!r}: unrecognized seed source file extension')
def make_full_path(outdir,outfile):
	return os.path.normpath(os.path.join(outdir, os.path.basename(outfile)))

def get_seed_file(cmd_args,nargs,invoked_as=None):
	from .filename import find_file_in_dir
	from .wallet import MMGenWallet

	wf = find_file_in_dir(MMGenWallet,g.data_dir)

	wd_from_opt = bool(opt.hidden_incog_input_params or opt.in_fmt) # have wallet data from opt?

	import mmgen.opts as opts
	if len(cmd_args) + (wd_from_opt or bool(wf)) < nargs:
		if not wf:
			msg('No default wallet found, and no other seed source was specified')
		opts.usage()
	elif len(cmd_args) > nargs:
		opts.usage()
	elif len(cmd_args) == nargs and wf and invoked_as != 'gen':
		qmsg('Warning: overriding default wallet with user-supplied wallet')

	if cmd_args or wf:
		check_infile(cmd_args[0] if cmd_args else wf)

	return cmd_args[0] if cmd_args else (wf,None)[wd_from_opt]

def confirm_or_raise(message,q,expect='YES',exit_msg='Exiting at user request'):
	if message.strip():
		msg(message.strip())
	a = f'{q}  ' if q[0].isupper() else f'Are you sure you want to {q}?\n'
	b = f'Type uppercase {expect!r} to confirm: '
	if line_input(a+b).strip() != expect:
		raise UserNonConfirmation(exit_msg)

def write_data_to_file( outfile,data,desc='data',
						ask_write=False,
						ask_write_prompt='',
						ask_write_default_yes=True,
						ask_overwrite=True,
						ask_tty=True,
						no_tty=False,
						quiet=False,
						binary=False,
						ignore_opt_outdir=False,
						check_data=False,
						cmp_data=None):

	if quiet: ask_tty = ask_overwrite = False
	if opt.quiet: ask_overwrite = False

	if ask_write_default_yes == False or ask_write_prompt:
		ask_write = True

	def do_stdout():
		qmsg('Output to STDOUT requested')
		if g.stdin_tty:
			if no_tty:
				die(2,f'Printing {desc} to screen is not allowed')
			if (ask_tty and not opt.quiet) or binary:
				confirm_or_raise('',f'output {desc} to screen')
		else:
			try:    of = os.readlink(f'/proc/{os.getpid()}/fd/1') # Linux
			except: of = None # Windows

			if of:
				if of[:5] == 'pipe:':
					if no_tty:
						die(2,f'Writing {desc} to pipe is not allowed')
					if ask_tty and not opt.quiet:
						confirm_or_raise('',f'output {desc} to pipe')
						msg('')
				of2,pd = os.path.relpath(of),os.path.pardir
				msg('Redirecting output to file {!r}'.format(of if of2[:len(pd)] == pd else of2))
			else:
				msg('Redirecting output to file')

		if binary and g.platform == 'win':
			import msvcrt
			msvcrt.setmode(sys.stdout.fileno(),os.O_BINARY)

		# MSWin workaround. See msg_r()
		try:
			sys.stdout.write(data.decode() if isinstance(data,bytes) else data)
		except:
			os.write(1,data if isinstance(data,bytes) else data.encode())

	def do_file(outfile,ask_write_prompt):
		if opt.outdir and not ignore_opt_outdir and not os.path.isabs(outfile):
			outfile = make_full_path(opt.outdir,outfile)

		if ask_write:
			if not ask_write_prompt:
				ask_write_prompt = f'Save {desc}?'
			if not keypress_confirm(ask_write_prompt,
						default_yes=ask_write_default_yes):
				die(1,f'{capfirst(desc)} not saved')

		hush = False
		if os.path.lexists(outfile) and ask_overwrite:
			confirm_or_raise('',f'File {outfile!r} already exists\nOverwrite?')
			msg(f'Overwriting file {outfile!r}')
			hush = True

		# not atomic, but better than nothing
		# if cmp_data is empty, file can be either empty or non-existent
		if check_data:
			try:
				with open(outfile,('r','rb')[bool(binary)]) as fp:
					d = fp.read()
			except:
				d = ''
			finally:
				if d != cmp_data:
					if g.test_suite:
						print_diff(cmp_data,d)
					die(3,f'{desc} in file {outfile!r} has been altered by some other program! Aborting file write')

		# To maintain portability, always open files in binary mode
		# If 'binary' option not set, encode/decode data before writing and after reading
		try:
			with open_or_die(outfile,'wb') as fp:
				fp.write(data if binary else data.encode())
		except:
			die(2,f'Failed to write {desc} to file {outfile!r}')

		if not (hush or quiet):
			msg(f'{capfirst(desc)} written to file {outfile!r}')

		return True

	if opt.stdout or outfile in ('','-'):
		do_stdout()
	elif sys.stdin.isatty() and not sys.stdout.isatty():
		do_stdout()
	else:
		do_file(outfile,ask_write_prompt)

def get_words_from_user(prompt):
	words = line_input(prompt, echo=opt.echo_passphrase).split()
	dmsg('Sanitized input: [{}]'.format(' '.join(words)))
	return words

def get_words_from_file(infile,desc,quiet=False):

	if not quiet:
		qmsg(f'Getting {desc} from file {infile!r}')

	with open_or_die(infile, 'rb') as fp:
		data = fp.read()

	try:
		words = data.decode().split()
	except:
		die(1,f'{capfirst(desc)} data must be UTF-8 encoded.')

	dmsg('Sanitized input: [{}]'.format(' '.join(words)))

	return words

def get_words(infile,desc,prompt):
	if infile:
		return get_words_from_file(infile,desc)
	else:
		return get_words_from_user(prompt)

def mmgen_decrypt_file_maybe(fn,desc='',quiet=False,silent=False):
	d = get_data_from_file(fn,desc,binary=True,quiet=quiet,silent=silent)
	have_enc_ext = get_extension(fn) == g.mmenc_ext
	if have_enc_ext or not is_utf8(d):
		m = ('Attempting to decrypt','Decrypting')[have_enc_ext]
		qmsg(f'{m} {desc} {fn!r}')
		from .crypto import mmgen_decrypt_retry
		d = mmgen_decrypt_retry(d,desc)
	return d

def get_lines_from_file(fn,desc='',trim_comments=False,quiet=False,silent=False):
	dec = mmgen_decrypt_file_maybe(fn,desc,quiet=quiet,silent=silent)
	ret = dec.decode().splitlines()
	if trim_comments:
		ret = strip_comments(ret)
	dmsg(f'Got {len(ret)} lines from file {fn!r}')
	return ret

def get_data_from_user(desc='data'): # user input MUST be UTF-8
	data = line_input(f'Enter {desc}: ',echo=opt.echo_passphrase)
	dmsg(f'User input: [{data}]')
	return data

def get_data_from_file(infile,desc='data',dash=False,silent=False,binary=False,quiet=False):

	if not opt.quiet and not silent and not quiet and desc:
		qmsg(f'Getting {desc} from file {infile!r}')

	with open_or_die(
			(0 if dash and infile == '-' else infile),
			'rb',
			silent=silent) as fp:
		data = fp.read(g.max_input_size+1)

	if not binary:
		data = data.decode()

	if len(data) == g.max_input_size + 1:
		raise MaxInputSizeExceeded(f'Too much input data!  Max input data size: {f.max_input_size} bytes')

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
