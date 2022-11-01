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
objmethods.py: Mixin classes for MMGen data objects
"""

import unicodedata
from .globalvars import g
import mmgen.color as color_mod

if 'MMGenObjectDevTools' in __builtins__: # added to builtins by devinit.init_dev()
	MMGenObject = __builtins__['MMGenObjectDevTools']
else:
	class MMGenObject:
		'placeholder - overridden when testing'
		def immutable_attr_init_check(self): pass

def truncate_str(s,width): # width = screen width
	wide_count = 0
	for i in range(len(s)):
		wide_count += unicodedata.east_asian_width(s[i]) in ('F','W')
		if wide_count + i >= width:
			return s[:i] + ('',' ')[
				unicodedata.east_asian_width(s[i]) in ('F','W')
				and wide_count + i == width]
	else: # pad the string to width if necessary
		return s + ' '*(width-len(s)-wide_count)

class Hilite:

	color = 'red'
	width = 0
	trunc_ok = True

	@classmethod
	# 'width' is screen width (greater than len(s) for CJK strings)
	# 'append_chars' and 'encl' must consist of single-width chars only
	def fmtc(cls,s,width=None,color=False,encl='',trunc_ok=None,
				center=False,nullrepl='',append_chars='',append_color=False,color_override=''):
		s_wide_count = len([1 for ch in s if unicodedata.east_asian_width(ch) in ('F','W')])
		if encl:
			a,b = list(encl)
			add_len = len(append_chars) + 2
		else:
			a,b = ('','')
			add_len = len(append_chars)
		if width == None:
			width = cls.width
		if trunc_ok == None:
			trunc_ok = cls.trunc_ok
		if g.test_suite:
			assert isinstance(encl,str) and len(encl) in (0,2),"'encl' must be 2-character str"
			assert width >= 2 + add_len, f'{s!r}: invalid width ({width}) (must be at least 2)' # CJK: 2 cells
		if len(s) + s_wide_count + add_len > width:
			assert trunc_ok, "If 'trunc_ok' is false, 'width' must be >= screen width of string"
			s = truncate_str(s,width-add_len)
		if s == '' and nullrepl:
			s = nullrepl.center(width)
		else:
			s = a+s+b
			if center:
				s = s.center(width)
		if append_chars:
			return (
				cls.colorize(s,color=color)
				+ cls.colorize(
					append_chars.ljust(width-len(s)-s_wide_count),
					color_override = append_color ))
		else:
			return cls.colorize(s.ljust(width-s_wide_count),color=color,color_override=color_override)

	@classmethod
	def colorize(cls,s,color=True,color_override=''):
		return getattr( color_mod, color_override or cls.color )(s) if color else s

	def fmt(self,*args,**kwargs):
		assert args == () # forbid invocation w/o keywords
		return self.fmtc(self,*args,**kwargs)

	@classmethod
	def hlc(cls,s,color=True,encl='',color_override=''):
		if encl:
			assert isinstance(encl,str) and len(encl) == 2, "'encl' must be 2-character str"
			s = encl[0] + s + encl[1]
		return cls.colorize(s,color=color,color_override=color_override)

	def hl(self,*args,**kwargs):
		assert args == () # forbid invocation w/o keywords
		return self.hlc(self,*args,**kwargs)

class InitErrors:

	@classmethod
	def init_fail(cls,e,m,e2=None,m2=None,objname=None,preformat=False):

		if preformat:
			errmsg = m
		else:
			errmsg = '{!r}: value cannot be converted to {} {}({!s})'.format(
				m,
				(objname or cls.__name__),
				(f'({e2!s}) ' if e2 else ''),
				e )

		if m2:
			errmsg = repr(m2) + '\n' + errmsg

		from .util import die

		if hasattr(cls,'passthru_excs') and type(e).__name__ in cls.passthru_excs:
			raise
		elif hasattr(cls,'exc'):
			die( cls.exc, errmsg )
		else:
			die( 'ObjectInitError', errmsg )

	@classmethod
	def method_not_implemented(cls):
		import traceback
		raise NotImplementedError(
			'method {}() not implemented for class {!r}'.format(
				traceback.extract_stack()[-2].name, cls.__name__) )
