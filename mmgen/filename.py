#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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
filename: File and MMGenFile classes and methods for the MMGen suite
"""

import sys, os
from .util import die, get_extension

class File:

	def __init__(self, fn, write=False):

		self.name     = fn
		self.dirname  = os.path.dirname(fn)
		self.basename = os.path.basename(fn)
		self.ext      = get_extension(fn)
		self.mtime    = None
		self.ctime    = None
		self.atime    = None

		try:
			st = os.stat(fn)
		except:
			die('FileNotFound', f'{fn!r}: file not found')

		import stat
		if stat.S_ISBLK(st.st_mode):
			if sys.platform in ('win32',):
				die(2, 'Access to raw block devices not supported on platform {sys.platform!r}')
			mode = (os.O_RDONLY, os.O_RDWR)[bool(write)]
			try:
				fd = os.open(fn, mode)
			except OSError as e:
				if e.errno == 13:
					die(2, f'{fn!r}: permission denied')
#				if e.errno != 17: raise
			else:
				if sys.platform == 'linux':
					self.size = os.lseek(fd, 0, os.SEEK_END)
				elif sys.platform == 'darwin':
					from .platform.darwin.util import get_device_size
					self.size = get_device_size(fn)
				os.close(fd)
		else:
			self.size  = st.st_size
			self.mtime = st.st_mtime
			self.ctime = st.st_ctime
			self.atime = st.st_atime

class FileList(list):

	def __init__(self, fns, write=False):
		list.__init__(
			self,
			[File(fn, write) for fn in fns])

	def names(self):
		return [f.name for f in self]

	def sort_by_age(self, key='mtime', reverse=False):
		assert key in ('atime', 'ctime', 'mtime'), f'{key!r}: invalid sort key'
		self.sort(key=lambda a: getattr(a, key), reverse=reverse)

class MMGenFile(File):

	def __init__(self, fn, base_class=None, subclass=None, proto=None, write=False):
		"""
		'base_class' - a base class with an 'ext_to_cls' method
		'subclass'   - a subclass with an 'ext' attribute

		One or the other must be provided, but not both.

		The base class signals support for the MMGenFile API by setting its 'filename_api'
		attribute to True.
		"""

		super().__init__(fn, write)

		assert (subclass or base_class) and not (subclass and base_class), 'MMGenFile chk1'

		if not getattr(subclass or base_class, 'filename_api', False):
			die(3, f'Class {(subclass or base_class).__name__!r} does not support the MMGenFile API')

		if base_class:
			subclass = base_class.ext_to_cls(self.ext, proto)
			if not subclass:
				die('BadFileExtension', f'{self.ext!r}: not a recognized file extension for {base_class}')

		self.subclass = subclass

class MMGenFileList(FileList):

	def __init__(self, fns, base_class, proto=None, write=False):
		list.__init__(
			self,
			[MMGenFile(fn, base_class=base_class, proto=proto, write=write) for fn in fns])

def find_files_in_dir(subclass, fdir, no_dups=False):

	assert isinstance(subclass, type), f'{subclass}: not a class'

	if not getattr(subclass, 'filename_api', False):
		die(3, f'Class {subclass.__name__!r} does not support the MMGenFile API')

	matches = [l for l in os.listdir(fdir) if l.endswith('.'+subclass.ext)]

	if no_dups:
		if len(matches) == 1:
			return os.path.join(fdir, matches[0])
		elif matches:
			die(1, f'ERROR: more than one {subclass.__name__} file in directory {fdir!r}')
		else:
			return None
	else:
		return [os.path.join(fdir, m) for m in matches]

def find_file_in_dir(subclass, fdir):
	return find_files_in_dir(subclass, fdir, no_dups=True)
