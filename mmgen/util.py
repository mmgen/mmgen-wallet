#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2017 Philemon <mmgen-py@yandex.com>
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
from binascii import hexlify,unhexlify
from string import hexdigits
from mmgen.color import *

def msg(s):    sys.stderr.write(s.encode('utf8') + '\n')
def msg_r(s):  sys.stderr.write(s.encode('utf8'))
def Msg(s):    sys.stdout.write(s.encode('utf8') + '\n')
def Msg_r(s):  sys.stdout.write(s.encode('utf8'))
def msgred(s): msg(red(s))
def ymsg(s):   msg(yellow(s))
def ymsg_r(s): msg_r(yellow(s))
def gmsg(s):   msg(green(s))
def gmsg_r(s): msg_r(green(s))

def mmsg(*args):
	for d in args: Msg(repr(d))
def mdie(*args):
	mmsg(*args); sys.exit(0)

def die_wait(delay,ev=0,s=''):
	assert type(delay) == int
	assert type(ev) == int
	if s: msg(s)
	time.sleep(delay)
	sys.exit(ev)
def die_pause(ev=0,s=''):
	assert type(ev) == int
	if s: msg(s)
	raw_input('Press ENTER to exit')
	sys.exit(ev)
def die(ev=0,s=''):
	assert type(ev) == int
	if s: msg(s)
	sys.exit(ev)
def Die(ev=0,s=''):
	assert type(ev) == int
	if s: Msg(s)
	sys.exit(ev)

def rdie(ev=0,s=''): die(ev,red(s))
def ydie(ev=0,s=''): die(ev,yellow(s))
def hi(): sys.stdout.write(yellow('hi'))

def pformat(d):
	import pprint
	return pprint.PrettyPrinter(indent=4).pformat(d)
def pmsg(*args):
	if not args: return
	Msg(pformat(args if len(args) > 1 else args[0]))
def pdie(*args):
	if not args: sys.exit(1)
	Die(1,(pformat(args if len(args) > 1 else args[0])))

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

def parse_nbytes(nbytes):
	import re
	m = re.match(r'([0123456789]+)(.*)',nbytes)
	smap = ('c',1),('w',2),('b',512),('kB',1000),('K',1024),('MB',1000*1000),\
			('M',1024*1024),('GB',1000*1000*1000),('G',1024*1024*1024)
	if m:
		if m.group(2):
			for k,v in smap:
				if k == m.group(2):
					return int(m.group(1)) * v
			else:
				msg("Valid byte specifiers: '%s'" % "' '".join([i[0] for i in smap]))
		else:
			return int(nbytes)

	die(1,"'%s': invalid byte specifier" % nbytes)

def check_or_create_dir(path):
	try:
		os.listdir(path)
	except:
		try:
			os.makedirs(path,0700)
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

def suf(arg,suf_type):
	suf_types = { 's':  ('s',''), 'es': ('es','') }
	assert suf_type in suf_types
	t = type(arg)
	if t == int:
		n = arg
	elif any(issubclass(t,c) for c in (list,tuple,set,dict)):
		n = len(arg)
	else:
		die(2,'%s: invalid parameter for suf()' % arg)
	return suf_types[suf_type][n==1]

def get_extension(f):
	a,b = os.path.splitext(f)
	return ('',b[1:])[len(b) > 1]

def remove_extension(f,e):
	a,b = os.path.splitext(f)
	return (f,a)[len(b)>1 and b[1:]==e]

def make_chksum_N(s,nchars,sep=False):
	if nchars%4 or not (4 <= nchars <= 64): return False
	s = sha256(sha256(s).digest()).hexdigest().upper()
	sep = ('',' ')[bool(sep)]
	return sep.join([s[i*4:i*4+4] for i in range(nchars/4)])

def make_chksum_8(s,sep=False):
	from mmgen.obj import HexStr
	s = HexStr(sha256(sha256(s).digest()).hexdigest()[:8].upper(),case='upper')
	return '{} {}'.format(s[:4],s[4:]) if sep else s
def make_chksum_6(s):
	from mmgen.obj import HexStr
	return HexStr(sha256(s).hexdigest()[:6])
def is_chksum_6(s): return len(s) == 6 and is_hex_str_lc(s)

def make_iv_chksum(s): return sha256(s).hexdigest()[:8].upper()

