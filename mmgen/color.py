#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2016 Philemon <mmgen-py@yandex.com>
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
color.py:  color routines for the MMGen suite
"""

import os

# If 88- or 256-color support is compiled, the following apply.
#    P s = 3 8 ; 5 ; P s -> Set foreground color to the second P s .
#    P s = 4 8 ; 5 ; P s -> Set background color to the second P s .
if os.environ['TERM'][-8:] == '256color':
	_blk,_red,_grn,_yel,_blu,_mag,_cya,_bright,_dim,_ybright,_ydim,_pnk,_orng,_gry = [
	'\033[38;5;%s;1m' % c for c in 232,210,121,229,75,90,122,231,245,187,243,218,215,246]
	_redbg = '\033[38;5;232;48;5;210;1m'
	_grnbg = '\033[38;5;232;48;5;121;1m'
	_grybg = '\033[38;5;231;48;5;240;1m'
	_reset = '\033[0m'
else:
	_blk,_red,_grn,_yel,_blu,_mag,_cya,_reset,_grnbg = \
		['\033[%sm' % c for c in '30;1','31;1','32;1','33;1','34;1','35;1','36;1','0','30;102']
	_gry=_orng=_pnk=_redbg=_ybright=_ydim=_bright=_dim=_grybg=_mag  # TODO

clr_red=clr_grn=clr_grnbg=clr_yel=clr_cya=clr_blu=clr_pnk=clr_orng=clr_gry=clr_mag=clr_reset=''

def nocolor(s): return s
def red(s):     return clr_red+s+clr_reset
def green(s):   return clr_grn+s+clr_reset
def grnbg(s):   return clr_grnbg+s+clr_reset
def yellow(s):  return clr_yel+s+clr_reset
def cyan(s):    return clr_cya+s+clr_reset
def blue(s):    return clr_blu+s+clr_reset
def pink(s):    return clr_pnk+s+clr_reset
def orange(s):  return clr_orng+s+clr_reset
def gray(s):    return clr_gry+s+clr_reset
def magenta(s): return clr_mag+s+clr_reset

def init_color(enable_color=True):
	global clr_red,clr_grn,clr_grnbg,clr_yel,clr_cya,clr_blu,clr_pnk,clr_orng,clr_gry,clr_mag,clr_reset
	if enable_color:
		clr_red = _red   
		clr_grn = _grn
		clr_grnbg = _grnbg
		clr_yel = _yel
		clr_cya = _cya
		clr_blu = _blu
		clr_pnk = _pnk
		clr_orng = _orng
		clr_gry = _gry
		clr_mag = _mag
		clr_reset = _reset
