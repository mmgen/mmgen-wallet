#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2016 Philemon <mmgen-py@yandex.com>
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

# If 88- or 256-color support is compiled, the following apply.
#    P s = 3 8 ; 5 ; P s -> Set foreground color to the second P s .
#    P s = 4 8 ; 5 ; P s -> Set background color to the second P s .
if os.environ['TERM'][-8:] == '256color':
	_blk,_red,_grn,_yel,_blu,_mag,_cya,_bright,_dim,_ybright,_ydim,_pnk,_orng,_gry = [
	'\033[38;5;%s;1m' % c for c in 232,210,121,229,75,90,122,231,245,187,243,218,215,246]
	_redbg = '\033[38;5;232;48;5;210;1m'
	_grnbg = '\033[38;5;232;48;5;121;1m'
	_grybg = '\033[38;5;231;48;5;240;1m'
	_reset = '\033[0m'
else:
	_blk,_red,_grn,_yel,_blu,_mag,_cya,_reset,_grnbg = \
		['\033[%sm' % c for c in '30;1','31;1','32;1','33;1','34;1','35;1','36;1','0','30;102']
	_gry = _orng = _pnk = _redbg = _ybright = _ydim = _bright = _dim = _grybg = _mag  # TODO

def red(s):     return _red+s+_reset
def green(s):   return _grn+s+_reset
def grnbg(s):   return _grnbg+s+_reset
def yellow(s):  return _yel+s+_reset
def cyan(s):    return _cya+s+_reset
def blue(s):    return _blu+s+_reset
def pink(s):    return _pnk+s+_reset
def orange(s):  return _orng+s+_reset
def gray(s):    return _gry+s+_reset
def magenta(s): return _mag+s+_reset
def nocolor(s): return s

def msg(s):    sys.stderr.write(s+'\n')
def msg_r(s):  sys.stderr.write(s)
def Msg(s):    sys.stdout.write(s + '\n')
def Msg_r(s):  sys.stdout.write(s)
def msgred(s): sys.stderr.write(red(s+'\n'))
def mmsg(*args):
	for d in args:
		sys.stdout.write(repr(d)+'\n')
def mdie(*args):
	for d in args:
		sys.stdout.write(repr(d)+'\n')
	sys.exit()

def die(ev=0,s=''):
	assert type(ev) == int
	if s: sys.stderr.write(s+'\n')
	sys.exit(ev)
def Die(ev=0,s=''):
	assert type(ev) == int
	if s: sys.stdout.write(s+'\n')
	sys.exit(ev)

def pp_format(d):
	import pprint
	return pprint.PrettyPrinter(indent=4).pformat(d)

def pp_die(d):
	import pprint
	die(1,pprint.PrettyPrinter(indent=4).pformat(d))

def pp_msg(d):
	import pprint
	msg(pprint.PrettyPrinter(indent=4).pformat(d))

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

from mmgen.opts import opt

def qmsg(s,alt=False):
	if opt.quiet:
		if alt != False: sys.stderr.write(alt + '\n')
	else: sys.stderr.write(s + '\n')
def qmsg_r(s,alt=False):
	if opt.quiet:
		if alt != False: sys.stderr.write(alt)
	else: sys.stderr.write(s)
def vmsg(s):
	if opt.verbose: sys.stderr.write(s + '\n')
def vmsg_r(s):
	if opt.verbose: sys.stderr.write(s)
def Vmsg(s):
	if opt.verbose: sys.stdout.write(s + '\n')
def Vmsg_r(s):
	if opt.verbose: sys.stdout.write(s)
def dmsg(s):
	if opt.debug: sys.stdout.write(s + '\n')

def suf(arg,suf_type):
	t = type(arg)
	if t == int:
		n = arg
	elif t in (list,tuple,set,dict):
		n = len(arg)
	else:
		msg('%s: invalid parameter' % arg)
		return ''

	if suf_type in ('a','es'): return ('es','')[n == 1]
	if suf_type in ('k','s'):  return ('s','')[n == 1]

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
	s = sha256(sha256(s).digest()).hexdigest()[:8].upper()
	return '{} {}'.format(s[:4],s[4:]) if sep else s
def make_chksum_6(s): return sha256(s).hexdigest()[:6]
def is_chksum_6(s): return len(s) == 6 and is_hexstring_lc(s)

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

def _is_whatstring(s,chars):
	return set(list(s)) <= set(chars)

def is_int(s):
	try:
		int(s)
		return True
	except:
		return False

def is_hexstring(s):
	return _is_whatstring(s.lower(),hexdigits.lower())
def is_hexstring_lc(s):
	return _is_whatstring(s,hexdigits.lower())
