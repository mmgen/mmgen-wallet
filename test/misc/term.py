#!/usr/bin/env python3

import sys,os
pn = os.path.abspath(os.path.dirname(sys.argv[0]))
parpar = os.path.dirname(os.path.dirname(pn))
os.chdir(parpar)
sys.path[0] = os.curdir

from mmgen.common import *

opts_data = {
	'text': {
		'desc': 'Interactively test MMGen terminal functionality',
		'usage':'',
		'options': """
-h, --help     Print this help message
""",
	'notes': """
"""
	}
}
cmd_args = opts.init(opts_data)

from mmgen.term import get_char,get_char_raw,get_terminal_size
from mmgen.ui import line_input,keypress_confirm,do_license_msg
import mmgen.term as term_mod

def cmsg(m):
	msg('\n'+cyan(m))

def confirm(m):
	if not keypress_confirm(m):
		if keypress_confirm('Are you sure you want to exit test?'):
			die(1,'Exiting test at user request')
		else:
			msg('Continuing...')

def tt_start():
	m = fmt("""
		We will now test MMGen’s terminal capabilities.
		This is a non-automated test and requires user interaction.
		Continue?
	""")
	confirm(m.strip())

def tt_get_terminal_size():
	cmsg('Testing get_terminal_size():')
	msg('X' * get_terminal_size().width)
	confirm('Do the X’s exactly fill the width of the screen?')

def tt_color():
	cmsg('Testing color:')
	confirm(blue('THIS TEXT') + ' should be blue.  Is it?')

def tt_license():
	cmsg('Testing do_license_msg() with pager')
	ymsg('Press "w" to test the pager, then "c" to continue')
	do_license_msg()

def tt_line_input():
	cmsg('Testing line_input():')
	msg(fmt("""
		At the Ready? prompt type and hold down "y".
		Then Enter some text, followed by held-down ENTER.
		The held-down "y" and ENTER keys should be blocked, not affecting the output
		on screen or entered text.
	"""))
	get_char_raw('Ready? ',num_bytes=1)
	reply = line_input('\nEnter text: ')
	confirm(f'Did you enter the text {reply!r}?')

def tt_get_char(raw=False,one_char=False,immed_chars=''):
	funcname = ('get_char','get_char_raw')[raw]
	fs = fmt("""
		Press some keys in quick succession.
		{}{}{}
		{}
		When you’re finished, use Ctrl-C to exit.
		""").strip()
	m1 = (
		'You should experience a delay with quickly repeated entry.',
		'Your entry should be repeated back to you immediately.'
	)[raw]
	m2 = (
		'',
		f'\nThe characters {immed_chars!r} will be repeated immediately, the others with delay.'
	)[bool(immed_chars)]
	m3 = 'The F1-F12 keys will be ' + (
		'blocked entirely.'
			if one_char and not raw else
		"echoed AS A SINGLE character '\\x1b'."
			if one_char else
		'echoed as a FULL CONTROL SEQUENCE.'
	)
	if g.platform == 'win':
		m3 = 'The Escape and F1-F12 keys will be returned as single characters.'
	kwargs = {}
	if one_char:
		kwargs.update({'num_bytes':1})
	if immed_chars:
		kwargs.update({'immed_chars':immed_chars})

	cmsg('Testing {}({}):'.format(
		funcname,
		','.join(f'{a}={b!r}' for a,b in kwargs.items())
	))
	msg(fs.format( m1, yellow(m2), yellow(m3) ))

	try:
		while True:
			ret = getattr( term_mod, funcname )('Enter a letter: ',**kwargs)
			msg(f'You typed {ret!r}')
	except KeyboardInterrupt:
		msg('\nDone')

def tt_urand():
	cmsg('Testing _get_random_data_from_user():')
	from mmgen.crypto import _get_random_data_from_user
	ret = _get_random_data_from_user(10,desc='data').decode()
	msg(f'USER ENTROPY (user input + keystroke timings):\n\n{fmt(ret,"  ")}')
	times = ret.splitlines()[1:]
	avg_prec = sum(len(t.split('.')[1]) for t in times) // len(times)
	if avg_prec < g.min_time_precision:
		ymsg(f'WARNING: Avg. time precision of only {avg_prec} decimal points.  User entropy quality is degraded!')
	else:
		msg(f'Average time precision: {avg_prec} decimal points - OK')
	line_input('Press ENTER to continue: ')

def tt_txview():
	cmsg('Testing tx.info.view_with_prompt() (try each viewing option)')
	from mmgen.tx import UnsignedTX
	fn = 'test/ref/0B8D5A[15.31789,14,tl=1320969600].rawtx'
	tx = UnsignedTX(filename=fn,quiet_open=True)
	while True:
		tx.info.view_with_prompt('View data for transaction?',pause=False)
		set_vt100()
		if not keypress_confirm('Continue testing transaction view?',default_yes=True):
			break

term_mod.register_cleanup()

tt_start()

tt_get_terminal_size()
tt_color()
tt_license()
set_vt100()
tt_line_input()
tt_urand()
tt_txview()

tt_get_char(one_char=True)
tt_get_char(one_char=True,raw=True)

if g.platform == 'linux':
	tt_get_char(one_char=False)
	tt_get_char(one_char=False,immed_chars='asdf')
	tt_get_char(one_char=False,raw=True)
else:
	tt_get_char(one_char=True,immed_chars='asdf')

gmsg('\nTest completed')
