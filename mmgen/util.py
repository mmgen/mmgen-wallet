#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2015 Philemon <mmgen-py@yandex.com>
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
util.py:  Low-level routines imported by other modules for the MMGen suite
"""

import sys,os,time,stat,re
from hashlib import sha256
from binascii import hexlify,unhexlify
from string import hexdigits

import mmgen.globalvars as g

pnm = g.proj_name

_red,_grn,_yel,_cya,_reset = \
	["\033[%sm" % c for c in "31;1","32;1","33;1","36;1","0"]

def red(s):     return _red+s+_reset
def green(s):   return _grn+s+_reset
def yellow(s):  return _yel+s+_reset
def cyan(s):    return _cya+s+_reset
def nocolor(s): return s

def start_mscolor():
	if sys.platform[:3] == "win":
		global red,green,yellow,cyan,nocolor
		import os
		if "MMGEN_NOMSCOLOR" in os.environ:
			red = green = yellow = cyan = nocolor
		else:
			try:
				import colorama
				colorama.init(strip=True,convert=True)
			except:
				red = green = yellow = cyan = nocolor

def msg(s):    sys.stderr.write(s+"\n")
def msg_r(s):  sys.stderr.write(s)
def Msg(s):    sys.stdout.write(s + "\n")
def Msg_r(s):  sys.stdout.write(s)
def msgred(s): sys.stderr.write(red(s+"\n"))
def mmsg(*args):
	for d in args:
		sys.stdout.write(repr(d)+"\n")
def mdie(*args):
	for d in args:
		sys.stdout.write(repr(d)+"\n")
	sys.exit()

def die(ev,s):
	sys.stderr.write(s+"\n"); sys.exit(ev)
def Die(ev,s):
	sys.stdout.write(s+"\n"); sys.exit(ev)

def is_mmgen_wallet_label(s):
	if len(s) > g.max_wallet_label_len:
		msg("ERROR: wallet label length (%s chars) > maximum allowed (%s chars)" % (len(s),g.max_wallet_label_len))
		return False

	try: s = s.decode("utf8")
	except: pass

	for ch in s:
		if ch not in g.wallet_label_symbols:
			msg("ERROR: wallet label contains illegal symbol (%s)" % ch)
			return False
	return True

# From "man dd":
# c=1, w=2, b=512, kB=1000, K=1024, MB=1000*1000, M=1024*1024,
# GB=1000*1000*1000, G=1024*1024*1024, and so on for T, P, E, Z, Y.

def parse_nbytes(nbytes):
	import re
	m = re.match(r'([0123456789]+)(.*)',nbytes)
	smap = ("c",1),("w",2),("b",512),("kB",1000),("K",1024),("MB",1000*1000),\
			("M",1024*1024),("GB",1000*1000*1000),("G",1024*1024*1024)
	if m:
		if m.group(2):
			for k,v in smap:
				if k == m.group(2):
					return int(m.group(1)) * v
			else:
				msg("Valid byte specifiers: '%s'" % "' '".join([i[0] for i in smap]))
		else:
			return int(nbytes)

	msg("'%s': invalid byte specifier" % nbytes)
	sys.exit(1)

import opt

def qmsg(s,alt=False):
	if opt.quiet:
		if alt != False: sys.stderr.write(alt + "\n")
	else: sys.stderr.write(s + "\n")
def qmsg_r(s,alt=False):
	if opt.quiet:
		if alt != False: sys.stderr.write(alt)
	else: sys.stderr.write(s)
def vmsg(s):
	if opt.verbose: sys.stderr.write(s + "\n")
def vmsg_r(s):
	if opt.verbose: sys.stderr.write(s)

def Vmsg(s):
	if opt.verbose: sys.stdout.write(s + "\n")
def Vmsg_r(s):
	if opt.verbose: sys.stdout.write(s)

def dmsg(s):
	if opt.debug: sys.stdout.write(s + "\n")

def suf(arg,suf_type):
	t = type(arg)
	if t == int:
		n = arg
	elif t == list or t == tuple or t == set:
		n = len(arg)
	else:
		msg("%s: invalid parameter" % arg)
		return ""

	if suf_type in ("a","es"):
		return "" if n == 1 else "es"
	if suf_type in ("k","s"):
		return "" if n == 1 else "s"

def get_extension(f):
	return os.path.splitext(f)[1][1:]

def make_chksum_N(s,nchars,sep=False):
	if nchars%4 or not (4 <= nchars <= 64): return False
	s = sha256(sha256(s).digest()).hexdigest().upper()
	sep = " " if sep else ""
	return sep.join([s[i*4:i*4+4] for i in range(nchars/4)])

def make_chksum_8(s,sep=False):
	s = sha256(sha256(s).digest()).hexdigest()[:8].upper()
	return "{} {}".format(s[:4],s[4:]) if sep else s
def make_chksum_6(s): return sha256(s).hexdigest()[:6]
def is_chksum_6(s): return len(s) == 6 and is_hexstring_lc(s)

def make_iv_chksum(s): return sha256(s).hexdigest()[:8].upper()

def splitN(s,n,sep=None):                      # always return an n-element list
	ret = s.split(sep,n-1)
	return ret + ["" for i in range(n-len(ret))]
def split2(s,sep=None): return splitN(s,2,sep) # always return a 2-element list
def split3(s,sep=None): return splitN(s,3,sep) # always return a 3-element list

def split_into_cols(col_wid,s):
	return " ".join([s[col_wid*i:col_wid*(i+1)]
					for i in range(len(s)/col_wid+1)]).rstrip()

def capfirst(s):
	return s if len(s) == 0 else \
		(s[0].upper() + (s[1:] if len(s) > 1 else ""))

def make_timestamp():
	tv = time.gmtime(time.time())[:6]
	return "{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(*tv)
def make_timestr():
	tv = time.gmtime(time.time())[:6]
	return "{:04d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}".format(*tv)
def secs_to_hms(secs):
	return "{:02d}:{:02d}:{:02d}".format(secs/3600, (secs/60) % 60, secs % 60)

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
	try: s.decode("utf8")
	except: return False
	else: return True

def match_ext(addr,ext):
	return addr.split(".")[-1] == ext

def file_exists(f):
	try:
		os.stat(f)
		return True
	except:
		return False

def get_from_brain_opt_params():
	l,p = opt.from_brain.split(",")
	return(int(l),p)

def pretty_hexdump(data,gw=2,cols=8,line_nums=False):
	r = 1 if len(data) % gw else 0
	return "".join(
		[
			("" if (line_nums == False or i % cols) else "{:06x}: ".format(i*gw)) +
			hexlify(data[i*gw:i*gw+gw]) +
			(" " if (i+1) % cols else "\n")
				for i in range(len(data)/gw + r)
		]
	).rstrip() + "\n"

def decode_pretty_hexdump(data):
	from string import hexdigits
	lines = [re.sub('^['+hexdigits+']+:\s+','',l) for l in data.split("\n")]
	try:
		return unhexlify("".join(("".join(lines).split())))
	except:
		msg("Data not in hexdump format")
		return False

def get_hash_params(hash_preset):
	if hash_preset in g.hash_presets:
		return g.hash_presets[hash_preset] # N,p,r,buflen
	else: # Shouldn't be here
		msg("%s: invalid 'hash_preset' value" % hash_preset)
		sys.exit(3)

def compare_chksums(chk1, desc1, chk2, desc2, hdr="", die_on_fail=False):

	if not chk1 == chk2:
		m = "%s ERROR: %s checksum (%s) doesn't match %s checksum (%s)"\
				% ((hdr+":\n   " if hdr else "CHECKSUM"),desc2,chk2,desc1,chk1)
		if die_on_fail:
			die(3,m)
		else:
			vmsg(m)
			return False

	vmsg("%s checksum OK (%s)" % (capfirst(desc1),chk1))
	return True

def compare_or_die(val1, desc1, val2, desc2, e="Error"):
	if cmp(val1,val2):
		die(3,"%s: %s (%s) doesn't match %s (%s)"
				% (e,desc2,val2,desc1,val1))
	dmsg("%s OK (%s)" % (capfirst(desc2),val2))
	return True

def get_default_wordlist():

	wl_id = g.default_wordlist
	if wl_id == "electrum": from mmgen.mn_electrum import words as wl
	elif wl_id == "tirosh": from mmgen.mn_tirosh   import words as wl
	return wl.strip().split("\n")

def open_file_or_exit(filename,mode):
	try:
		f = open(filename, mode)
	except:
		op = "reading" if 'r' in mode else "writing"
		msg("Unable to open file '%s' for %s" % (filename,op))
		sys.exit(2)
	return f


def check_file_type_and_access(fname,ftype,blkdev_ok=False):

	import os, stat

	a = ((os.R_OK,"read"),(os.W_OK,"writ"))
	access,m = a[int(ftype in ("output file","output directory"))]

	ok_types = [
		(stat.S_ISREG,"regular file"),
		(stat.S_ISLNK,"symbolic link")
	]
	if blkdev_ok: ok_types.append((stat.S_ISBLK,"block device"))
	if ftype == "output directory": ok_types = [(stat.S_ISDIR, "output directory")]

	try: mode = os.stat(fname).st_mode
	except:
		msg("Unable to stat requested %s '%s'" % (ftype,fname))
		sys.exit(1)

	for t in ok_types:
		if t[0](mode): break
	else:
		msg("Requested %s '%s' is not a %s" % (ftype,fname,
				" or ".join([t[1] for t in ok_types])))
		sys.exit(1)

	if not os.access(fname, access):
		msg("Requested %s '%s' is not %sable by you" % (ftype,fname,m))
		sys.exit(1)

	return True

def check_infile(f,blkdev_ok=False):
	return check_file_type_and_access(f,"input file",blkdev_ok=blkdev_ok)
def check_outfile(f,blkdev_ok=False):
	return check_file_type_and_access(f,"output file",blkdev_ok=blkdev_ok)
def check_outdir(f):  return check_file_type_and_access(f,"output directory")

def _validate_addr_num(n):

	try: n = int(n)
	except:
		msg("'%s': addr index must be an integer" % n)
		return False

	if n < 1:
		msg("'%s': addr index must be greater than zero" % n)
		return False

	return n


def make_full_path(outdir,outfile):
	return os.path.normpath(os.path.join(outdir, os.path.basename(outfile)))


def parse_addr_idxs(arg,sep=","):

	ret = []

	for i in (arg.split(sep)):

		j = i.split("-")

		if len(j) == 1:
			i = _validate_addr_num(i)
			if not i: return False
			ret.append(i)
		elif len(j) == 2:
			beg = _validate_addr_num(j[0])
			if not beg: return False
			end = _validate_addr_num(j[1])
			if not end: return False
			if end < beg:
				msg("'%s-%s': end of range less than beginning" % (beg,end))
				return False
			ret.extend(range(beg,end+1))
		else:
			msg("'%s': invalid argument for address range" % i)
			return False

	return sorted(set(ret))


def get_new_passphrase(desc,passchg=False):

	w = "{}passphrase for {}".format("new " if passchg else "", desc)
	if opt.passwd_file:
		pw = " ".join(get_words_from_file(opt.passwd_file,w))
	elif opt.echo_passphrase:
		pw = " ".join(get_words_from_user("Enter {}: ".format(w)))
	else:
		for i in range(g.passwd_max_tries):
			pw = " ".join(get_words_from_user("Enter {}: ".format(w)))
			pw2 = " ".join(get_words_from_user("Repeat passphrase: "))
			dmsg("Passphrases: [%s] [%s]" % (pw,pw2))
			if pw == pw2:
				vmsg("Passphrases match"); break
			else: msg("Passphrases do not match.  Try again.")
		else:
			msg("User failed to duplicate passphrase in %s attempts" %
					g.passwd_max_tries)
			sys.exit(2)

	if pw == "": qmsg("WARNING: Empty passphrase")
	return pw


def confirm_or_exit(message, question, expect="YES"):

	m = message.strip()
	if m: msg(m)

	a = question+"  " if question[0].isupper() else \
			"Are you sure you want to %s?\n" % question
	b = "Type uppercase '%s' to confirm: " % expect

	if my_raw_input(a+b).strip() != expect:
		die(2,"Exiting at user request")


def write_to_stdout(data, desc, ask_terminal=True):
	if sys.stdout.isatty() and ask_terminal:
		confirm_or_exit("",'output {} to screen'.format(desc))
	elif not sys.stdout.isatty():
		try:
			of = os.readlink("/proc/%d/fd/1" % os.getpid())
			of_maybe = os.path.relpath(of)
			of = of if of_maybe.find(os.path.pardir) == 0 else of_maybe
			msg("Redirecting output to file '%s'" % of)
		except:
			msg("Redirecting output to file")
	sys.stdout.write(data)

# New function
def write_data_to_file(
		outfile,
		data,
		desc="data",
		ask_write=False,
		ask_write_prompt="",
		ask_write_default_yes=False,
		ask_overwrite=True,
		ask_tty=True,
		no_tty=False,
		silent=False
	):
	if opt.stdout or not sys.stdout.isatty():
		qmsg("Output to STDOUT requested")
		write_ok = False
		if sys.stdout.isatty():
			if no_tty:
				die(2,"Printing %s to screen is not allowed" % desc)
			if ask_tty:
				confirm_or_exit("",'output %s to screen' % desc)
		else:
			try:    of = os.readlink("/proc/%d/fd/1" % os.getpid()) # Linux
			except: of = None # Windows

			if of:
				if of[:5] == "pipe:":
					if no_tty:
						die(2,"Writing %s to pipe is not allowed" % desc)
					if ask_tty:
						confirm_or_exit("",'output %s to pipe' % desc)
						msg("")
				of2,pd = os.path.relpath(of),os.path.pardir
				msg("Redirecting output to file '%s'" %
						(of if of2[:len(pd)] == pd else of2))
			else:
				msg("Redirecting output to file")

		sys.stdout.write(data)
	else:
		if opt.outdir: outfile = make_full_path(opt.outdir,outfile)

		if ask_write:
			if not keypress_confirm(ask_write_prompt,
						default_yes=ask_write_default_yes):
				die(1,"Exiting at user request")

		hush = False
		if file_exists(outfile):
			if ask_overwrite and not silent:
					q = "File '%s' already exists\nOverwrite?" % outfile
					confirm_or_exit("",q)
					msg("Overwriting file '%s'" % outfile)
			hush = True

		f = open_file_or_exit(outfile,'wb')
		try:
			f.write(data)
		except:
			if not silent: msg("Failed to write %s to file '%s'" % (desc,outfile))
			sys.exit(2)
		f.close

		if not hush:
			msg("%s written to file '%s'" % (capfirst(desc),outfile))

		return True


def write_to_file(
		outfile,
		data,
		desc="data",
		confirm_overwrite=False,
		verbose=False,
		silent=False,
		mode='wb'
	):

	if opt.outdir: outfile = make_full_path(opt.outdir,outfile)

	try:    os.stat(outfile)
	except: pass
	else:
		if confirm_overwrite:
			q = "File '%s' already exists\nOverwrite?" % outfile
			confirm_or_exit("",q)
		else:
			if not silent: msg("Overwriting file '%s'" % outfile)

	f = open_file_or_exit(outfile,mode)
	try:
		f.write(data)
	except:
		if not silent: msg("Failed to write %s to file '%s'" % (desc,outfile))
		sys.exit(2)
	f.close

	if verbose: msg("%s written to file '%s'" % (capfirst(desc),outfile))
	return True


def write_to_file_or_stdout(outfile, data,  desc="data"):

	if opt.stdout or not sys.stdout.isatty():
		write_to_stdout(data, desc)
	else:
		write_to_file(outfile,data,desc,not opt.quiet,True)


from mmgen.bitcoin import b58decode_pad,b58encode_pad

def display_control_data(label,metadata,hash_preset,salt,enc_seed):
	Msg("WALLET DATA")
	fs = "  {:18} {}"
	pw_empty = "yes" if metadata[3] == "E" else "no"
	for i in (
		("Label:",               label),
		("Seed ID:",             metadata[0].upper()),
		("Key  ID:",             metadata[1].upper()),
		("Seed length:",         "%s bits (%s bytes)" %
				(metadata[2],int(metadata[2])/8)),
		("Scrypt params:",  "Preset '%s' (%s)" % (hash_preset,
				" ".join([str(i) for i in get_hash_params(hash_preset)]))),
		("Passphrase empty?", pw_empty.capitalize()),
		("Timestamp:",           "%s UTC" % metadata[4]),
	): Msg(fs.format(*i))

	fs = "  {:6} {}"
	for i in (
		("Salt:",    ""),
		("  b58:",      b58encode_pad(salt)),
		("  hex:",      hexlify(salt)),
		("Encrypted seed:", ""),
		("  b58:",      b58encode_pad(enc_seed)),
		("  hex:",      hexlify(enc_seed))
	): Msg(fs.format(*i))


def write_wallet_to_file(seed, passwd, key_id, salt, enc_seed):

	seed_id = make_chksum_8(seed)
	seed_len = str(len(seed)*8)
	pw_status = "NE" if len(passwd) else "E"
	hash_preset = opt.hash_preset
	label = opt.label or "No Label"
	metadata = seed_id.lower(),key_id.lower(),seed_len,\
		pw_status,make_timestamp()
	sf  = b58encode_pad(salt)
	esf = b58encode_pad(enc_seed)

	lines = (
		label,
		"{} {} {} {} {}".format(*metadata),
		"{}: {} {} {}".format(hash_preset,*get_hash_params(hash_preset)),
		"{} {}".format(make_chksum_6(sf),  split_into_cols(4,sf)),
		"{} {}".format(make_chksum_6(esf), split_into_cols(4,esf))
	)

	chk = make_chksum_6(" ".join(lines))
	outfile="{}-{}[{},{}].{}".format(
		seed_id,key_id,seed_len,hash_preset,g.wallet_ext)

	d = "\n".join((chk,)+lines)+"\n"
	write_to_file(outfile,d,"wallet",not opt.quiet,True)

	if opt.debug:
		display_control_data(label,metadata,hash_preset,salt,enc_seed)


def _check_mmseed_format(words):

	valid = False
	desc = "%s data" % g.seed_ext
	try:
		chklen = len(words[0])
	except:
		return False

	if len(words) < 3 or len(words) > 12:
		msg("Invalid data length (%s) in %s" % (len(words),desc))
	elif not is_hexstring(words[0]):
		msg("Invalid format of checksum '%s' in %s"%(words[0], desc))
	elif chklen != 6:
		msg("Incorrect length of checksum (%s) in %s" % (chklen,desc))
	else: valid = True

	return valid


def _check_wallet_format(infile, lines):

	desc = "wallet file '%s'" % infile
	valid = False
	chklen = len(lines[0])
	if len(lines) != 6:
		vmsg("Invalid number of lines (%s) in %s" % (len(lines),desc))
	elif chklen != 6:
		vmsg("Incorrect length of Master checksum (%s) in %s" % (chklen,desc))
	elif not is_hexstring(lines[0]):
		vmsg("Invalid format of Master checksum '%s' in %s"%(lines[0], desc))
	else: valid = True

	if valid == False:
		msg("Invalid %s" % desc)
		sys.exit(2)


def _check_chksum_6(chk,val,desc,infile):
	comp_chk = make_chksum_6(val)
	if chk != comp_chk:
		msg("%s checksum incorrect in file '%s'!" % (desc,infile))
		msg("Checksum: %s. Computed value: %s" % (chk,comp_chk))
		sys.exit(2)
	dmsg("%s checksum passed: %s" % (capfirst(desc),chk))


def get_data_from_wallet(infile,silent=False):

	# Don't make this a qmsg: User will be prompted for passphrase and must see
	# the filename.
	if not silent and not opt.quiet:
		msg("Getting {pnm} wallet data from file '{f}'".format(pnm=pnm,f=infile))

	f = open_file_or_exit(infile, 'r')

	lines = [i.strip() for i in f.readlines()]
	f.close()

	_check_wallet_format(infile, lines)

	label = lines[1]

	metadata = lines[2].split()

	for i in 0,1: metadata[i] = metadata[i].upper()

	hd = lines[3].split()
	hash_preset = hd[0][:-1]
	hash_params = [int(i) for i in hd[1:]]

	if hash_params != get_hash_params(hash_preset):
		msg("Hash parameters '%s' don't match hash preset '%s'" %
				(" ".join(hash_params), hash_preset))
		sys.exit(9)

	res = {}
	for i,key in (4,"salt"),(5,"enc_seed"):
		l = lines[i].split()
		val = "".join(l[1:])
		_check_chksum_6(l[0], val, key, infile)
		res[key] = b58decode_pad(val)
		if res[key] == False:
			msg("Invalid b58 number: %s" % val)
			sys.exit(9)

	_check_chksum_6(lines[0], " ".join(lines[1:]), "Master", infile)

	return label,metadata,hash_preset,res['salt'],res['enc_seed']


def get_words_from_user(prompt):
	# split() also strips
	words = my_raw_input(prompt, echo=opt.echo_passphrase).split()
	dmsg("Sanitized input: [%s]" % " ".join(words))
	return words


def get_words_from_file(infile,desc,silent=False):
	if not silent:
		qmsg("Getting %s from file '%s'" % (desc,infile))
	f = open_file_or_exit(infile, 'r')
	# split() also strips
	words = f.read().split()
	f.close()
	dmsg("Sanitized input: [%s]" % " ".join(words))
	return words


def get_words(infile,desc,prompt):
	if infile:
		return get_words_from_file(infile,desc)
	else:
		return get_words_from_user(prompt)

def remove_comments(lines):
	# re.sub(pattern, repl, string, count=0, flags=0)
	ret = []
	for i in lines:
		i = re.sub('#.*','',i,1)
		i = re.sub('\s+$','',i)
		if i: ret.append(i)
	return ret

def get_lines_from_file(infile,desc="",trim_comments=False):
	if desc != "":
		qmsg("Getting %s from file '%s'" % (desc,infile))
	f = open_file_or_exit(infile,'r')
	lines = f.read().splitlines()
	f.close()
	return remove_comments(lines) if trim_comments else lines


def get_data_from_user(desc="data",silent=False):
	data = my_raw_input("Enter %s: " % desc, echo=opt.echo_passphrase)
	dmsg("User input: [%s]" % data)
	return data

def get_data_from_file(infile,desc="data",dash=False,silent=False):
	if dash and infile == "-": return sys.stdin.read()
	if not silent:
		qmsg("Getting %s from file '%s'" % (desc,infile))
	f = open_file_or_exit(infile,'rb')
	data = f.read()
	f.close()
	return data


def get_seed_from_seed_data(words):

	if not _check_mmseed_format(words):
		msg("Invalid %s data" % g.seed_ext)
		return False

	stored_chk = words[0]
	seed_b58 = "".join(words[1:])

	chk = make_chksum_6(seed_b58)
	vmsg_r("Validating %s checksum..." % g.seed_ext)

	if compare_chksums(chk, "seed", stored_chk, "input"):
		seed = b58decode_pad(seed_b58)
		if seed == False:
			msg("Invalid b58 number: %s" % val)
			return False

		msg("Valid seed data for seed ID %s" % make_chksum_8(seed))
		return seed
	else:
		msg("Invalid checksum for {pnm} seed".format(pnm=pnm))
		return False


passwd_file_used = False

def pwfile_reuse_warning():
	global passwd_file_used
	if passwd_file_used:
		qmsg("Reusing passphrase from file '%s' at user request" % opt.passwd_file)
		return True
	passwd_file_used = True
	return False


def get_mmgen_passphrase(desc,passchg=False):
	prompt ="Enter {}passphrase for {}: ".format("old " if passchg else "",desc)
	if opt.passwd_file:
		pwfile_reuse_warning()
		return " ".join(get_words_from_file(opt.passwd_file,"passphrase"))
	else:
		return " ".join(get_words_from_user(prompt))


def get_bitcoind_passphrase(prompt):
	if opt.passwd_file:
		pwfile_reuse_warning()
		return get_data_from_file(opt.passwd_file,
				"passphrase").strip("\r\n")
	else:
		return my_raw_input(prompt, echo=opt.echo_passphrase)


def check_data_fits_file_at_offset(fname,offset,dlen,action):
	# TODO: Check for Windows
	if stat.S_ISBLK(os.stat(fname).st_mode):
		fd = os.open(fname, os.O_RDONLY)
		fsize = os.lseek(fd, 0, os.SEEK_END)
		os.close(fd)
	else:
		fsize = os.stat(fname).st_size

	if fsize < offset + dlen:
		m = "Destination" if action == "write" else "Input"
		msg(
	"%s file has length %s, too short to %s %s bytes of data at offset %s"
			% (m,fsize,action,dlen,offset))
		sys.exit(1)


from mmgen.term import kb_hold_protect,get_char

def get_hash_preset_from_user(hp=g.hash_preset,desc="data"):
	p = """Enter hash preset for %s,
 or hit ENTER to accept the default value ('%s'): """ % (desc,hp)
	while True:
		ret = my_raw_input(p)
		if ret:
			if ret in g.hash_presets.keys(): return ret
			else:
				msg("Invalid input.  Valid choices are %s" %
						", ".join(sorted(g.hash_presets.keys())))
				continue
		else: return hp


def my_raw_input(prompt,echo=True,insert_txt="",use_readline=True):

	try: import readline
	except: use_readline = False # Windows

	if use_readline and sys.stdout.isatty():
		def st_hook(): readline.insert_text(insert_txt)
		readline.set_startup_hook(st_hook)
	else:
		msg_r(prompt)
		prompt = ""

	kb_hold_protect()
	if echo:
		reply = raw_input(prompt)
	else:
		from getpass import getpass
		reply = getpass(prompt)
	kb_hold_protect()

	return reply.strip()


def keypress_confirm(prompt,default_yes=False,verbose=False):

	q = "(Y/n)" if default_yes else "(y/N)"

	while True:
		reply = get_char("%s %s: " % (prompt, q)).strip("\n\r")

		if not reply:
			if default_yes: msg(""); return True
			else:           msg(""); return False
		elif reply in 'yY': msg(""); return True
		elif reply in 'nN': msg(""); return False
		else:
			if verbose: msg("\nInvalid reply")
			else: msg_r("\r")


def prompt_and_get_char(prompt,chars,enter_ok=False,verbose=False):

	while True:
		reply = get_char("%s: " % prompt).strip("\n\r")

		if reply in chars or (enter_ok and not reply):
			msg("")
			return reply

		if verbose: msg("\nInvalid reply")
		else: msg_r("\r")


def do_license_msg(immed=False):

	import mmgen.license as gpl
	if opt.quiet or g.no_license: return

	p = "Press 'w' for conditions and warranty info, or 'c' to continue:"
	msg(gpl.warning)
	prompt = "%s " % p.strip()

	while True:
		reply = get_char(prompt, immed_chars="wc" if immed else "")
		if reply == 'w':
			from mmgen.term import do_pager
			do_pager(gpl.conditions)
		elif reply == 'c':
			msg(""); break
		else:
			msg_r("\r")
	msg("")