def splitN(s,n,sep=None):                      # always return an n-element list
	ret = s.split(sep,n-1)
	return ret + ['' for i in range(n-len(ret))]
def split2(s,sep=None): return splitN(s,2,sep) # always return a 2-element list
def split3(s,sep=None): return splitN(s,3,sep) # always return a 3-element list

def split_into_cols(col_wid,s):
	return ' '.join([s[col_wid*i:col_wid*(i+1)]
					for i in range(len(s)/col_wid+1)]).rstrip()

def capfirst(s): # different from str.capitalize() - doesn't downcase any uc in string
	return s if len(s) == 0 else s[0].upper() + s[1:]

def decode_timestamp(s):
# 	with open('/etc/timezone') as f:
# 		tz_save = f.read().rstrip()
	os.environ['TZ'] = 'UTC'
	ts = time.strptime(s,'%Y%m%d_%H%M%S')
	t = time.mktime(ts)
# 	os.environ['TZ'] = tz_save
	return int(t)

def make_timestamp(secs=None):
	t = int(secs) if secs else time.time()
	tv = time.gmtime(t)[:6]
	return '{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}'.format(*tv)

def make_timestr(secs=None):
	t = int(secs) if secs else time.time()
	tv = time.gmtime(t)[:6]
	return '{:04d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}'.format(*tv)

def secs_to_hms(secs):
	return '{:02d}:{:02d}:{:02d}'.format(secs/3600, (secs/60) % 60, secs % 60)

def secs_to_ms(secs):
	return '{:02d}:{:02d}'.format(secs/60, secs % 60)

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
	digits = {
		'electrum': tuple(__import__('mmgen.mn_electrum',fromlist=['words']).words.split()),
		'tirosh': tuple(__import__('mmgen.mn_tirosh',fromlist=['words']).words.split()[:mn_base]),
		'b58': tuple('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'),
		'b32': tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'),
		'b16': tuple('0123456789abcdef'),
		'b10': tuple('0123456789'),
		'b8':  tuple('01234567'),
	}
	wl_chksums = {
		'electrum': '5ca31424',
		'tirosh':   '48f05e1f', # tirosh truncated to mn_base (1626)
		# 'tirosh1633': '1a5faeff'
	}
	b58pad_lens =     [(16,22), (24,33), (32,44)]
	b58pad_lens_rev = [(v,k) for k,v in b58pad_lens]

	@classmethod
	def b58encode(cls,s,pad=None):
		pad = cls.get_pad(s,pad,'en',cls.b58pad_lens,[bytes])
		return ''.join(cls.fromhex(hexlify(s),'b58',pad=pad))

	@classmethod
	def b58decode(cls,s,pad=None):
		pad = cls.get_pad(s,pad,'de',cls.b58pad_lens_rev,[bytes,unicode])
		return unhexlify(cls.tohex(s,'b58',pad=pad*2 if pad else None))

	@staticmethod
	def get_pad(s,pad,op,pad_map,ok_types):
		m = "b58{}code() input must be one of {}, not '{}'"
		assert type(s) in ok_types, m.format(op,repr([t.__name__ for t in ok_types]),type(s).__name__)
		if pad:
			assert type(pad) == bool, "'pad' must be boolean type"
			d = dict(pad_map)
			assert len(s) in d, 'Invalid data length for b58{}code(pad=True)'.format(op)
			return d[len(s)]
		else:
			return None

	@classmethod
	def get_wordlist_chksum(cls,wl_id):
		return sha256(' '.join(cls.digits[wl_id])).hexdigest()[:8]

	@classmethod
	def check_wordlists(cls):
		for k,v in cls.wl_chksums.items(): assert cls.get_wordlist_chksum(k) == v

	@classmethod
	def check_wordlist(cls,wl_id):

		wl = baseconv.digits[wl_id]
		Msg('Wordlist: %s\nLength: %i words' % (capfirst(wl_id),len(wl)))
		new_chksum = cls.get_wordlist_chksum(wl_id)

		a,b = 'generated checksum','saved checksum'
		compare_chksums(new_chksum,a,cls.wl_chksums[wl_id],b,die_on_fail=True)

		Msg('Checksum %s matches' % new_chksum)
		Msg('List is sorted') if tuple(sorted(wl)) == wl else die(3,'ERROR: List is not sorted!')


	@classmethod
	def tohex(cls,words_arg,wl_id,pad=None):

		words = words_arg if type(words_arg) in (list,tuple) else tuple(words_arg.strip())

		wl = cls.digits[wl_id]
		base = len(wl)

		if not set(words) <= set(wl):
			die(2,'{} is not in {} (base{}) format'.format(repr(words_arg),wl_id,base))

		deconv =  [wl.index(words[::-1][i])*(base**i) for i in range(len(words))]
		ret = ('{:0{w}x}'.format(sum(deconv),w=pad or 0))
		return ('','0')[len(ret) % 2] + ret

	@classmethod
	def fromhex(cls,hexnum,wl_id,pad=None):

		hexnum = hexnum.strip()
		if not is_hex_str(hexnum):
			die(2,"'%s': not a hexadecimal number" % hexnum)

		wl = cls.digits[wl_id]
		base = len(wl)
		num,ret = int(hexnum,16),[]
		while num:
			ret.append(num % base)
			num /= base
		return [wl[n] for n in [0] * ((pad or 0)-len(ret)) + ret[::-1]]

