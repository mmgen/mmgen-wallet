#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>
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
from hashlib import sha256
from string import hexdigits,digits
from mmgen.color import *
from mmgen.exception import *
from mmgen.globalvars import *

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

def set_for_type(val,refval,desc,invert_bool=False,src=None):
	src_str = (''," in '{}'".format(src))[bool(src)]
	if type(refval) == bool:
		v = str(val).lower()
		if v in ('true','yes','1'):          ret = True
		elif v in ('false','no','none','0'): ret = False
		else: die(1,"'{}': invalid value for '{}'{} (must be of type '{}')".format(
				val,desc,src_str,'bool'))
		if invert_bool: ret = not ret
	else:
		try:
			ret = type(refval)((val,not val)[invert_bool])
		except:
			die(1,"'{}': invalid value for '{}'{} (must be of type '{}')".format(
				val,desc,src_str,type(refval).__name__))
	return ret

# From 'man dd':
# c=1, w=2, b=512, kB=1000, K=1024, MB=1000*1000, M=1024*1024,
# GB=1000*1000*1000, G=1024*1024*1024, and so on for T, P, E, Z, Y.

def parse_bytespec(nbytes):
	smap = (('c',   1),
			('w',   2),
			('b',   512),
			('kB',  1000),
			('K',   1024),
			('MB',  1000*1000),
			('M',   1024*1024),
			('GB',  1000*1000*1000),
			('G',   1024*1024*1024),
			('TB',  1000*1000*1000*1000),
			('T',   1024*1024*1024*1024))
	import re
	m = re.match(r'([0123456789.]+)(.*)',nbytes)
	if m:
		if m.group(2):
			for k,v in smap:
				if k == m.group(2):
					from decimal import Decimal
					return int(Decimal(m.group(1)) * v)
			else:
				msg("Valid byte specifiers: '{}'".format("' '".join([i[0] for i in smap])))
		elif '.' in nbytes:
			raise ValueError('fractional bytes not allowed')
		else:
			return int(nbytes)

	die(1,"'{}': invalid byte specifier".format(nbytes))

def check_or_create_dir(path):
	try:
		os.listdir(path)
	except:
		try:
			os.makedirs(path,0o700)
		except:
			die(2,"ERROR: unable to read or create path '{}'".format(path))

from mmgen.opts import opt

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

def suf(arg,suf_type='s'):
	suf_types = { 's': '', 'es': '', 'ies': 'y' }
	assert suf_type in suf_types,'invalid suffix type'
	if isinstance(arg,int):
		n = arg
	elif isinstance(arg,(list,tuple,set,dict)):
		n = len(arg)
	else:
		die(2,'{}: invalid parameter for suf()'.format(arg))
	return suf_types[suf_type] if n == 1 else suf_type

def get_extension(f):
	a,b = os.path.splitext(f)
	return ('',b[1:])[len(b) > 1]

def remove_extension(f,e):
	a,b = os.path.splitext(f)
	return (f,a)[len(b)>1 and b[1:]==e]

