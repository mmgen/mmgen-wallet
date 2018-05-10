#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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
	'magenta':     (  213,      (35,1) ),
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

for c in _colors:
	e = _colors[c]
	globals()['_256_'+c]   = '\033[38;5;{};1m'.format(e[0]) if type(e[0]) == int \
						else '\033[38;5;{};48;5;{};1m'.format(*e[0])
	globals()['_16_'+c]    = '\033[{}m'.format(e[1][0]) if e[1][1] == 0 \
						else '\033[{};{}m'.format(*e[1])
	globals()['_clr_'+c] = ''; _reset = ''
	exec 'def {c}(s): return _clr_{c}+s+_reset'.format(c=c)

def nocolor(s): return s

def init_color(enable_color=True,num_colors='auto'):
	if enable_color:
		assert num_colors in ('auto',8,16,256)
		globals()['_reset'] = '\033[0m'
		if num_colors in (8,16):
			pfx = '_16_'
		elif num_colors in (256,):
			pfx = '_256_'
		else:
			try:
				import os
				assert os.environ['TERM'][-8:] == '256color'
				pfx = '_256_'
			except:
				try:
					import subprocess
					a = subprocess.check_output(['infocmp','-0'])
					b = [e.split('#')[1] for e in a.split(',') if e[:6] == 'colors'][0]
					pfx = ('_16_','_256_')[b=='256']
				except:
					pfx = '_16_'

		for c in _colors:
			globals()['_clr_'+c] = globals()[pfx+c]

def test_color():
	try:
		import colorama
		colorama.init(strip=True,convert=True)
	except:
		pass
	for desc,n in (('auto','auto'),('8-color',8),('256-color',256)):
		if n != 'auto': init_color(num_colors=n)
		print('{:9}: {}'.format(desc,' '.join([globals()[c](c) for c in sorted(_colors)])))

if __name__ == '__main__': test_color()
