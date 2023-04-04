#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
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
term: Terminal classes for the MMGen suite
"""

# TODO: reimplement as instance instead of class

import sys,os,time
from collections import namedtuple

from .cfg import gc
from .util import msg,msg_r,die

try:
	import tty,termios
	from select import select
	_platform = 'linux'
except:
	try:
		import msvcrt
		_platform = 'mswin'
	except:
		die(2,'Unable to set terminal mode')
	if not sys.stdin.isatty():
		msvcrt.setmode(sys.stdin.fileno(),os.O_BINARY)

_term_dimensions = namedtuple('terminal_dimensions',['width','height'])

class MMGenTerm(object):

	@classmethod
	def register_cleanup(cls):
		pass

	@classmethod
	def init(cls,noecho=False):
		pass

	@classmethod
	def set(cls,*args,**kwargs):
		pass

	@classmethod
	def reset(cls):
		pass

	@classmethod
	def kb_hold_protect(cls):
		return None

class MMGenTermLinux(MMGenTerm):

	@classmethod
	def register_cleanup(cls):
		if not hasattr(cls,'cleanup_registered'):
			import atexit
			atexit.register(
				lambda: termios.tcsetattr(
					cls.stdin_fd,
					termios.TCSADRAIN,
					cls.orig_term) )
			cls.cleanup_registered = True

	@classmethod
	def reset(cls):
		termios.tcsetattr( cls.stdin_fd, termios.TCSANOW, cls.orig_term )
		cls.cur_term = cls.orig_term

	@classmethod
	def set(cls,setting):
		d = {
			'echo':   lambda t: t[:3] + [t[3] |  (termios.ECHO | termios.ECHONL)] + t[4:], # echo input chars
			'noecho': lambda t: t[:3] + [t[3] & ~(termios.ECHO | termios.ECHONL)] + t[4:], # don’t echo input chars
		}
		termios.tcsetattr( cls.stdin_fd, termios.TCSANOW, d[setting](cls.cur_term) )
		cls.cur_term = termios.tcgetattr(cls.stdin_fd)

	@classmethod
	def init(cls,noecho=False):
		cls.stdin_fd = sys.stdin.fileno()
		cls.cur_term = termios.tcgetattr(cls.stdin_fd)
		if not hasattr(cls,'orig_term'):
			cls.orig_term = cls.cur_term
		if noecho:
			cls.set('noecho')

	@classmethod
	def get_terminal_size(cls):
		try:
			ret = os.get_terminal_size()
		except:
			try:
				ret = (os.environ['COLUMNS'],os.environ['LINES'])
			except:
				ret = (80,25)
		return _term_dimensions(*ret)

	@classmethod
	def kb_hold_protect(cls):
		if cls.cfg.hold_protect_disable:
			return
		tty.setcbreak(cls.stdin_fd)
		timeout = 0.3
		while True:
			key = select([sys.stdin], [], [], timeout)[0]
			if key:
				sys.stdin.read(1)
			else:
				termios.tcsetattr(cls.stdin_fd, termios.TCSADRAIN, cls.cur_term)
				break

	@classmethod
	def get_char(cls,prompt='',immed_chars='',prehold_protect=True,num_bytes=5):
		"""
		Use os.read(), not file.read(), to get a variable number of bytes without blocking.
		Request 5 bytes to cover escape sequences generated by F1, F2, .. Fn keys (5 bytes)
		as well as UTF8 chars (4 bytes max).
		"""
		timeout = 0.3
		tty.setcbreak(cls.stdin_fd)
		msg_r(prompt)
		if cls.cfg.hold_protect_disable:
			prehold_protect = False
		while True:
			# Protect against held-down key before read()
			key = select([sys.stdin], [], [], timeout)[0]
			s = os.read(cls.stdin_fd,num_bytes).decode()
			if prehold_protect and key:
				continue
			if s in immed_chars:
				break
			# Protect against long keypress
			key = select([sys.stdin], [], [], timeout)[0]
			if not key:
				break
		termios.tcsetattr(cls.stdin_fd, termios.TCSADRAIN, cls.cur_term)
		return s

	@classmethod
	def get_char_raw(cls,prompt='',num_bytes=5,**kwargs):
		tty.setcbreak(cls.stdin_fd)
		msg_r(prompt)
		s = os.read(cls.stdin_fd,num_bytes).decode()
		termios.tcsetattr(cls.stdin_fd, termios.TCSADRAIN, cls.cur_term)
		return s

class MMGenTermLinuxStub(MMGenTermLinux):

	@classmethod
	def register_cleanup(cls):
		pass

	@classmethod
	def init(cls,noecho=False):
		cls.stdin_fd = sys.stdin.fileno()

	@classmethod
	def set(cls,*args,**kwargs):
		pass

	@classmethod
	def reset(cls):
		pass

	@classmethod
	def get_char(cls,prompt='',immed_chars='',prehold_protect=None,num_bytes=5):
		msg_r(prompt)
		return os.read(0,num_bytes).decode()

	get_char_raw = get_char

	@classmethod
	def kb_hold_protect(cls):
		pass

class MMGenTermMSWin(MMGenTerm):

	@classmethod
	def get_terminal_size(cls):
		import struct
		x,y = 0,0
		try:
			from ctypes import windll,create_string_buffer
			# handles - stdin: -10, stdout: -11, stderr: -12
			csbi = create_string_buffer(22)
			h = windll.kernel32.GetStdHandle(-12)
			res = windll.kernel32.GetConsoleScreenBufferInfo(h,csbi)
			assert res, 'failed to get console screen buffer info'
			left,top,right,bottom = struct.unpack('hhhhHhhhhhh', csbi.raw)[5:9]
			x = right - left + 1
			y = bottom - top + 1
		except:
			pass

		if x and y:
			return _term_dimensions(x,y)
		else:
			msg(yellow('Warning: could not get terminal size. Using fallback dimensions.'))
			return _term_dimensions(80,25)

	@classmethod
	def kb_hold_protect(cls):
		timeout = 0.5
		while True:
			hit_time = time.time()
			while True:
				if msvcrt.kbhit():
					msvcrt.getch()
					break
				if time.time() - hit_time > timeout:
					return

	@classmethod
	def get_char(cls,prompt='',immed_chars='',prehold_protect=True,num_bytes=None):
		"""
		always return a single character, ignore num_bytes
		first character of 2-character sequence returned by F1-F12 keys is discarded
		prehold_protect is ignored
		"""
		msg_r(prompt)
		timeout = 0.5
		while True:
			if msvcrt.kbhit():
				ch = chr(msvcrt.getch()[0])
				if ch == '\x03':
					raise KeyboardInterrupt
				if ch in immed_chars:
					return ch
				hit_time = time.time()
				while True:
					if msvcrt.kbhit():
						break
					if time.time() - hit_time > timeout:
						return ch

	@classmethod
	def get_char_raw(cls,prompt='',num_bytes=None,**kwargs):
		"""
		return single ASCII char or 2-char escape sequence, ignoring num_bytes
		"""
		msg_r(prompt)
		ret = msvcrt.getch()
		if ret in (b'\x00',b'\xe0'): # first byte of 2-byte escape sequence
			return chr(ret[0]) + chr(msvcrt.getch()[0])
		if ret == b'\x03':
			raise KeyboardInterrupt
		return chr(ret[0])

class MMGenTermMSWinStub(MMGenTermMSWin):

	@classmethod
	def get_char(cls,prompt='',immed_chars='',prehold_protect=None,num_bytes=None):
		"""
		Use stdin to allow UTF-8 and emulate the one-character behavior of MMGenTermMSWin
		"""
		msg_r(prompt)
		return sys.stdin.read(1)

	get_char_raw = get_char

def get_term():
	return {
		'linux': (MMGenTermLinux if sys.stdin.isatty() else MMGenTermLinuxStub),
		'mswin': (MMGenTermMSWin if sys.stdin.isatty() else MMGenTermMSWinStub),
	}[_platform]

def init_term(cfg,noecho=False):

	term = get_term()

	term.init(noecho=noecho)

	import mmgen.term as self
	for var in ('get_char','get_char_raw','kb_hold_protect','get_terminal_size'):
		setattr( self, var, getattr(term,var) )

	term.cfg = cfg # setting the _class_ attribute

def reset_term():
	get_term().reset()
