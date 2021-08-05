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
util.py:  Low-level routines imported by other modules in the MMGen suite
"""

import sys,os,time,stat,re
from subprocess import run
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

	die(1,"'{}': invalid byte specifier".format(nbytes))

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
		die(2,'{}: invalid parameter for suf()'.format(arg))
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

def is_digits(s): return set(list(s)) <= set(list(digits))
def is_int(s):
	try:
		int(str(s))
		return True
	except:
		return False

def is_hex_str(s):    return set(list(s.lower())) <= set(list(hexdigits.lower()))
def is_hex_str_lc(s): return set(list(s))         <= set(list(hexdigits.lower()))
def is_hex_str_uc(s): return set(list(s))         <= set(list(hexdigits.upper()))

def is_utf8(s):
	return is_ascii(s,enc='utf8')
def is_ascii(s,enc='ascii'):
	try:    s.decode(enc)
	except: return False
	else:   return True

def check_int_between(n,lo,hi,desc='value'):
	import re
	m = re.match(r'-{0,1}[0-9]+',str(n))
	if m == None:
		raise NotAnInteger(f'{n}: {desc} must be an integer')
	n = int(n)
	if n < lo or n > hi:
		raise IntegerOutOfRange(f'{n}: {desc} must be between {lo} and {hi}')
	return n

def match_ext(addr,ext):
	return addr.split('.')[-1] == ext

def file_exists(f):
	try:
		os.stat(f)
		return True
	except:
		return False

def file_is_readable(f):
	from stat import S_IREAD
	try:
		assert os.stat(f).st_mode & S_IREAD
	except:
		return False
	else:
		return True

def get_from_brain_opt_params():
	l,p = opt.from_brain.split(',')
	return(int(l),p)

def remove_whitespace(s):
	return s.translate(dict((ord(ws),None) for ws in '\t\r\n '))

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

def strip_comments(line):
	return re.sub(r'\s+$','',re.sub(r'#.*','',line,1))

def remove_comments(lines):
	return [m for m in [strip_comments(l) for l in lines] if m != '']

def get_hash_params(hash_preset):
	if hash_preset in g.hash_presets:
		return g.hash_presets[hash_preset] # N,p,r,buflen
	else: # Shouldn't be here
		die(3,"{}: invalid 'hash_preset' value".format(hash_preset))

def compare_chksums(chk1,desc1,chk2,desc2,hdr='',die_on_fail=False,verbose=False):

	if not chk1 == chk2:
		fs = "{} ERROR: {} checksum ({}) doesn't match {} checksum ({})"
		m = fs.format((hdr+':\n   ' if hdr else 'CHECKSUM'),desc2,chk2,desc1,chk1)
		if die_on_fail:
			die(3,m)
		else:
			vmsg(m,force=verbose)
			return False

	vmsg('{} checksum OK ({})'.format(capfirst(desc1),chk1))
	return True

def compare_or_die(val1, desc1, val2, desc2, e='Error'):
	if val1 != val2:
		die(3,"{}: {} ({}) doesn't match {} ({})".format(e,desc2,val2,desc1,val1))
	dmsg('{} OK ({})'.format(capfirst(desc2),val2))
	return True

def open_file_or_exit(filename,mode,silent=False):
	try:
		return open(filename, mode)
	except:
		op = ('writing','reading')['r' in mode]
		die(2,("Unable to open file '{}' for {}".format(filename,op),'')[silent])

def check_file_type_and_access(fname,ftype,blkdev_ok=False):

	a = ((os.R_OK,'read'),(os.W_OK,'writ'))
	access,m = a[ftype in ('output file','output directory')]

	ok_types = [
		(stat.S_ISREG,'regular file'),
		(stat.S_ISLNK,'symbolic link')
	]
	if blkdev_ok: ok_types.append((stat.S_ISBLK,'block device'))
	if ftype == 'output directory': ok_types = [(stat.S_ISDIR, 'output directory')]

	try: mode = os.stat(fname).st_mode
	except:
		raise FileNotFound("Requested {} '{}' not found".format(ftype,fname))

	for t in ok_types:
		if t[0](mode): break
	else:
		die(1,"Requested {} '{}' is not a {}".format(ftype,fname,' or '.join([t[1] for t in ok_types])))

	if not os.access(fname, access):
		die(1,"Requested {} '{}' is not {}able by you".format(ftype,fname,m))

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
		raise BadFileExtension("'{}': unrecognized seed source file extension".format(fn))
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
	m = message.strip()
	if m: msg(m)
	a = q+'  ' if q[0].isupper() else 'Are you sure you want to {}?\n'.format(q)
	b = "Type uppercase '{}' to confirm: ".format(expect)
	if my_raw_input(a+b).strip() != expect:
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
				die(2,'Printing {} to screen is not allowed'.format(desc))
			if (ask_tty and not opt.quiet) or binary:
				confirm_or_raise('','output {} to screen'.format(desc))
		else:
			try:    of = os.readlink('/proc/{}/fd/1'.format(os.getpid())) # Linux
			except: of = None # Windows

			if of:
				if of[:5] == 'pipe:':
					if no_tty:
						die(2,'Writing {} to pipe is not allowed'.format(desc))
					if ask_tty and not opt.quiet:
						confirm_or_raise('','output {} to pipe'.format(desc))
						msg('')
				of2,pd = os.path.relpath(of),os.path.pardir
				msg("Redirecting output to file '{}'".format((of2,of)[of2[:len(pd)] == pd]))
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
			if not ask_write_prompt: ask_write_prompt = 'Save {}?'.format(desc)
			if not keypress_confirm(ask_write_prompt,
						default_yes=ask_write_default_yes):
				die(1,'{} not saved'.format(capfirst(desc)))

		hush = False
		if file_exists(outfile) and ask_overwrite:
			q = "File '{}' already exists\nOverwrite?".format(outfile)
			confirm_or_raise('',q)
			msg("Overwriting file '{}'".format(outfile))
			hush = True

		# not atomic, but better than nothing
		# if cmp_data is empty, file can be either empty or non-existent
		if check_data:
			try:
				d = open(outfile,('r','rb')[bool(binary)]).read()
			except:
				d = ''
			finally:
				if d != cmp_data:
					if g.test_suite:
						print_diff(cmp_data,d)
					m = "{} in file '{}' has been altered by some other program!  Aborting file write"
					die(3,m.format(desc,outfile))

		# To maintain portability, always open files in binary mode
		# If 'binary' option not set, encode/decode data before writing and after reading
		f = open_file_or_exit(outfile,'wb')

		try:
			f.write(data if binary else data.encode())
		except:
			die(2,"Failed to write {} to file '{}'".format(desc,outfile))
		f.close

		if not (hush or quiet):
			msg("{} written to file '{}'".format(capfirst(desc),outfile))

		return True

	if opt.stdout or outfile in ('','-'):
		do_stdout()
	elif sys.stdin.isatty() and not sys.stdout.isatty():
		do_stdout()
	else:
		do_file(outfile,ask_write_prompt)

def get_words_from_user(prompt):
	words = my_raw_input(prompt, echo=opt.echo_passphrase).split()
	dmsg('Sanitized input: [{}]'.format(' '.join(words)))
	return words

def get_words_from_file(infile,desc,quiet=False):
	if not quiet:
		qmsg("Getting {} from file '{}'".format(desc,infile))
	f = open_file_or_exit(infile, 'rb')
	try: words = f.read().decode().split()
	except: die(1,'{} data must be UTF-8 encoded.'.format(capfirst(desc)))
	f.close()
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
		qmsg("{} {} '{}'".format(m,desc,fn))
		from .crypto import mmgen_decrypt_retry
		d = mmgen_decrypt_retry(d,desc)
	return d

def get_lines_from_file(fn,desc='',trim_comments=False,quiet=False,silent=False):
	dec = mmgen_decrypt_file_maybe(fn,desc,quiet=quiet,silent=silent)
	ret = dec.decode().splitlines()
	if trim_comments: ret = remove_comments(ret)
	dmsg("Got {} lines from file '{}'".format(len(ret),fn))
	return ret

def get_data_from_user(desc='data'): # user input MUST be UTF-8
	p = ('','Enter {}: '.format(desc))[g.stdin_tty]
	data = my_raw_input(p,echo=opt.echo_passphrase)
	dmsg('User input: [{}]'.format(data))
	return data

def get_data_from_file(infile,desc='data',dash=False,silent=False,binary=False,quiet=False):

	if not opt.quiet and not silent and not quiet and desc:
		qmsg("Getting {} from file '{}'".format(desc,infile))

	if dash and infile == '-':
		data = os.fdopen(0,'rb').read(g.max_input_size+1)
	else:
		data = open_file_or_exit(infile,'rb',silent=silent).read(g.max_input_size+1)

	if not binary:
		data = data.decode()

	if len(data) == g.max_input_size + 1:
		raise MaxInputSizeExceeded('Too much input data!  Max input data size: {} bytes'.format(g.max_input_size))

	return data

passwd_files_used = {}

class oneshot_warning:

	def __init__(self,wcls,div=None,fmt_args=[]):

		def do_warning():
			cls = getattr(self,wcls)
			message = getattr(cls,'message')
			color = globals()[getattr(cls,'color')]
			msg(color('WARNING: ' + message.format(*fmt_args)))

		flag = wcls+'_warning_shown'

		if not hasattr(self,flag):
			setattr(type(self),flag,[])

		attr = getattr(type(self),flag)

		if not div in attr:
			do_warning()
			attr.append(div)

def pwfile_reuse_warning(passwd_file):
	if passwd_file in passwd_files_used:
		qmsg(f'Reusing passphrase from file {passwd_file!r} at user request')
		return True
	passwd_files_used[passwd_file] = True
	return False

def my_raw_input(prompt,echo=True,insert_txt='',use_readline=True):

	try: import readline
	except: use_readline = False # Windows

	if use_readline and sys.stdout.isatty():
		def st_hook(): readline.insert_text(insert_txt)
		readline.set_startup_hook(st_hook)
	else:
		msg_r(prompt)
		prompt = ''

	from .term import kb_hold_protect
	kb_hold_protect()

	if g.test_suite_popen_spawn:
		msg(prompt)
		sys.stderr.flush()
		reply = os.read(0,4096).decode()
	elif echo or not sys.stdin.isatty():
		reply = input(prompt)
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

	try:
		return reply.strip()
	except:
		die(1,'User input must be UTF-8 encoded.')

def keypress_confirm(prompt,default_yes=False,verbose=False,no_nl=False,complete_prompt=False):

	q = ('(y/N)','(Y/n)')[bool(default_yes)]
	p = prompt if complete_prompt else '{} {}: '.format(prompt,q)
	nl = ('\n','\r{}\r'.format(' '*len(p)))[no_nl]

	if g.accept_defaults:
		msg(p)
		return default_yes

	from .term import get_char
	while True:
		reply = get_char(p,immed_chars='yYnN').strip('\n\r')
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

	p = "Press 'w' for conditions and warranty info, or 'c' to continue:"
	import mmgen.license as gpl
	msg(gpl.warning)
	prompt = '{} '.format(p.strip())

	from .term import get_char
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
			m = '{} opened in read-only mode: cannot execute method {}()'
			die(1,m.format(type(self).__name__,locals()['orig_func'].__name__))
		return orig_func(self,*args,**kwargs)
	return f

def run_session(callback,backend=None):
	backend = backend or opt.rpc_backend
	import asyncio
	async def do():
		if backend == 'aiohttp':
			import aiohttp
			async with aiohttp.ClientSession(
				headers = { 'Content-Type': 'application/json' },
				connector = aiohttp.TCPConnector(limit_per_host=g.aiohttp_rpc_queue_len),
			) as g.session:
				ret = await callback
			return ret
		else:
			return await callback

	# return asyncio.run(do()) # Python 3.7+
	return asyncio.get_event_loop().run_until_complete(do())
