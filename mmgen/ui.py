#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
ui: Interactive user interface functions for the MMGen suite
"""

import sys,os

from .globalvars import g,gc
from .opts import opt
from .util import msg,msg_r,Msg,dmsg,die

def confirm_or_raise(message,action,expect='YES',exit_msg='Exiting at user request'):
	if message:
		msg(message)
	if line_input(
			(f'{action}  ' if action[0].isupper() else f'Are you sure you want to {action}?\n') +
			f'Type uppercase {expect!r} to confirm: '
		).strip() != expect:
		die( 'UserNonConfirmation', exit_msg )

def get_words_from_user(prompt):
	words = line_input(prompt, echo=opt.echo_passphrase).split()
	if g.debug:
		msg('Sanitized input: [{}]'.format(' '.join(words)))
	return words

def get_data_from_user(desc='data'): # user input MUST be UTF-8
	data = line_input(f'Enter {desc}: ',echo=opt.echo_passphrase)
	if g.debug:
		msg(f'User input: [{data}]')
	return data

def line_input(prompt,echo=True,insert_txt='',hold_protect=True):
	"""
	multi-line prompts OK
	one-line prompts must begin at beginning of line
	empty prompts forbidden due to interactions with readline
	"""
	assert prompt,'calling line_input() with an empty prompt forbidden'

	def get_readline():
		try:
			import readline
			return readline
		except ImportError:
			return False

	if not sys.stdout.isatty():
		msg_r(prompt)
		prompt = ''

	if hold_protect:
		from .term import kb_hold_protect
		kb_hold_protect()

	if g.test_suite_popen_spawn:
		msg(prompt)
		sys.stderr.flush()
		reply = os.read(0,4096).decode().rstrip('\n') # strip NL to mimic behavior of input()
	elif echo or not sys.stdin.isatty():
		readline = insert_txt and sys.stdin.isatty() and get_readline()
		if readline:
			readline.set_startup_hook(lambda: readline.insert_text(insert_txt))
		reply = input(prompt)
		if readline:
			readline.set_startup_hook(lambda: readline.insert_text(''))
	else:
		from getpass import getpass
		reply = getpass(prompt)

	if hold_protect:
		kb_hold_protect()

	return reply.strip()

def keypress_confirm(
	prompt,
	default_yes     = False,
	verbose         = False,
	no_nl           = False,
	complete_prompt = False ):

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
	os.environ['LESS'] = (('--shift 8 -RS'),('--shift 16 -RS'))[gc.platform=='win']

	if 'PAGER' in os.environ and os.environ['PAGER'] != pagers[0]:
		pagers = [os.environ['PAGER']] + pagers

	from subprocess import run
	from .color import set_vt100
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
	set_vt100()

def do_license_msg(immed=False):

	if opt.quiet or g.no_license or opt.yes or not g.stdin_tty:
		return

	import mmgen.contrib.license as gpl
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
