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
term.py:  Terminal-handling routines for the MMGen suite
"""

import os,struct
from mmgen.common import *

try:
	import tty,termios
	from select import select
	_platform = 'linux'
except:
	try:
		import msvcrt,time
		_platform = 'win'
	except:
		die(2,'Unable to set terminal mode')
	if os.getenv('MMGEN_PEXPECT_POPEN_SPAWN'):
		msvcrt.setmode(sys.stdin.fileno(),os.O_BINARY)

def _kb_hold_protect_unix():

	fd = sys.stdin.fileno()
	old = termios.tcgetattr(fd)
	tty.setcbreak(fd)

	timeout = float(0.3)

	while True:
		key = select([sys.stdin], [], [], timeout)[0]
		if key: sys.stdin.read(1)
		else:
			termios.tcsetattr(fd, termios.TCSADRAIN, old)
			break

def _kb_hold_protect_unix_raw(): pass

def _get_keypress_unix(prompt='',immed_chars='',prehold_protect=True):

	msg_r(prompt)
	timeout = float(0.3)

	fd = sys.stdin.fileno()
	old = termios.tcgetattr(fd)
	tty.setcbreak(fd)

	while True:
		# Protect against held-down key before read()
		key = select([sys.stdin], [], [], timeout)[0]
		ch = sys.stdin.read(1)
		if prehold_protect:
			if key: continue
		if immed_chars == 'ALL' or ch in immed_chars: break
		if immed_chars == 'ALL_EXCEPT_ENTER' and not ch in '\n\r': break
		# Protect against long keypress
		key = select([sys.stdin], [], [], timeout)[0]
		if not key: break

	termios.tcsetattr(fd, termios.TCSADRAIN, old)
	return ch

def _get_keypress_unix_stub(prompt='',immed_chars='',prehold_protect=None):
	msg_r(prompt)
	return sys.stdin.read(1)

def _get_keypress_unix_raw(prompt='',immed_chars='',prehold_protect=None):

	msg_r(prompt)

	fd = sys.stdin.fileno()
	old = termios.tcgetattr(fd)
	tty.setcbreak(fd)

	ch = sys.stdin.read(1)

	termios.tcsetattr(fd, termios.TCSADRAIN, old)

	return ch

def _kb_hold_protect_mswin():

	timeout = float(0.5)

	while True:
		hit_time = time.time()
		while True:
			if msvcrt.kbhit():
				msvcrt.getch()
				break
			if float(time.time() - hit_time) > timeout:
				return

def _kb_hold_protect_mswin_raw(): pass

def _get_keypress_mswin(prompt='',immed_chars='',prehold_protect=True):

	msg_r(prompt)
	timeout = float(0.5)

	while True:
		if msvcrt.kbhit():
			ch = msvcrt.getch()

			if ord(ch) == 3: raise KeyboardInterrupt

			if immed_chars == 'ALL' or ch in immed_chars:
				return ch
			if immed_chars == 'ALL_EXCEPT_ENTER' and not ch in '\n\r':
				return ch

			hit_time = time.time()

			while True:
				if msvcrt.kbhit(): break
				if float(time.time() - hit_time) > timeout:
					return ch

def _get_keypress_mswin_raw(prompt='',immed_chars='',prehold_protect=None):

	msg_r(prompt)
	ch = msvcrt.getch()
	if ord(ch) == 3: raise KeyboardInterrupt
	return ch

def _get_keypress_mswin_emu(prompt='',immed_chars='',prehold_protect=None):
	msg_r(prompt)
	return sys.stdin.read(1)

def _get_terminal_size_linux():

	def ioctl_GWINSZ(fd):
		try:
			import fcntl
			cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
			return cr
		except:
			pass

	cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)

	if not cr:
		try:
			fd = os.open(os.ctermid(), os.O_RDONLY)
			cr = ioctl_GWINSZ(fd)
			os.close(fd)
		except:
			pass

	if not cr:
		try:
			cr = (os.environ['LINES'], os.environ['COLUMNS'])
		except:
			return 80,25

	return int(cr[1]), int(cr[0])

def _get_terminal_size_mswin():
	import sys,os,struct
	x,y = 0,0
	try:
		from ctypes import windll,create_string_buffer
		# handles - stdin: -10, stdout: -11, stderr: -12
		csbi = create_string_buffer(22)
		h = windll.kernel32.GetStdHandle(-12)
		res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
		if res:
			(bufx, bufy, curx, cury, wattr, left, top, right, bottom,
			maxx, maxy) = struct.unpack('hhhhHhhhhhh', csbi.raw)
			x = right - left + 1
			y = bottom - top + 1
	except:
		pass

	if x and y:
		return x, y
	else:
		msg(yellow('Warning: could not get terminal size. Using fallback dimensions.'))
		return 80,25

def mswin_dummy_flush(fd,termconst): pass

def set_terminal_vars():
	global get_char,kb_hold_protect,get_terminal_size
	if _platform == 'linux':
		get_char = (_get_keypress_unix_raw,_get_keypress_unix)[g.hold_protect]
		kb_hold_protect = (_kb_hold_protect_unix_raw,_kb_hold_protect_unix)[g.hold_protect]
		if os.getenv('MMGEN_PEXPECT_POPEN_SPAWN'):
			get_char,kb_hold_protect = _get_keypress_unix_stub,_kb_hold_protect_unix_raw
		get_terminal_size = _get_terminal_size_linux
#		myflush = termios.tcflush   # call: myflush(sys.stdin, termios.TCIOFLUSH)
	else:
		get_char = (_get_keypress_mswin_raw,_get_keypress_mswin)[g.hold_protect]
		kb_hold_protect = (_kb_hold_protect_mswin_raw,_kb_hold_protect_mswin)[g.hold_protect]
		if os.getenv('MMGEN_PEXPECT_POPEN_SPAWN'):
			get_char = _get_keypress_mswin_emu
		get_terminal_size = _get_terminal_size_mswin
#		myflush = mswin_dummy_flush