baseconv.check_wordlists()

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

def pretty_hexdump(data,gw=2,cols=8,line_nums=False):
	r = (0,1)[bool(len(data) % gw)]
	return ''.join(
		[
			('' if (line_nums == False or i % cols) else '{:06x}: '.format(i*gw)) +
				hexlify(data[i*gw:i*gw+gw]) + ('\n',' ')[bool((i+1) % cols)]
					for i in range(len(data)/gw + r)
		]
	).rstrip() + '\n'

def decode_pretty_hexdump(data):
	from string import hexdigits
	pat = r'^[%s]+:\s+' % hexdigits
	lines = [re.sub(pat,'',l) for l in data.splitlines()]
	try:
		return unhexlify(''.join((''.join(lines).split())))
	except:
		msg('Data not in hexdump format')
		return False

def strip_comments(line):
	return re.sub(ur'\s+$',u'',re.sub(ur'#.*',u'',line,1))

def remove_comments(lines):
	return [m for m in [strip_comments(l) for l in lines] if m != '']

from mmgen.globalvars import g

def start_mscolor():
	try:
		import colorama
		colorama.init(strip=True,convert=True)
	except:
		msg('Import of colorama module failed')

def get_hash_params(hash_preset):
	if hash_preset in g.hash_presets:
		return g.hash_presets[hash_preset] # N,p,r,buflen
	else: # Shouldn't be here
		die(3,"%s: invalid 'hash_preset' value" % hash_preset)

def compare_chksums(chk1,desc1,chk2,desc2,hdr='',die_on_fail=False,verbose=False):

	if not chk1 == chk2:
		m = "%s ERROR: %s checksum (%s) doesn't match %s checksum (%s)"\
				% ((hdr+':\n   ' if hdr else 'CHECKSUM'),desc2,chk2,desc1,chk1)
		if die_on_fail:
			die(3,m)
		else:
			vmsg(m,force=verbose)
			return False

	vmsg('%s checksum OK (%s)' % (capfirst(desc1),chk1))
	return True

def compare_or_die(val1, desc1, val2, desc2, e='Error'):
	if cmp(val1,val2):
		die(3,"%s: %s (%s) doesn't match %s (%s)"
				% (e,desc2,val2,desc1,val1))
	dmsg('%s OK (%s)' % (capfirst(desc2),val2))
	return True

def open_file_or_exit(filename,mode):
	try:
		f = open(filename, mode)
	except:
		op = ('writing','reading')['r' in mode]
		die(2,"Unable to open file '%s' for %s" % (filename,op))
	return f

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
		die(1,"Unable to stat requested %s '%s'" % (ftype,fname))

	for t in ok_types:
		if t[0](mode): break
	else:
		die(1,"Requested %s '%s' is not a %s" % (ftype,fname,
				' or '.join([t[1] for t in ok_types])))

	if not os.access(fname, access):
		die(1,"Requested %s '%s' is not %sable by you" % (ftype,fname,m))

	return True

def check_infile(f,blkdev_ok=False):
	return check_file_type_and_access(f,'input file',blkdev_ok=blkdev_ok)
def check_outfile(f,blkdev_ok=False):
	return check_file_type_and_access(f,'output file',blkdev_ok=blkdev_ok)
