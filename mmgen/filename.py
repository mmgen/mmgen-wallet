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
filename.py:  Filename class and methods for the MMGen suite
"""
import sys,os
from mmgen.obj import *
from mmgen.util import die,get_extension,check_infile

class Filename(MMGenObject):

	def __init__(self,fn,ftype=None,write=False):
		self.name     = fn
		self.dirname  = os.path.dirname(fn)
		self.basename = os.path.basename(fn)
		self.ext      = get_extension(fn)
		self.ftype    = None # the file's associated class

		from mmgen.seed import SeedSource
		if ftype:
			if type(ftype) == type:
				if issubclass(ftype,SeedSource):
					self.ftype = ftype
				# elif: # other MMGen file types
				else:
					die(3,"'%s': not a recognized file type for SeedSource" % ftype)
			else:
				die(3,"'%s': not a class" % ftype)
		else:
			self.ftype = SeedSource.ext_to_type(self.ext)
			if not self.ftype:
				die(3,"'%s': not a recognized extension for SeedSource" % self.ext)


		import stat
		if stat.S_ISBLK(os.stat(fn).st_mode):
			mode = (os.O_RDONLY,os.O_RDWR)[bool(write)]
			if sys.platform[:3] == 'win': mode |= os.O_BINARY
			try:
				fd = os.open(fn, mode)
			except OSError as e:
				if e.errno == 13:
					die(2,"'%s': permission denied" % fn)
#				if e.errno != 17: raise
			else:
				self.size = os.lseek(fd, 0, os.SEEK_END)
				os.close(fd)
		else:
			self.size = os.stat(fn).st_size
