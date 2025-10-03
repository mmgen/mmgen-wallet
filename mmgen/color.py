#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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
color: color handling for the MMGen suite
"""

_colors = {
	'black':   (232,        (30, 0)),
	'red':     (210,        (31, 1)),
	'green':   (121,        (32, 1)),
	'yellow':  (229,        (33, 1)),
	'blue':    (75,         (34, 1)),
	'magenta': (205,        (35, 1)),
	'cyan':    (122,        (36, 1)),

	'gray':    (246,        (30, 1)),
	'orange':  (216,        (31, 1)),
	'purple':  (141,        (35, 1)),
	'pink':    (218,        (35, 1)),

	'melon':   (222,        (33, 1)),
	'brown':   (173,        (33, 0)),
	'grndim':  (108,        (32, 0)),

	'redbg':   ((232, 210), (30, 101)),
	'grnbg':   ((232, 121), (30, 102)),
	'yelbg':   ((232, 229), (30, 103)),
	'blubg':   ((232, 75),  (30, 104)),
}

def nocolor(s):
	return s

def set_vt100():
	'hack to put term into VT100 mode under MSWin'
	import sys
	if sys.platform == 'win32':
		from subprocess import run
		run([], shell=True)

def get_terminfo_colors(term=None):
	from subprocess import run, PIPE
	cmd = ['infocmp', '-0']
	if term:
		cmd.append(term)

	try:
		cmdout = run(cmd, stdout=PIPE, check=True, text=True).stdout
	except:
		set_vt100()
		return None
	else:
		set_vt100()
		s = [e.split('#')[1] for e in cmdout.split(',') if e.startswith('colors')][0]
		from .util import is_hex_str
		if s.isdecimal():
			return int(s)
		elif s.startswith('0x') and is_hex_str(s[2:]):
			return int(s[2:], 16)
		else:
			return None

def init_color(num_colors='auto'):
	assert num_colors in ('auto', 8, 16, 256, 0)

	import sys
	self = sys.modules[__name__]

	if num_colors == 'auto':
		import os
		if sys.platform == 'win32':
			# Force 256-color for MSYS2: terminal supports it, however infocmp reports 8-color.
			# We also avoid spawning a subprocess, leading to a subsequent OSError 22 when testing
			# with pexpect spawn.
			num_colors = 256
		elif (t := os.getenv('TERM')) and t.endswith('256color'):
			num_colors = 256
		else:
			num_colors = get_terminfo_colors() or 16

	reset = '\033[0m'
	match num_colors:
		case 0:
			ncc = (lambda s: s).__code__
			for c in _colors:
				getattr(self, c).__code__ = ncc
		case 256:
			for c, e in _colors.items():
				start = (
					'\033[38;5;{};1m'.format(e[0]) if type(e[0]) == int else
					'\033[38;5;{};48;5;{};1m'.format(*e[0]))
				getattr(self, c).__code__ = eval(f'(lambda s: "{start}" + s + "{reset}").__code__')
		case 8 | 16:
			for c, e in _colors.items():
				start = (
					'\033[{}m'.format(e[1][0]) if e[1][1] == 0 else
					'\033[{};{}m'.format(*e[1]))
				getattr(self, c).__code__ = eval(f'(lambda s: "{start}" + s + "{reset}").__code__')

	set_vt100()

# Each color name must be bound to an independent stub function with its own
# address in memory.  The names themselves must never be redefined, since other
# modules could import them before init_color() is run.  Instead, the code
# objects of their associated functions are manipulated by init_color() to
# enable/disable color.

black   = lambda s: s
red     = lambda s: s
green   = lambda s: s
yellow  = lambda s: s
blue    = lambda s: s
magenta = lambda s: s
cyan    = lambda s: s

gray    = lambda s: s
orange  = lambda s: s
purple  = lambda s: s
pink    = lambda s: s

melon   = lambda s: s
brown   = lambda s: s
grndim  = lambda s: s

redbg   = lambda s: s
grnbg   = lambda s: s
yelbg   = lambda s: s
blubg   = lambda s: s