def check_outdir(f):
	return check_file_type_and_access(f,'output directory')
def make_full_path(outdir,outfile):
	return os.path.normpath(os.path.join(outdir, os.path.basename(outfile)))

def get_seed_file(cmd_args,nargs,invoked_as=None):
	from mmgen.filename import find_file_in_dir
	from mmgen.seed import Wallet
	if g.bob or g.alice:
		import regtest as rt
		wf = rt.mmwallet(('alice','bob')[g.bob])
	else:
		wf = find_file_in_dir(Wallet,g.data_dir)

	wd_from_opt = bool(opt.hidden_incog_input_params or opt.in_fmt) # have wallet data from opt?

	import mmgen.opts as opts
	if len(cmd_args) + (wd_from_opt or bool(wf)) < nargs:
		opts.usage()
	elif len(cmd_args) > nargs:
		opts.usage()
	elif len(cmd_args) == nargs and wf and invoked_as != 'gen':
		msg('Warning: overriding default wallet with user-supplied wallet')

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
		for i in range(g.passwd_max_tries):
			pw = ' '.join(get_words_from_user('Enter {}: '.format(w)))
			pw2 = ' '.join(get_words_from_user('Repeat passphrase: '))
			dmsg('Passphrases: [%s] [%s]' % (pw,pw2))
			if pw == pw2:
				vmsg('Passphrases match'); break
			else: msg('Passphrases do not match.  Try again.')
		else:
			die(2,'User failed to duplicate passphrase in %s attempts' %
					g.passwd_max_tries)

	if pw == '': qmsg('WARNING: Empty passphrase')
	return pw

def confirm_or_exit(message,question,expect='YES',exit_msg='Exiting at user request'):
	m = message.strip()
	if m: msg(m)
	a = question+'  ' if question[0].isupper() else \
			'Are you sure you want to %s?\n' % question
	b = "Type uppercase '%s' to confirm: " % expect
	if my_raw_input(a+b).strip() != expect:
		die(1,exit_msg)


# New function
def write_data_to_file(
		outfile,
		data,
		desc='data',
		ask_write=False,
		ask_write_prompt='',
		ask_write_default_yes=True,
		ask_overwrite=True,
		ask_tty=True,
		no_tty=False,
		silent=False,
		binary=False
	):

	if silent: ask_tty = ask_overwrite = False
	if opt.quiet: ask_overwrite = False

	if ask_write_default_yes == False or ask_write_prompt:
		ask_write = True

	if not binary and type(data) == unicode:
		data = data.encode('utf8')

	def do_stdout():
		qmsg('Output to STDOUT requested')
		if sys.stdout.isatty():
			if no_tty:
				die(2,'Printing %s to screen is not allowed' % desc)
			if (ask_tty and not opt.quiet) or binary:
				confirm_or_exit('','output %s to screen' % desc)
		else:
			try:    of = os.readlink('/proc/%d/fd/1' % os.getpid()) # Linux
			except: of = None # Windows

			if of:
				if of[:5] == 'pipe:':
					if no_tty:
						die(2,'Writing %s to pipe is not allowed' % desc)
					if ask_tty and not opt.quiet:
						confirm_or_exit('','output %s to pipe' % desc)
						msg('')
				of2,pd = os.path.relpath(of),os.path.pardir
				msg("Redirecting output to file '%s'" % (of2,of)[of2[:len(pd)] == pd])
			else:
				msg('Redirecting output to file')

		if binary and g.platform == 'win':
			import msvcrt
			msvcrt.setmode(sys.stdout.fileno(),os.O_BINARY)

		sys.stdout.write(data)

	def do_file(outfile,ask_write_prompt):
		if opt.outdir and not os.path.isabs(outfile):
			outfile = make_full_path(opt.outdir,outfile)

		if ask_write:
			if not ask_write_prompt: ask_write_prompt = 'Save %s?' % desc
			if not keypress_confirm(ask_write_prompt,
						default_yes=ask_write_default_yes):
				die(1,'%s not saved' % capfirst(desc))

		hush = False
		if file_exists(outfile) and ask_overwrite:
			q = "File '%s' already exists\nOverwrite?" % outfile
			confirm_or_exit('',q)
			msg("Overwriting file '%s'" % outfile)
			hush = True

		f = open_file_or_exit(outfile,('w','wb')[bool(binary)])
		try:
			f.write(data)
		except:
			die(2,"Failed to write %s to file '%s'" % (desc,outfile))
		f.close

		if not (hush or silent):
			msg("%s written to file '%s'" % (capfirst(desc),outfile))

		return True

	if opt.stdout or outfile in ('','-'):
		do_stdout()
	elif sys.stdin.isatty() and not sys.stdout.isatty():
		do_stdout()
	else:
		do_file(outfile,ask_write_prompt)

