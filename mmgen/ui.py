#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
ui: Interactive user interface functions for the MMGen suite
"""

import sys, os

from .util import msg, msg_r, Msg, die

def confirm_or_raise(cfg, message, action, expect='YES', exit_msg='Exiting at user request'):
	if message:
		msg(message)
	if line_input(
			cfg,
			(f'{action}  ' if action[0].isupper() else f'Are you sure you want to {action}?\n') +
			f'Type uppercase {expect!r} to confirm: '
		).strip() != expect:
		die('UserNonConfirmation', exit_msg)

def get_words_from_user(cfg, prompt):
	words = line_input(cfg, prompt, echo=cfg.echo_passphrase).split()
	if cfg.debug:
		msg('Sanitized input: [{}]'.format(' '.join(words)))
	return words

def get_data_from_user(cfg, desc='data'): # user input MUST be UTF-8
	data = line_input(cfg, f'Enter {desc}: ', echo=cfg.echo_passphrase)
	if cfg.debug:
		msg(f'User input: [{data}]')
	return data

def line_input(cfg, prompt, echo=True, insert_txt='', hold_protect=True):
	"""
	multi-line prompts OK
	one-line prompts must begin at beginning of line
	empty prompts forbidden due to interactions with readline
	"""
	assert prompt, 'calling line_input() with an empty prompt forbidden'

	def get_readline():
		try:
			import readline
			return readline
		except ImportError:
			return False

	if hold_protect:
		from .term import kb_hold_protect
		kb_hold_protect()

	if cfg.test_suite_popen_spawn:
		msg(prompt)
		sys.stderr.flush() # required by older Pythons (e.g. v3.7)
		reply = os.read(0, 4096).decode().rstrip('\n') # strip NL to mimic behavior of input()
	elif not sys.stdin.isatty():
		msg_r(prompt)
		reply = input('')
	elif echo:
		readline = get_readline()
		if readline and insert_txt:
			readline.set_startup_hook(lambda: readline.insert_text(insert_txt))
		reply = input(prompt)
		if readline and insert_txt:
			readline.set_startup_hook(lambda: readline.insert_text(''))
	else:
		from getpass import getpass
		reply = getpass(prompt)

	if hold_protect:
		kb_hold_protect()

	return reply.strip()

def keypress_confirm(
	cfg,
	prompt,
	default_yes     = False,
	verbose         = False,
	no_nl           = False,
	complete_prompt = False):

	if not complete_prompt:
		prompt = '{} {}: '.format(prompt, '(Y/n)' if default_yes else '(y/N)')

	nl = f'\r{" "*len(prompt)}\r' if no_nl else '\n'

	if cfg.accept_defaults:
		msg(prompt)
		return default_yes

	from .term import get_char
	while True:
		reply = get_char(prompt, immed_chars='yYnN').strip('\n\r')
		if not reply:
			msg_r(nl)
			return default_yes
		elif reply in 'yYnN':
			msg_r(nl)
			return reply in 'yY'
		else:
			msg_r('\nInvalid reply\n' if verbose else '\r')

def do_pager(text):

	pagers = ['less', 'more']
	end_msg = '\n(end of text)\n\n'
	os.environ['LESS'] = '--jump-target=2 --shift=4 --tabs=4 --RAW-CONTROL-CHARS --chop-long-lines'

	if 'PAGER' in os.environ and os.environ['PAGER'] != pagers[0]:
		pagers = [os.environ['PAGER']] + pagers

	from subprocess import run
	from .color import set_vt100
	for pager in pagers:
		try:
			m = text + ('' if pager == 'less' else end_msg)
			run([pager], input=m.encode(), check=True)
			msg_r('\r')
		except:
			pass
		else:
			break
	else:
		Msg(text+end_msg)
	set_vt100()

def do_license_msg(cfg, immed=False):

	if cfg.quiet or cfg.no_license or cfg.yes or not cfg.stdin_tty:
		return

	from .contrib import license as gpl
	from .cfg import gc
	msg(gpl.warning.format(gc=gc))

	from .term import get_char
	prompt = "Press 'w' for conditions and warranty info, or 'c' to continue: "
	while True:
		reply = get_char(prompt, immed_chars=('', 'wc')[bool(immed)])
		if reply == 'w':
			do_pager(gpl.conditions)
		elif reply == 'c':
			msg('')
			break
		else:
			msg_r('\r')
	msg('')
