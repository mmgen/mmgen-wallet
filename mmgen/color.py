#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
color.py:  color handling for the MMGen suite
"""

_colors = {
	'black':       (  232,      (30,0) ),
	'red':         (  210,      (31,1) ),
	'green':       (  121,      (32,1) ),
	'yellow':      (  229,      (33,1) ),
	'blue':        (  75,       (34,1) ),
	'magenta':     (  205,      (35,1) ),
	'cyan':        (  122,      (36,1) ),
	'pink':        (  218,      (35,1) ),
	'orange':      (  216,      (31,1) ),
	'gray':        (  246,      (30,1) ),
	'purple':      (  141,      (35,1) ),

	'brown':       (  208,      (33,0) ),
	'grndim':      (  108,      (32,0) ),
	'redbg':       ( (232,210), (30,101) ),
	'grnbg':       ( (232,121), (30,102) ),
	'blubg':       ( (232,75),  (30,104) ),
	'yelbg':       ( (232,229), (30,103) ),
}

def nocolor(s):
	return s

def set_vt100():
	'hack to put term into VT100 mode under MSWin'
	from .globalvars import g
	if g.platform == 'win':
		from subprocess import run
		run([],shell=True)

def get_terminfo_colors(term=None):
	from subprocess import run,PIPE
	cmd = ['infocmp','-0']
	if term:
		cmd.append(term)

	def is_hex_str(s):
		from string import hexdigits
		return set(list(s)) <= set(list(hexdigits))

	try:
		cmdout = run(cmd,stdout=PIPE,check=True).stdout.decode()
	except:
		return None
	else:
		s = [e.split('#')[1] for e in cmdout.split(',') if e.startswith('colors')][0]
		if s.isdecimal():
			return int(s)
		elif s.startswith('0x') and is_hex_str(s[2:]):
			return int(s[2:],16)
		else:
			return None

def init_color(num_colors='auto'):
	assert num_colors in ('auto',8,16,256,0)

	if num_colors == 'auto':
		import os
		t = os.getenv('TERM')
		num_colors = 256 if (t and t.endswith('256color')) or get_terminfo_colors() == 256 else 16

	reset = '\033[0m'
	if num_colors == 0:
		ncc = (lambda s: s).__code__
		for c in _colors:
			globals()[c].__code__ = ncc
	elif num_colors == 256:
		for c,e in _colors.items():
			start = (
				'\033[38;5;{};1m'.format(e[0]) if type(e[0]) == int else
				'\033[38;5;{};48;5;{};1m'.format(*e[0]) )
			globals()[c].__code__ = eval(f'(lambda s: "{start}" + s + "{reset}").__code__')
	elif num_colors in (8,16):
		for c,e in _colors.items():
			start = (
				'\033[{}m'.format(e[1][0]) if e[1][1] == 0 else
				'\033[{};{}m'.format(*e[1]) )
			globals()[c].__code__ = eval(f'(lambda s: "{start}" + s + "{reset}").__code__')

	set_vt100()

for _c in _colors:
	exec(f'{_c} = lambda s: s')