def get_words_from_user(prompt):
	# split() also strips
	words = my_raw_input(prompt, echo=opt.echo_passphrase).split()
	dmsg('Sanitized input: [%s]' % ' '.join(words))
	return words


def get_words_from_file(infile,desc,silent=False):
	if not silent:
		qmsg("Getting %s from file '%s'" % (desc,infile))
	f = open_file_or_exit(infile, 'r')
	# split() also strips
	words = f.read().split()
	f.close()
	dmsg('Sanitized input: [%s]' % ' '.join(words))
	return words


def get_words(infile,desc,prompt):
	if infile:
		return get_words_from_file(infile,desc)
	else:
		return get_words_from_user(prompt)

def mmgen_decrypt_file_maybe(fn,desc=''):
	d = get_data_from_file(fn,desc,binary=True)
	have_enc_ext = get_extension(fn) == g.mmenc_ext
	if have_enc_ext or not is_utf8(d):
		m = ('Attempting to decrypt','Decrypting')[have_enc_ext]
		msg("%s %s '%s'" % (m,desc,fn))
		from mmgen.crypto import mmgen_decrypt_retry
		d = mmgen_decrypt_retry(d,desc)
	return d

def get_lines_from_file(fn,desc='',trim_comments=False):
	dec = mmgen_decrypt_file_maybe(fn,desc)
	ret = dec.decode('utf8').splitlines() # DOS-safe
	if trim_comments: ret = remove_comments(ret)
	vmsg(u"Got {} lines from file '{}'".format(len(ret),fn))
	return ret

def get_data_from_user(desc='data',silent=False):
	p = ('','Enter {}: '.format(desc))[g.stdin_tty]
	data = my_raw_input(p,echo=opt.echo_passphrase)
	dmsg('User input: [%s]' % data)
	return data

def get_data_from_file(infile,desc='data',dash=False,silent=False,binary=False):
	if dash and infile == '-': return sys.stdin.read()
	if not silent and desc:
		qmsg("Getting %s from file '%s'" % (desc,infile))
	f = open_file_or_exit(infile,('r','rb')[bool(binary)])
	data = f.read()
	f.close()
	return data

def pwfile_reuse_warning():
	if 'passwd_file_used' in globals():
		qmsg("Reusing passphrase from file '%s' at user request" % opt.passwd_file)
		return True
	globals()['passwd_file_used'] = True
	return False

def get_mmgen_passphrase(desc,passchg=False):
	prompt ='Enter {}passphrase for {}: '.format(('','old ')[bool(passchg)],desc)
	if opt.passwd_file:
		pwfile_reuse_warning()
		return ' '.join(get_words_from_file(opt.passwd_file,'passphrase'))
	else:
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
	if echo or not sys.stdin.isatty():
		reply = raw_input(prompt.encode('utf8'))
	else:
		from getpass import getpass
		reply = getpass(prompt)
	kb_hold_protect()

	return reply.strip()

def keypress_confirm(prompt,default_yes=False,verbose=False,no_nl=False):

	from mmgen.term import get_char

	q = ('(y/N)','(Y/n)')[bool(default_yes)]
	p = '{} {}: '.format(prompt,q)
	nl = ('\n','\r{}\r'.format(' '*len(p)))[no_nl]

	while True:
		reply = get_char(p).strip('\n\r')
		if not reply:
			if default_yes: msg_r(nl); return True
			else:           msg_r(nl); return False
		elif reply in 'yY': msg_r(nl); return True
		elif reply in 'nN': msg_r(nl); return False
		else:
			if verbose: msg('\nInvalid reply')
			else: msg_r('\r')

def prompt_and_get_char(prompt,chars,enter_ok=False,verbose=False):

	from mmgen.term import get_char

	while True:
		reply = get_char('%s: ' % prompt).strip('\n\r')

		if reply in chars or (enter_ok and not reply):
			msg('')
			return reply

		if verbose: msg('\nInvalid reply')
		else: msg_r('\r')

