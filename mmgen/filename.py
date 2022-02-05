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
filename.py:  Filename class and methods for the MMGen suite
"""

import sys,os

from .obj import *
from .util import die,get_extension
from .seed import *

class Filename(MMGenObject):

	def __init__(self,fn,base_class=None,subclass=None,proto=None,write=False):
		"""
		'base_class' - a base class with an 'ext_to_type' method
		'subclass'   - a subclass with an 'ext' attribute

		One or the other must be provided, but not both.

		The base class signals support for the Filename API by setting its 'filename_api'
		attribute to True.
		"""
		self.name     = fn
		self.dirname  = os.path.dirname(fn)
		self.basename = os.path.basename(fn)
		self.ext      = get_extension(fn)
		self.mtime    = None
		self.ctime    = None
		self.atime    = None

		assert (subclass or base_class) and not (subclass and base_class), 'Filename chk1'

		if not getattr(subclass or base_class,'filename_api',False):
			die(3,f'Class {(subclass or base_class).__name__!r} does not support the Filename API')

		if base_class:
			subclass = base_class.ext_to_type(self.ext,proto)
			if not subclass:
				from .exception import BadFileExtension
				raise BadFileExtension(f'{self.ext!r}: not a recognized file extension for {base_class}')

		self.subclass = subclass

		try:
			st = os.stat(fn)
		except:
			from .exception import FileNotFound
			raise FileNotFound(f'{fn!r}: file not found')

		import stat
		if stat.S_ISBLK(st.st_mode):
			mode = (os.O_RDONLY,os.O_RDWR)[bool(write)]
			if g.platform == 'win':
				mode |= os.O_BINARY
			try:
				fd = os.open(fn, mode)
			except OSError as e:
				if e.errno == 13:
					die(2,f'{fn!r}: permission denied')
#				if e.errno != 17: raise
			else:
				self.size = os.lseek(fd, 0, os.SEEK_END)
				os.close(fd)
		else:
			self.size  = st.st_size
			self.mtime = st.st_mtime
			self.ctime = st.st_ctime
			self.atime = st.st_atime

class MMGenFileList(list,MMGenObject):

	def __init__(self,fns,base_class,proto=None):
		flist = [Filename( fn, base_class=base_class, proto=proto ) for fn in fns]
		return list.__init__(self,flist)

	def names(self):
		return [f.name for f in self]

	def sort_by_age(self,key='mtime',reverse=False):
		if key not in ('atime','ctime','mtime'):
			die(1,f'{key!r}: illegal sort key')
		self.sort( key=lambda a: getattr(a,key), reverse=reverse )

def find_files_in_dir(subclass,fdir,no_dups=False):

	assert isinstance(subclass,type), f'{subclass}: not a class'

	if not getattr(subclass,'filename_api',False):
		die(3,f'Class {subclass.__name__!r} does not support the Filename API')

	matches = [l for l in os.listdir(fdir) if l.endswith('.'+subclass.ext)]

	if no_dups:
		if len(matches) == 1:
			return os.path.join(fdir,matches[0])
		elif matches:
			die(1,f'ERROR: more than one {subclass.__name__} file in directory {fdir!r}')
		else:
			return None
	else:
		return [os.path.join(fdir,m) for m in matches]

def find_file_in_dir(subclass,fdir):
	return find_files_in_dir(subclass,fdir,no_dups=True)
