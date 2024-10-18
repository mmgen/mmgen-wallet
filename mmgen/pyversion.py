#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
pyversion: Python version string operations
"""

class PythonVersion(str):

	major = 0
	minor = 0

	def __new__(cls, arg=None):
		if isinstance(arg, PythonVersion):
			return arg
		if arg:
			major, minor = arg.split('.')
		else:
			import platform
			major, minor = platform.python_version_tuple()[:2]
		me = str.__new__(cls, f'{major}.{minor}')
		me.major = int(major)
		me.minor = int(minor)
		return me

	def __lt__(self, other):
		other = type(self)(other)
		return self.major < other.major or (self.major == other.major and self.minor < other.minor)

	def __le__(self, other):
		other = type(self)(other)
		return self.major < other.major or (self.major == other.major and self.minor <= other.minor)

	def __eq__(self, other):
		other = type(self)(other)
		return self.major == other.major and self.minor == other.minor

	def __ne__(self, other):
		other = type(self)(other)
		return not (self.major == other.major and self.minor == other.minor)

	def __gt__(self, other):
		other = type(self)(other)
		return self.major > other.major or (self.major == other.major and self.minor > other.minor)

	def __ge__(self, other):
		other = type(self)(other)
		return self.major > other.major or (self.major == other.major and self.minor >= other.minor)

python_version = PythonVersion()
