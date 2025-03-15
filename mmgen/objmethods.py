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
objmethods: Mixin classes for MMGen data objects
"""

import unicodedata
from . import color as color_mod

if 'MMGenObjectDevTools' in __builtins__: # added to builtins by devinit.init_dev()
	MMGenObject = __builtins__['MMGenObjectDevTools']
else:
	class MMGenObject:
		'placeholder - overridden when testing'
		def immutable_attr_init_check(self):
			pass

def truncate_str(s, width): # width = screen width
	wide_count = 0
	for n, ch in enumerate(s, 1):
		wide_count += unicodedata.east_asian_width(ch) in ('F', 'W')
		if n + wide_count > width:
			return s[:n-1] + ('', ' ')[
				unicodedata.east_asian_width(ch) in ('F', 'W')
				and n + wide_count == width + 1]
	raise ValueError('string requires no truncating')

class Hilite:

	color = 'red'
	width = 0
	trunc_ok = True

	# class method equivalent of fmt()
	@classmethod
	def fmtc(cls, s, width, /, *, color=False):
		if len(s) > width:
			assert cls.trunc_ok, "If 'trunc_ok' is false, 'width' must be >= width of string"
			return cls.colorize(s[:width].ljust(width), color=color)
		else:
			return cls.colorize(s.ljust(width), color=color)

	@classmethod
	def hlc(cls, s, *, color=True):
		return getattr(color_mod, cls.color)(s) if color else s

	@classmethod
	def colorize(cls, s, *, color=True):
		return getattr(color_mod, cls.color)(s) if color else s

	@classmethod
	def colorize2(cls, s, *, color=True, color_override=''):
		return getattr(color_mod, color_override or cls.color)(s) if color else s

class HiliteStr(str, Hilite):

	# supports single-width characters only
	def fmt(self, width, /, *, color=False):
		if len(self) > width:
			assert self.trunc_ok, "If 'trunc_ok' is false, 'width' must be >= width of string"
			return self.colorize(self[:width].ljust(width), color=color)
		else:
			return self.colorize(self.ljust(width), color=color)

	# an alternative to fmt(), with double-width char support and other features
	def fmt2(
			self,
			width,                  # screen width - must be at least 2 (one wide char)
			/,
			*,
			color          = False,
			encl           = '',    # if set, must be exactly 2 single-width chars
			nullrepl       = '',
			append_chars   = '',    # single-width chars only
			append_color   = False,
			color_override = ''):

		if self == '':
			return getattr(color_mod, self.color)(nullrepl.ljust(width)) if color else nullrepl.ljust(width)

		s_wide_count = len(['' for ch in self if unicodedata.east_asian_width(ch) in ('F', 'W')])

		a, b = encl or ('', '')
		add_len = len(append_chars) + len(encl)

		if len(self) + s_wide_count + add_len > width:
			assert self.trunc_ok, "If 'trunc_ok' is false, 'width' must be >= screen width of string"
			s = a + (truncate_str(self, width-add_len) if s_wide_count else self[:width-add_len]) + b
		else:
			s = a + self + b

		if append_chars:
			return (
				self.colorize(s, color=color)
				+ self.colorize2(
					append_chars.ljust(width-len(s)-s_wide_count),
					color_override = append_color))
		else:
			return self.colorize2(s.ljust(width-s_wide_count), color=color, color_override=color_override)

	def hl(self, *, color=True):
		return getattr(color_mod, self.color)(self) if color else self

	# an alternative to hl(), with enclosure and color override
	# can be called as an unbound method with class as first argument
	def hl2(self, s=None, *, color=True, encl='', color_override=''):
		if encl:
			return self.colorize2(encl[0]+(s or self)+encl[1], color=color, color_override=color_override)
		else:
			return self.colorize2((s or self), color=color, color_override=color_override)

class InitErrors:

	@classmethod
	def init_fail(cls, e, m, *, e2=None, m2=None, objname=None, preformat=False):

		def get_errmsg():
			ret = m if preformat else (
				'{!r}: value cannot be converted to {} {}({!s})'.format(
					m,
					(objname or cls.__name__),
					(f'({e2!s}) ' if e2 else ''),
					e))
			return f'{m2!r}\n{ret}' if m2 else ret

		if hasattr(cls, 'passthru_excs') and type(e).__name__ in cls.passthru_excs:
			raise e

		from .util import die
		die(getattr(cls, 'exc', 'ObjectInitError'), get_errmsg())

	@classmethod
	def method_not_implemented(cls):
		import traceback
		raise NotImplementedError(
			'method {}() not implemented for class {!r}'.format(
				traceback.extract_stack()[-2].name, cls.__name__))
