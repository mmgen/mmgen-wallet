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

def tt_my_raw_input():
	cmsg('Testing my_raw_input():')
	msg(fmt("""
		At the Ready? prompt type and hold down "y".
		Then Enter some text, followed by held-down ENTER.
		The held-down "y" and ENTER keys should be blocked, not affecting the output
		on screen or entered text.
	"""))
	get_char_raw('Ready? ',num_chars=1)
	reply = my_raw_input('\nEnter text: ')
	confirm('Did you enter the text {!r}?'.format(reply))

def tt_prompt_and_get_char():
	cmsg('Testing prompt_and_get_char():')
	m = 'Type some letters besides "x" or "z", then "x" or "z"'
	reply = prompt_and_get_char(m,'xz')
	confirm('Did you enter the letter {!r}?'.format(reply))

def tt_prompt_and_get_char_enter_ok():
	cmsg('Testing prompt_and_get_char() with blank choices and enter_ok=True:')
	for m in (
		'Type ENTER',
		'Type any letter followed by a pause, followed by ENTER',
	):
		reply = prompt_and_get_char(m,'',enter_ok=True)
		assert reply == ''
		msg('OK')

def tt_get_char(raw=False,one_char=False,sleep=0,immed_chars=''):
	fname = ('get_char','get_char_raw')[raw]
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
		'\nA delay of {} seconds will added before each prompt'.format(sleep)
	)[bool(sleep)]
	m3 = (
		'',
		'\nThe characters {!r} will be repeated immediately, the others with delay.'.format(immed_chars)
	)[bool(immed_chars)]
	m4 = 'The F1-F12 keys will be ' + (
		'blocked entirely.'
			if one_char and not raw else
		"echoed AS A SINGLE character '\\x1b'."
			if one_char else
		'echoed as a FULL CONTROL SEQUENCE.'
	)
	if g.platform == 'win':
		m4 = 'The Escape and F1-F12 keys will be returned as single characters.'
	kwargs = {}
	if one_char:
		kwargs.update({'num_chars':1})
	if sleep:
		kwargs.update({'sleep':sleep})
	if immed_chars:
		kwargs.update({'immed_chars':immed_chars})

	cmsg('Testing {}({}):'.format(fname,','.join(['{}={!r}'.format(*i) for i in kwargs.items()])))
	msg(fs.format(m1,yellow(m2),yellow(m3),yellow(m4)))

	try:
		while True:
			ret = globals()[fname]('Enter a letter: ',**kwargs)
			msg('You typed {!r}'.format(ret))
	except KeyboardInterrupt:
		msg('\nDone')

if g.platform == 'linux':
	import termios,atexit
	fd = sys.stdin.fileno()
	old = termios.tcgetattr(fd)
	atexit.register(lambda: termios.tcsetattr(fd,termios.TCSADRAIN,old))

tt_start()

tt_get_terminal_size()
tt_color()
tt_license()
tt_my_raw_input()
tt_prompt_and_get_char()
tt_prompt_and_get_char_enter_ok()

tt_get_char(one_char=True)
tt_get_char(one_char=True,sleep=1)
tt_get_char(one_char=True,raw=True)

if g.platform == 'linux':
	tt_get_char(one_char=False)
	tt_get_char(one_char=False,immed_chars='asdf')
	tt_get_char(one_char=False,raw=True)
else:
	tt_get_char(one_char=True,immed_chars='asdf')

gmsg('\nTest completed')