def do_pager(text):

	pagers,shell = ['less','more'],False
	# --- Non-MSYS Windows code deleted ---
	# raw, chop, horiz scroll 8 chars, disable buggy line chopping in MSYS
	os.environ['LESS'] = (('--shift 8 -RS'),('-cR -#1'))[g.platform=='win']

	if 'PAGER' in os.environ and os.environ['PAGER'] != pagers[0]:
		pagers = [os.environ['PAGER']] + pagers

	text = text.encode('utf8')

	for pager in pagers:
		end = ('\n(end of text)\n','')[pager=='less']
		try:
			from subprocess import Popen,PIPE,STDOUT
			p = Popen([pager], stdin=PIPE, shell=shell)
		except: pass
		else:
			p.communicate(text+end+'\n')
			msg_r('\r')
			break
	else: Msg(text+end)

def do_license_msg(immed=False):

	if opt.quiet or g.no_license or opt.yes or not g.stdin_tty: return

	import mmgen.license as gpl

	p = "Press 'w' for conditions and warranty info, or 'c' to continue:"
	msg(gpl.warning)
	prompt = '%s ' % p.strip()

	from mmgen.term import get_char

	while True:
		reply = get_char(prompt, immed_chars=('','wc')[bool(immed)])
		if reply == 'w':
			do_pager(gpl.conditions)
		elif reply == 'c':
			msg(''); break
		else:
			msg_r('\r')
	msg('')

def get_bitcoind_cfg_options(cfg_keys):

	cfg_file = os.path.join(g.bitcoin_data_dir,'bitcoin.conf')

	cfg = dict([(k,v) for k,v in [split2(str(line).translate(None,'\t '),'=')
			for line in get_lines_from_file(cfg_file,'')] if k in cfg_keys]) \
				if file_is_readable(cfg_file) else {}

	for k in set(cfg_keys) - set(cfg.keys()): cfg[k] = ''

	return cfg

def get_bitcoind_auth_cookie():
	f = os.path.join(g.bitcoin_data_dir,('',g.testnet_name)[g.testnet],'.cookie')
	return get_lines_from_file(f,'')[0] if file_is_readable(f) else ''

def rpc_connection():

	def check_coin_mismatch(c):
		if c.getblockcount() == 0:
			msg('Warning: no blockchain, so skipping block mismatch check')
			return
		fb = '00000000000000000019f112ec0a9982926f1258cdcc558dd7c3b7e5dc7fa148'
		err = []
		if c.getblockchaininfo()['blocks'] <= 478558 or c.getblockhash(478559) == fb:
			if g.coin == 'BCH': err = 'BCH','BTC'
		elif g.coin == 'BTC': err = 'BTC','BCH'
		if err: ydie(2,"'{}' requested, but this is the {} chain!".format(*err))

	def check_chain_mismatch():
		err = None
		if g.regtest and g.chain != 'regtest':
			err = '--regtest option'
		elif g.testnet and g.chain == 'mainnet':
			err = '--testnet option'
		# we won't actually get here, as connect will fail first
		elif (not g.testnet) and g.chain != 'mainnet':
			err = 'mainnet'
		if err:
			die(1,'{} selected but chain is {}'.format(err,g.chain))

	cfg = get_bitcoind_cfg_options(('rpcuser','rpcpassword'))
	import mmgen.rpc
	c = mmgen.rpc.BitcoinRPCConnection(
				g.rpc_host or 'localhost',
				g.rpc_port or g.ports[g.coin][g.testnet],
				g.rpc_user or cfg['rpcuser'], # MMGen's rpcuser,rpcpassword override bitcoind's
				g.rpc_password or cfg['rpcpassword'],
				auth_cookie=get_bitcoind_auth_cookie())

	if not g.bitcoind_version: # First call
		if g.bob or g.alice:
			import regtest as rt
			rt.user(('alice','bob')[g.bob],quiet=True)
		g.bitcoind_version = int(c.getnetworkinfo()['version'])
		g.chain = c.getblockchaininfo()['chain']
		if g.chain != 'regtest':
			g.chain += 'net'
		assert g.chain in g.chains
		if g.chain == 'mainnet':
			check_coin_mismatch(c)
	return c
