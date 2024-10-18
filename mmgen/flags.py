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
flags: Class flags and opts for the MMGen suite
"""

from .base_obj import AttrCtrl, Lockable
from .util import fmt_list, die

class ClassFlags(AttrCtrl):
	_name = 'flags'
	_desc = 'flag'
	reserved_attrs = ()

	def __init__(self, parent, arg):
		self._parent = parent
		self._available = getattr(self._parent, 'avail_'+self._name)

		for a in self._available:
			if a.startswith('_'):
				die('ClassFlagsError', f'{a!r}: {self._desc} cannot begin with an underscore')
			for b in self.reserved_attrs:
				if a == b:
					die('ClassFlagsError', f'{a!r}: {b} is a reserved name for {self._desc}')

		if arg:
			assert type(arg) in (list, tuple), f"{arg!r}: {self._name!r} must be list or tuple"
		else:
			arg = []

		for e in arg:
			if e not in self._available:
				self.not_available_error(e)

		for e in self._available:
			setattr(self, e, e in arg)

	def __dir__(self):
		return [k for k in self.__dict__ if not k.startswith('_') and not k in self.reserved_attrs]

	def __str__(self):
		return ' '.join(f'{k}={getattr(self, k)}' for k in dir(self))

	def __setattr__(self, name, val):

		if self._locked:

			if name not in self._available:
				self.not_available_error(name)

			if self._name == 'flags':
				assert isinstance(val, bool), f'{val!r} not boolean'
				old_val = getattr(self, name)
				if val and old_val:
					die('ClassFlagsError', f'{self._desc} {name!r} already set')
				if not val and not old_val:
					die('ClassFlagsError', f'{self._desc} {name!r} not set, so cannot be unset')

		super().__setattr__(name, val)

	def not_available_error(self, name):
		die('ClassFlagsError', '{!r}: unrecognized {} for {}: (available {}: {})'.format(
			name,
			self._desc,
			type(self._parent).__name__,
			self._name,
			fmt_list(self._available, fmt='bare')))

class ClassOpts(ClassFlags, Lockable):
	_name = 'opts'
	_desc = 'opt'
