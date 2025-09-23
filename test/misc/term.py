#!/usr/bin/env python3

import sys, os
pn = os.path.abspath(os.path.dirname(sys.argv[0]))
parpar = os.path.dirname(os.path.dirname(pn))
os.chdir(parpar)
sys.path[0] = os.curdir

from mmgen.cfg import Config, gc
from mmgen.color import yellow, blue, cyan, set_vt100
from mmgen.util import msg, ymsg, gmsg, fmt, fmt_list, die

commands = [
	'start',
	'get_terminal_size',
	'color',
	'license',
	'line_input',
	'urand',
	'txview',
	'get_char_one',
	'get_char_one_raw',
]

match sys.platform:
	case 'linux' | 'darwin':
		commands.extend([
			'get_char',
			'get_char_immed_chars',
			'get_char_raw',
		])
	case 'win32':
		commands.extend([
			'get_char_one_char_immed_chars',
		])

opts_data = {
	'text': {
		'desc': 'Interactively test MMGen terminal functionality',
		'usage': 'command',
		'options': """
-h, --help     Print this help message
""",
	'notes': f"""
available commands for platform {sys.platform!r}:
{fmt_list(commands, fmt='col', indent='    ')}
"""
	}
}

cfg = Config(opts_data=opts_data)

from mmgen.term import get_char_raw, get_terminal_size, get_term
from mmgen.ui import line_input, keypress_confirm, do_license_msg
import mmgen.term as term_mod

def cmsg(m):
	msg('\n'+cyan(m))

def confirm(m):
	if not keypress_confirm(cfg, m):
		if keypress_confirm(cfg, 'Are you sure you want to exit test?'):
			die(1, 'Exiting test at user request')
		else:
			msg('Continuing...')

def tt_start():
	m = fmt("""
		We will now test MMGen Wallet’s terminal capabilities.
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
	do_license_msg(cfg)

def tt_line_input():
	set_vt100()
	cmsg('Testing line_input():')
	msg(fmt("""
		At the Ready? prompt type and hold down "y".
		Then Enter some text, followed by held-down ENTER.
		The held-down "y" and ENTER keys should be blocked, not affecting the output
		on screen or entered text.
	"""))
	get_char_raw('Ready? ', num_bytes=1)
	reply = line_input(cfg, '\nEnter text: ')
	confirm(f'Did you enter the text {reply!r}?')

def _tt_get_char(raw=False, one_char=False, immed_chars=''):
	funcname = ('get_char', 'get_char_raw')[raw]
	fs = fmt("""
		Press some keys in quick succession.
		{}{}
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
	if sys.platform == 'win32':
		if raw:
			m3 = 'The Escape and F1-F12 keys will be returned as two-character strings.'
		else:
			m3 = 'The Escape and F1-F12 keys will be returned as single characters.'
	kwargs = {}
	if one_char:
		kwargs.update({'num_bytes':1})
	if immed_chars:
		kwargs.update({'immed_chars':immed_chars})

	cmsg('Testing {}({}):'.format(
		funcname,
		','.join(f'{a}={b!r}' for a, b in kwargs.items())
	))
	msg(fs.format(m1, yellow(m2), yellow(m3)))

	try:
		while True:
			ret = getattr(term_mod, funcname)('Enter a letter: ', **kwargs)
			msg(f'You typed {ret!r}')
	except KeyboardInterrupt:
		msg('\nDone')

def tt_urand():
	cmsg('Testing _get_random_data_from_user():')
	from mmgen.crypto import Crypto
	ret = Crypto(cfg)._get_random_data_from_user(uchars=10, desc='data').decode()
	msg(f'USER ENTROPY (user input + keystroke timings):\n\n{fmt(ret, "  ")}')
	times = ret.splitlines()[1:]
	avg_prec = sum(len(t.split('.')[1]) for t in times) // len(times)
	if avg_prec < gc.min_time_precision:
		ymsg(f'WARNING: Avg. time precision of only {avg_prec} decimal points.  User entropy quality is degraded!')
	else:
		msg(f'Average time precision: {avg_prec} decimal points - OK')
	line_input(cfg, 'Press ENTER to continue: ')

def tt_txview():
	cmsg('Testing tx.info.view_with_prompt() (try each viewing option)')
	from mmgen.tx import UnsignedTX
	fn = 'test/ref/0B8D5A[15.31789,14,tl=1320969600].rawtx'
	tx = UnsignedTX(cfg=cfg, filename=fn, quiet_open=True)
	while True:
		tx.info.view_with_prompt('View data for transaction?', pause=False)
		set_vt100()
		if not keypress_confirm(cfg, 'Continue testing transaction view?', default_yes=True):
			break

def tt_get_char_one():
	_tt_get_char(one_char=True)

def tt_get_char_one_raw():
	_tt_get_char(one_char=True, raw=True)

def tt_get_char():
	_tt_get_char(one_char=False)

def tt_get_char_immed_chars():
	_tt_get_char(one_char=False, immed_chars='asdf')

def tt_get_char_raw():
	_tt_get_char(one_char=False, raw=True)

def tt_get_char_one_char_immed_chars():
	_tt_get_char(one_char=True, immed_chars='asdf')

get_term().register_cleanup()

if cfg._args:
	locals()['tt_'+cfg._args[0]]()
else:
	for command in commands:
		locals()['tt_'+command]()

gmsg('\nTest completed')