def make_chksum_N(s,nchars,sep=False):
	if isinstance(s,str): s = s.encode()
	if nchars%4 or not (4 <= nchars <= 64): return False
	s = sha256(sha256(s).digest()).hexdigest().upper()
	sep = ('',' ')[bool(sep)]
	return sep.join([s[i*4:i*4+4] for i in range(nchars//4)])

def make_chksum_8(s,sep=False):
	from mmgen.obj import HexStr
	s = HexStr(sha256(sha256(s).digest()).hexdigest()[:8].upper(),case='upper')
	return '{} {}'.format(s[:4],s[4:]) if sep else s
def make_chksum_6(s):
	from mmgen.obj import HexStr
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
	tv = time.gmtime(t)[:6]
	return '{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}'.format(*tv)

def make_timestr(secs=None):
	t = int(secs) if secs else time.time()
	tv = time.gmtime(t)[:6]
	return '{:04d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}'.format(*tv)

def secs_to_dhms(secs):
	dsecs = secs//3600
	return '{}{:02d}:{:02d}:{:02d}'.format(
		('','{} day{}, '.format(dsecs//24,suf(dsecs//24)))[dsecs > 24],
		dsecs % 24, (secs//60) % 60, secs % 60)

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

# https://en.wikipedia.org/wiki/Base32#RFC_4648_Base32_alphabet
# https://tools.ietf.org/html/rfc4648
def is_hex_str(s):    return set(list(s.lower())) <= set(list(hexdigits.lower()))
def is_hex_str_lc(s): return set(list(s))         <= set(list(hexdigits.lower()))
def is_hex_str_uc(s): return set(list(s))         <= set(list(hexdigits.upper()))
def is_b58_str(s):    return set(list(s))         <= set(baseconv.digits['b58'])
def is_b32_str(s):    return set(list(s))         <= set(baseconv.digits['b32'])

def is_ascii(s,enc='ascii'):
	try:    s.decode(enc)
	except: return False
	else:   return True

def is_utf8(s): return is_ascii(s,enc='utf8')

class baseconv(object):

	mn_base = 1626 # tirosh list is 1633 words long!
	mn_ids = ('mmgen','tirosh')
	digits = {
		'b58': tuple('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'),
		'b32': tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'),
		'b16': tuple('0123456789abcdef'),
		'b10': tuple('0123456789'),
		'b8':  tuple('01234567'),
	}
	wl_chksums = {
		'mmgen':  '5ca31424',
		'tirosh': '48f05e1f', # tirosh truncated to mn_base (1626)
		# 'tirosh1633': '1a5faeff'
	}
	seed_pad_lens = {
		'b58': { 16:22, 24:33, 32:44 },
	}
	seed_pad_lens_rev = {
		'b58': { 22:16, 33:24, 44:32 },
	}

	@classmethod
	def init_mn(cls,mn_id):
		assert mn_id in cls.mn_ids
		if mn_id == 'mmgen':
			from mmgen.mn_electrum import words
			cls.digits[mn_id] = words
		elif mn_id == 'tirosh':
			from mmgen.mn_tirosh import words
			cls.digits[mn_id] = words[:cls.mn_base]
		else: # bip39
			cls.digits[mn_id] = cls.words

	@classmethod
	def get_wordlist(cls,wl_id):
		cls.init_mn(wl_id)
		return cls.digits[wl_id]

	@classmethod
	def get_wordlist_chksum(cls,wl_id):
		cls.init_mn(wl_id)
		return sha256(' '.join(cls.digits[wl_id]).encode()).hexdigest()[:8]

	@classmethod
	def check_wordlists(cls):
		for k,v in list(cls.wl_chksums.items()):
			res = cls.get_wordlist_chksum(k)
			assert res == v,'{}: checksum mismatch for {} (should be {})'.format(res,k,v)

	@classmethod
	def check_wordlist(cls,wl_id):
		cls.init_mn(wl_id)

		wl = cls.digits[wl_id]
		qmsg('Wordlist: {}\nLength: {} words'.format(wl_id,len(wl)))
		new_chksum = cls.get_wordlist_chksum(wl_id)

		a,b = 'generated','saved'
		compare_chksums(new_chksum,a,cls.wl_chksums[wl_id],b,die_on_fail=True)

		qmsg('List is sorted') if tuple(sorted(wl)) == wl else die(3,'ERROR: List is not sorted!')

	@classmethod
	def get_pad(cls,pad,seed_pad_func):
		"""
		'pad' argument to baseconv conversion methods must be either None, 'seed' or an integer.
		If None, output of minimum (but never zero) length will be produced.
		If 'seed', output length will be mapped from input length using data in seed_pad_lens.
		If an integer, the string, hex string or byte output will be padded to this length.
		"""
		if pad == None:
			return 0
		elif type(pad) == int:
			return pad
		elif pad == 'seed':
			return seed_pad_func()
		else:
			m = "{!r}: illegal value for 'pad' (must be None,'seed' or int)"
			raise BaseConversionPadError(m.format(pad))

	@classmethod
	def tohex(cls,words_arg,wl_id,pad=None):
		"convert string or list data of base 'wl_id' to hex string"
		return cls.tobytes(words_arg,wl_id,pad//2 if type(pad)==int else pad).hex()

	@classmethod
	def tobytes(cls,words_arg,wl_id,pad=None):
		"convert string or list data of base 'wl_id' to byte string"

		words = words_arg if isinstance(words_arg,(list,tuple)) else tuple(words_arg.strip())

		if len(words) == 0:
			raise BaseConversionError('empty {} data'.format(wl_id))

		def get_seed_pad():
			assert wl_id in cls.seed_pad_lens_rev,'seed padding not supported for base {!r}'.format(wl_id)
			d = cls.seed_pad_lens_rev[wl_id]
			if not len(words) in d:
				m = '{}: invalid length for seed-padded {} data in base conversion'
				raise BaseConversionError(m.format(len(words),wl_id))
			return d[len(words)]

		pad_val = max(cls.get_pad(pad,get_seed_pad),1)
		wl = cls.digits[wl_id]
		base = len(wl)

		if not set(words) <= set(wl):
			m = ('{w!r}:','seed data')[pad=='seed'] + ' not in {i} (base{b}) format'
			raise BaseConversionError(m.format(w=words_arg,i=wl_id,b=base))

		ret = sum([wl.index(words[::-1][i])*(base**i) for i in range(len(words))])
		bl = ret.bit_length()
		return ret.to_bytes(max(pad_val,bl//8+bool(bl%8)),'big')

	@classmethod
	def fromhex(cls,hexstr,wl_id,pad=None,tostr=False):
		"convert hex string to list or string data of base 'wl_id'"

		if not is_hex_str(hexstr):
			m = ('{h!r}:','seed data')[pad=='seed'] + ' not a hexadecimal string'
			raise HexadecimalStringError(m.format(h=hexstr))

		return cls.frombytes(bytes.fromhex(hexstr),wl_id,pad,tostr)

	@classmethod
	def frombytes(cls,bytestr,wl_id,pad=None,tostr=False):
		"convert byte string to list or string data of base 'wl_id'"

		if not bytestr:
			raise BaseConversionError('empty data not allowed in base conversion')

		def get_seed_pad():
			assert wl_id in cls.seed_pad_lens,'seed padding not supported for base {!r}'.format(wl_id)
			d = cls.seed_pad_lens[wl_id]
			if not len(bytestr) in d:
				m = '{}: invalid seed byte length for seed-padded base conversion'
				raise SeedLengthError(m.format(len(bytestr)))
			return d[len(bytestr)]

		pad = max(cls.get_pad(pad,get_seed_pad),1)
		wl = cls.digits[wl_id]
		base = len(wl)

		num = int.from_bytes(bytestr,'big')
		ret = []
		while num:
			ret.append(num % base)
			num //= base
		o = [wl[n] for n in [0] * (pad-len(ret)) + ret[::-1]]
		return ''.join(o) if tostr else o

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

def pretty_hexdump(data,gw=2,cols=8,line_nums=False):
	r = (0,1)[bool(len(data) % gw)]
	return ''.join(
		[
			('' if (line_nums == False or i % cols) else '{:06x}: '.format(i*gw)) +
				data[i*gw:i*gw+gw].hex() + ('\n',' ')[bool((i+1) % cols)]
					for i in range(len(data)//gw + r)
		]
	).rstrip() + '\n'

def decode_pretty_hexdump(data):
	from string import hexdigits
	pat = r'^[{}]+:\s+'.format(hexdigits)
	lines = [re.sub(pat,'',l) for l in data.splitlines()]
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
	from mmgen.seed import SeedSource
	if not SeedSource.ext_to_type(get_extension(fn)):
		raise BadFileExtension("'{}': unrecognized seed source file extension".format(fn))
def make_full_path(outdir,outfile):
	return os.path.normpath(os.path.join(outdir, os.path.basename(outfile)))

def get_seed_file(cmd_args,nargs,invoked_as=None):
	from mmgen.filename import find_file_in_dir
	from mmgen.seed import Wallet

	wf = find_file_in_dir(Wallet,g.data_dir)

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

def get_new_passphrase(desc,passchg=False):

	w = '{}passphrase for {}'.format(('','new ')[bool(passchg)], desc)
	if opt.passwd_file:
		pw = ' '.join(get_words_from_file(opt.passwd_file,w))
	elif opt.echo_passphrase:
		pw = ' '.join(get_words_from_user('Enter {}: '.format(w)))
	else:
		from mmgen.common import mswin_pw_warning
		mswin_pw_warning()
		for i in range(g.passwd_max_tries):
			pw = ' '.join(get_words_from_user('Enter {}: '.format(w)))
			pw2 = ' '.join(get_words_from_user('Repeat passphrase: '))
			dmsg('Passphrases: [{}] [{}]'.format(pw,pw2))
			if pw == pw2:
				vmsg('Passphrases match'); break
			else: msg('Passphrases do not match.  Try again.')
		else:
			die(2,'User failed to duplicate passphrase in {} attempts'.format(g.passwd_max_tries))

	if pw == '': qmsg('WARNING: Empty passphrase')
	return pw

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

		sys.stdout.write(data.decode() if isinstance(data,bytes) else data)

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
		from mmgen.crypto import mmgen_decrypt_retry
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

def pwfile_reuse_warning():
	if 'passwd_file_used' in globals():
		qmsg("Reusing passphrase from file '{}' at user request".format(opt.passwd_file))
		return True
	globals()['passwd_file_used'] = True
	return False

def get_mmgen_passphrase(desc,passchg=False):
	prompt ='Enter {}passphrase for {}: '.format(('','old ')[bool(passchg)],desc)
	if opt.passwd_file:
		pwfile_reuse_warning()
		return ' '.join(get_words_from_file(opt.passwd_file,'passphrase'))
	else:
		from mmgen.common import mswin_pw_warning
		mswin_pw_warning()
		return ' '.join(get_words_from_user(prompt))

def my_raw_input(prompt,echo=True,insert_txt='',use_readline=True):

	try: import readline
	except: use_readline = False # Windows

	if use_readline and sys.stdout.isatty():
		def st_hook(): readline.insert_text(insert_txt)
		readline.set_startup_hook(st_hook)
	else:
		msg_r(prompt)
		prompt = ''

	from mmgen.term import kb_hold_protect
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

	from mmgen.term import get_char

	q = ('(y/N)','(Y/n)')[bool(default_yes)]
	p = prompt if complete_prompt else '{} {}: '.format(prompt,q)
	nl = ('\n','\r{}\r'.format(' '*len(p)))[no_nl]

	if opt.accept_defaults:
		msg(p)
		return default_yes

	while True:
		r = get_char(p).strip(b'\n\r')
		if not r:
			if default_yes: msg_r(nl); return True
			else:           msg_r(nl); return False
		elif r in b'yY': msg_r(nl); return True
		elif r in b'nN': msg_r(nl); return False
		else:
			if verbose: msg('\nInvalid reply')
			else: msg_r('\r')

def prompt_and_get_char(prompt,chars,enter_ok=False,verbose=False):

	from mmgen.term import get_char

	while True:
		reply = get_char('{}: '.format(prompt)).strip(b'\n\r')

		if reply in chars.encode() or (enter_ok and not reply):
			msg('')
			return reply.decode()

		if verbose: msg('\nInvalid reply')
		else: msg_r('\r')

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
			from subprocess import run
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

	if opt.quiet or g.no_license or opt.yes or not g.stdin_tty: return

	import mmgen.license as gpl

	p = "Press 'w' for conditions and warranty info, or 'c' to continue:"
	msg(gpl.warning)
	prompt = '{} '.format(p.strip())

	from mmgen.term import get_char

	while True:
		reply = get_char(prompt, immed_chars=('','wc')[bool(immed)])
		if reply == b'w':
			do_pager(gpl.conditions)
		elif reply == b'c':
			msg(''); break
		else:
			msg_r('\r')
	msg('')

def get_daemon_cfg_options(cfg_keys):
	cfg_file = os.path.join(g.proto.daemon_data_dir,g.proto.name+'.conf')
	try:
		lines = get_lines_from_file(cfg_file,'',silent=bool(opt.quiet))
		kv_pairs = [l.split('=') for l in lines]
		cfg = {k:v for k,v in kv_pairs if k in cfg_keys}
	except:
		vmsg("Warning: '{}' does not exist or is unreadable".format(cfg_file))
		cfg = {}
	for k in set(cfg_keys) - set(cfg.keys()): cfg[k] = ''
	return cfg

def get_coin_daemon_auth_cookie():
	f = os.path.join(g.proto.daemon_data_dir,g.proto.daemon_data_subdir,'.cookie')
	return get_lines_from_file(f,'')[0] if file_is_readable(f) else ''

def rpc_init(reinit=False):
	if not 'rpc' in g.proto.mmcaps:
		die(1,'Coin daemon operations not supported for coin {}!'.format(g.coin))
	if g.rpch != None and not reinit: return g.rpch
	from mmgen.rpc import init_daemon
	g.rpch = init_daemon(g.proto.daemon_family)
	return g.rpch

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

# module loading magic for tx.py and tw.py
def altcoin_subclass(cls,mod_id,cls_name):
	if cls.__name__ != cls_name: return cls
	mod_dir = g.proto.base_coin.lower()
	pname = g.proto.class_pfx if hasattr(g.proto,'class_pfx') else capfirst(g.proto.name)
	tname = 'Token' if g.token else ''
	import importlib
	modname = 'mmgen.altcoins.{}.{}'.format(mod_dir,mod_id)
	clsname = '{}{}{}'.format(pname,tname,cls_name)
	try:
		return getattr(importlib.import_module(modname),clsname)
	except ImportError:
		return cls

# decorator for TrackingWallet
def write_mode(orig_func):
	def f(self,*args,**kwargs):
		if self.mode != 'w':
			m = '{} opened in read-only mode: cannot execute method {}()'
			die(1,m.format(type(self).__name__,locals()['orig_func'].__name__))
		return orig_func(self,*args,**kwargs)
	return f
