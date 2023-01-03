#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
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
fileutil: Routines that read, write, execute or stat files
"""

import sys,os

from .globalvars import g
from .color import set_vt100
from .util import (
	msg,
	qmsg,
	dmsg,
	die,
	get_extension,
	is_utf8,
	capfirst,
	make_full_path,
	strip_comments,
)

def check_or_create_dir(path):
	try:
		os.listdir(path)
	except:
		if os.getenv('MMGEN_TEST_SUITE'):
			from subprocess import run
			run([
				('rm' if g.platform == 'win' else '/bin/rm'),
				'-rf',
				path ])
			set_vt100()
		try:
			os.makedirs(path,0o700)
		except:
			die(2,f'ERROR: unable to read or create path {path!r}')

def check_binary(args):
	from subprocess import run,DEVNULL
	try:
		run(args,stdout=DEVNULL,stderr=DEVNULL,check=True)
	except:
		die(2,f'{args[0]!r} binary missing, not in path, or not executable')
	set_vt100()

def shred_file(fn,verbose=False):
	check_binary(['shred','--version'])
	from subprocess import run
	run(
		['shred','--force','--iterations=30','--zero','--remove=wipesync']
		+ (['--verbose'] if verbose else [])
		+ [fn],
		check=True )
	set_vt100()

def _check_file_type_and_access(fname,ftype,blkdev_ok=False):

	import stat

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
		die( 'FileNotFound', f'Requested {ftype} {fname!r} not found' )

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
	return _check_file_type_and_access(f,'input file',blkdev_ok=blkdev_ok)

def check_outfile(f,blkdev_ok=False):
	return _check_file_type_and_access(f,'output file',blkdev_ok=blkdev_ok)

def check_outdir(f):
	return _check_file_type_and_access(f,'output directory')

def get_seed_file(cmd_args,nargs,invoked_as=None):

	from .opts import opt
	from .filename import find_file_in_dir
	from .wallet.mmgen import wallet

	wf = find_file_in_dir(wallet,g.data_dir)

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

def _open_or_die(filename,mode,silent=False):
	try:
		return open(filename,mode)
	except:
		die(2,'' if silent else
			'Unable to open file {!r} for {}'.format(
				({0:'STDIN',1:'STDOUT',2:'STDERR'}[filename] if type(filename) == int else filename),
				('reading' if 'r' in mode else 'writing')
			))

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

	from .opts import opt

	if quiet:
		ask_tty = ask_overwrite = False

	if opt.quiet:
		ask_overwrite = False

	if ask_write_default_yes == False or ask_write_prompt:
		ask_write = True

	def do_stdout():
		qmsg('Output to STDOUT requested')
		if g.stdin_tty:
			if no_tty:
				die(2,f'Printing {desc} to screen is not allowed')
			if (ask_tty and not opt.quiet) or binary:
				from .ui import confirm_or_raise
				confirm_or_raise(
					message = '',
					action  = f'output {desc} to screen' )
		else:
			try:    of = os.readlink(f'/proc/{os.getpid()}/fd/1') # Linux
			except: of = None # Windows

			if of:
				if of[:5] == 'pipe:':
					if no_tty:
						die(2,f'Writing {desc} to pipe is not allowed')
					if ask_tty and not opt.quiet:
						from .ui import confirm_or_raise
						confirm_or_raise(
							message = '',
							action  = f'output {desc} to pipe' )
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
			from .ui import keypress_confirm
			if not keypress_confirm(ask_write_prompt,
						default_yes=ask_write_default_yes):
				die(1,f'{capfirst(desc)} not saved')

		hush = False
		if os.path.lexists(outfile) and ask_overwrite:
			from .ui import confirm_or_raise
			confirm_or_raise(
				message = '',
				action  = f'File {outfile!r} already exists\nOverwrite?' )
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
					die(3,f'{desc} in file {outfile!r} has been altered by some other program! Aborting file write')

		# To maintain portability, always open files in binary mode
		# If 'binary' option not set, encode/decode data before writing and after reading
		try:
			with _open_or_die(outfile,'wb') as fp:
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

def get_words_from_file(infile,desc,quiet=False):

	if not quiet:
		qmsg(f'Getting {desc} from file {infile!r}')

	with _open_or_die(infile, 'rb') as fp:
		data = fp.read()

	try:
		words = data.decode().split()
	except:
		die(1,f'{capfirst(desc)} data must be UTF-8 encoded.')

	dmsg('Sanitized input: [{}]'.format(' '.join(words)))

	return words

def get_data_from_file(infile,desc='data',dash=False,silent=False,binary=False,quiet=False):

	from .opts import opt
	if not (opt.quiet or silent or quiet):
		qmsg(f'Getting {desc} from file {infile!r}')

	with _open_or_die(
			(0 if dash and infile == '-' else infile),
			'rb',
			silent=silent) as fp:
		data = fp.read(g.max_input_size+1)

	if not binary:
		data = data.decode()

	if len(data) == g.max_input_size + 1:
		die( 'MaxInputSizeExceeded',
			f'Too much input data!  Max input data size: {f.max_input_size} bytes' )

	return data

def _mmgen_decrypt_file_maybe(fn,desc='data',quiet=False,silent=False):
	d = get_data_from_file(fn,desc=desc,binary=True,quiet=quiet,silent=silent)
	from .crypto import mmenc_ext
	have_enc_ext = get_extension(fn) == mmenc_ext
	if have_enc_ext or not is_utf8(d):
		m = ('Attempting to decrypt','Decrypting')[have_enc_ext]
		qmsg(f'{m} {desc} {fn!r}')
		from .crypto import mmgen_decrypt_retry
		d = mmgen_decrypt_retry(d,desc)
	return d

def get_lines_from_file(fn,desc='data',trim_comments=False,quiet=False,silent=False):
	dec = _mmgen_decrypt_file_maybe(fn,desc=desc,quiet=quiet,silent=silent)
	ret = dec.decode().splitlines()
	if trim_comments:
		ret = strip_comments(ret)
	dmsg(f'Got {len(ret)} lines from file {fn!r}')
	return ret
