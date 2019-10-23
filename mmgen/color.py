#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>
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

for _c in _colors:
	_e = _colors[_c]
	globals()['_256_'+_c]   = '\033[38;5;{};1m'.format(_e[0]) if type(_e[0]) == int \
						else '\033[38;5;{};48;5;{};1m'.format(*_e[0])
	globals()['_16_'+_c]    = '\033[{}m'.format(_e[1][0]) if _e[1][1] == 0 \
						else '\033[{};{}m'.format(*_e[1])
	globals()['_clr_'+_c] = ''; _reset = ''
	exec('def {c}(s): return _clr_{c}+s+_reset'.format(c=_c))

def nocolor(s): return s

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
	assert num_colors in ('auto',8,16,256)
	globals()['_reset'] = '\033[0m'

	import os
	t = os.getenv('TERM')
	if num_colors in (8,16):
		pfx = '_16_'
	elif num_colors == 256 or (t and t.endswith('256color')) or get_terminfo_colors() == 256:
		pfx = '_256_'
	else:
		pfx = '_16_'

	for c in _colors:
		globals()['_clr_'+c] = globals()[pfx+c]

def start_mscolor():
	import sys
	from mmgen.globalvars import g
	try:
		import colorama
		colorama.init(strip=True,convert=True)
	except:
		from mmgen.util import msg
		msg('Import of colorama module failed')
	else:
		g.stdout = sys.stdout
		g.stderr = sys.stderr
