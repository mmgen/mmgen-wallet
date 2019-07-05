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
filename.py:  Filename class and methods for the MMGen suite
"""
import sys,os
from mmgen.obj import *
from mmgen.util import die,get_extension
from mmgen.seed import *

class Filename(MMGenObject):

	def __init__(self,fn,ftype=None,write=False):
		self.name     = fn
		self.dirname  = os.path.dirname(fn)
		self.basename = os.path.basename(fn)
		self.ext      = get_extension(fn)
		self.ftype    = None # the file's associated class
		self.mtime    = None
		self.ctime    = None
		self.atime    = None

		from mmgen.seed import SeedSource
		from mmgen.tx import MMGenTX
		if ftype:
			if type(ftype) == type:
				if issubclass(ftype,(SeedSource,MMGenTX)):
					self.ftype = ftype
				# elif: # other MMGen file types
				else:
					die(3,"'{}': not a recognized file type for SeedSource".format(ftype))
			else:
				die(3,"'{}': not a class".format(ftype))
		else:
			# TODO: other file types
			self.ftype = SeedSource.ext_to_type(self.ext)
			if not self.ftype:
				die(3,"'{}': not a recognized extension for SeedSource".format(self.ext))


		import stat
		if stat.S_ISBLK(os.stat(fn).st_mode):
			mode = (os.O_RDONLY,os.O_RDWR)[bool(write)]
			if g.platform == 'win': mode |= os.O_BINARY
			try:
				fd = os.open(fn, mode)
			except OSError as e:
				if e.errno == 13:
					die(2,"'{}': permission denied".format(fn))
#				if e.errno != 17: raise
			else:
				self.size = os.lseek(fd, 0, os.SEEK_END)
				os.close(fd)
		else:
			self.size = os.stat(fn).st_size
			self.mtime = os.stat(fn).st_mtime
			self.ctime = os.stat(fn).st_ctime
			self.atime = os.stat(fn).st_atime

class MMGenFileList(list,MMGenObject):

	def __init__(self,fns,ftype):
		flist = [Filename(fn,ftype) for fn in fns]
		return list.__init__(self,flist)

	def names(self):
		return [f.name for f in self]

	def sort_by_age(self,key='mtime',reverse=False):
		if key not in ('atime','ctime','mtime'):
			die(1,"'{}': illegal sort key".format(key))
		self.sort(key=lambda a: getattr(a,key),reverse=reverse)

def find_files_in_dir(ftype,fdir,no_dups=False):
	if type(ftype) != type:
		die(3,"'{}': not a type".format(ftype))

	from mmgen.seed import SeedSource
	if not issubclass(ftype,SeedSource):
		die(3,"'{}': not a recognized file type".format(ftype))

	try: dirlist = os.listdir(fdir)
	except: die(3,"ERROR: unable to read directory '{}'".format(fdir))

	matches = [l for l in dirlist if l[-len(ftype.ext)-1:]=='.'+ftype.ext]

	if no_dups:
		if len(matches) > 1:
			die(1,"ERROR: more than one {} file in directory '{}'".format(ftype.__name__,fdir))
		return os.path.join(fdir,matches[0]) if len(matches) else None
	else:
		return [os.path.join(fdir,m) for m in matches]

def find_file_in_dir(ftype,fdir,no_dups=True):
	return find_files_in_dir(ftype,fdir,no_dups=no_dups)