def is_hexstring_uc(s):
	return _is_whatstring(s,hexdigits.upper())
def is_b58string(s):
	from mmgen.bitcoin import b58a
	return _is_whatstring(s,b58a)

def is_utf8(s):
	try: s.decode('utf8')
	except: return False
	else: return True

def is_ascii(s):
	try: s.decode('ascii')
	except: return False
	else: return True

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
	if g.platform == 'win':
		global red,green,yellow,cyan,nocolor
		import os
		if 'MMGEN_NOMSCOLOR' in os.environ:
			red = green = yellow = cyan = grnbg = nocolor
		else:
			try:
				import colorama
				colorama.init(strip=True,convert=True)
			except:
				red = green = yellow = cyan = grnbg = nocolor

def get_hash_params(hash_preset):
	if hash_preset in g.hash_presets:
		return g.hash_presets[hash_preset] # N,p,r,buflen
	else: # Shouldn't be here
		die(3,"%s: invalid 'hash_preset' value" % hash_preset)

def compare_chksums(chk1, desc1, chk2, desc2, hdr='', die_on_fail=False):

	if not chk1 == chk2:
		m = "%s ERROR: %s checksum (%s) doesn't match %s checksum (%s)"\
				% ((hdr+':\n   ' if hdr else 'CHECKSUM'),desc2,chk2,desc1,chk1)
		if die_on_fail:
			die(3,m)
		else:
			vmsg(m)
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


def confirm_or_exit(message, question, expect='YES'):

	m = message.strip()
	if m: msg(m)

	a = question+'  ' if question[0].isupper() else \
			'Are you sure you want to %s?\n' % question
	b = "Type uppercase '%s' to confirm: " % expect

	if my_raw_input(a+b).strip() != expect:
		die(2,'Exiting at user request')


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

	if opt.stdout or not sys.stdout.isatty() or outfile in ('','-'):
		qmsg('Output to STDOUT requested')
		if sys.stdout.isatty():
			if no_tty:
				die(2,'Printing %s to screen is not allowed' % desc)
			if ask_tty and not opt.quiet:
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
	else:
		if opt.outdir: outfile = make_full_path(opt.outdir,outfile)

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
	if have_enc_ext or not is_ascii(d):
		m = ('Attempting to decrypt','Decrypting')[have_enc_ext]
		msg("%s %s '%s'" % (m,desc,fn))
		from mmgen.crypto import mmgen_decrypt_retry
		d = mmgen_decrypt_retry(d,desc)
	return d

def get_lines_from_file(fn,desc='',trim_comments=False):
	dec = mmgen_decrypt_file_maybe(fn,desc)
	ret = dec.decode('utf8').splitlines() # DOS-safe
	return remove_comments(ret) if trim_comments else ret

def get_data_from_user(desc='data',silent=False):
	data = my_raw_input('Enter %s: ' % desc, echo=opt.echo_passphrase)
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
	if echo:
		reply = raw_input(prompt)
	else:
		from getpass import getpass
		reply = getpass(prompt)
	kb_hold_protect()

	return reply.strip()

def keypress_confirm(prompt,default_yes=False,verbose=False):

	from mmgen.term import get_char

	q = ('(y/N)','(Y/n)')[bool(default_yes)]

	while True:
		reply = get_char('%s %s: ' % (prompt, q)).strip('\n\r')

		if not reply:
			if default_yes: msg(''); return True
			else:           msg(''); return False
		elif reply in 'yY': msg(''); return True
		elif reply in 'nN': msg(''); return False
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

def do_license_msg(immed=False):

	if opt.quiet or g.no_license: return

	import mmgen.license as gpl

	p = "Press 'w' for conditions and warranty info, or 'c' to continue:"
	msg(gpl.warning)
	prompt = '%s ' % p.strip()

	from mmgen.term import get_char,do_pager

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

	f = os.path.join(g.bitcoin_data_dir,('',g.testnet_name)[g.testnet],
						('.','_')[g.platform=='win']+'cookie')

	if file_is_readable(f):
		return get_lines_from_file(f,'')[0]
	else:
		return ''

def bitcoin_connection():

	port = (8332,18332)[g.testnet]
	host,user,passwd = g.rpc_host,'rpcuser','rpcpassword'
	cfg = get_bitcoind_cfg_options((user,passwd))
	auth_cookie = get_bitcoind_auth_cookie()

	import mmgen.rpc
	c = mmgen.rpc.BitcoinRPCConnection(
				host,port,cfg[user],cfg[passwd],auth_cookie=auth_cookie)
	c.client_version = int(c.getinfo()['version'])
	return c
