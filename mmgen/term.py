#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2015 Philemon <mmgen-py@yandex.com>
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

import sys, os, struct
import mmgen.config as g
from mmgen.util import msg, msg_r

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

def _get_keypress_unix(prompt="",immed_chars="",prehold_protect=True):

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
		if immed_chars == "ALL" or ch in immed_chars: break
		if immed_chars == "ALL_EXCEPT_ENTER" and not ch in "\n\r": break
		# Protect against long keypress
		key = select([sys.stdin], [], [], timeout)[0]
		if not key: break

	termios.tcsetattr(fd, termios.TCSADRAIN, old)
	return ch


def _get_keypress_unix_raw(prompt="",immed_chars="",prehold_protect=None):

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

def _get_keypress_mswin(prompt="",immed_chars="",prehold_protect=True):

	msg_r(prompt)
	timeout = float(0.5)

	while True:
		if msvcrt.kbhit():
			ch = msvcrt.getch()

			if ord(ch) == 3: raise KeyboardInterrupt

			if immed_chars == "ALL" or ch in immed_chars:
				return ch
			if immed_chars == "ALL_EXCEPT_ENTER" and not ch in "\n\r":
				return ch

			hit_time = time.time()

			while True:
				if msvcrt.kbhit(): break
				if float(time.time() - hit_time) > timeout:
					return ch

def _get_keypress_mswin_raw(prompt="",immed_chars="",prehold_protect=None):

	msg_r(prompt)
	ch = msvcrt.getch()
	if ord(ch) == 3: raise KeyboardInterrupt
	return ch


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
	try:
		from ctypes import windll, create_string_buffer
		# stdin handle is -10
		# stdout handle is -11
		# stderr handle is -12
		h = windll.kernel32.GetStdHandle(-12)
		csbi = create_string_buffer(22)
		res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
		if res:
			(bufx, bufy, curx, cury, wattr, left, top, right, bottom,
			maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
			sizex = right - left + 1
			sizey = bottom - top + 1
			return sizex, sizey
	except:
		return 80,25

def mswin_dummy_flush(fd,termconst): pass

try:
	import tty, termios
	from select import select
	if g.disable_hold_protect:
		get_char = _get_keypress_unix_raw
		kb_hold_protect = _kb_hold_protect_unix_raw
	else:
		get_char = _get_keypress_unix
		kb_hold_protect = _kb_hold_protect_unix
	get_terminal_size = _get_terminal_size_linux
	myflush = termios.tcflush
# call: myflush(sys.stdin, termios.TCIOFLUSH)
except:
	try:
		import msvcrt, time
		if g.disable_hold_protect:
			get_char = _get_keypress_mswin_raw
			kb_hold_protect = _kb_hold_protect_mswin_raw
		else:
			get_char = _get_keypress_mswin
			kb_hold_protect = _kb_hold_protect_mswin
		get_terminal_size = _get_terminal_size_mswin
		myflush = mswin_dummy_flush
	except:
		if not sys.platform.startswith("linux") \
				and not sys.platform.startswith("win"):
			msg("Unsupported platform: %s" % sys.platform)
			msg("This program currently runs only on Linux and Windows")
		else:
			msg("Unable to set terminal mode")
		sys.exit(2)


def do_pager(text):

	pagers = ["less","more"]
	shell = False

	from os import environ

# Hack for MS Windows command line (i.e. non CygWin) environment
# When 'shell' is true, Windows aborts the calling program if executable
# not found.
# When 'shell' is false, an exception is raised, invoking the fallback
# 'print' instead of the pager.
# We risk assuming that "more" will always be available on a stock
# Windows installation.
	if sys.platform.startswith("win") and 'HOME' not in environ:
		shell = True
		pagers = ["more"]

	if 'PAGER' in environ and environ['PAGER'] != pagers[0]:
		pagers = [environ['PAGER']] + pagers

	for pager in pagers:
		end = "" if pager == "less" else "\n(end of text)\n"
		try:
			from subprocess import Popen, PIPE, STDOUT
			p = Popen([pager], stdin=PIPE, shell=shell)
		except: pass
		else:
			p.communicate(text+end+"\n")
			msg_r("\r")
			break
	else: print text+end
