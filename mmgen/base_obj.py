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
base_obj: base objects with no internal imports for the MMGen suite
"""

class AsyncInit(type):
	async def __call__(cls, *args, **kwargs):
		instance = cls.__new__(cls, *args, **kwargs)
		await type(instance).__init__(instance, *args, **kwargs)
		return instance

class AttrCtrlMeta(type):
	def __call__(cls, *args, **kwargs):
		instance = super().__call__(*args, **kwargs)
		if instance._autolock:
			instance._lock()
		return instance

class AttrCtrl(metaclass=AttrCtrlMeta):
	"""
	After instance is locked, forbid setting any attribute if the attribute is not present
	in either the class or instance dict.

	Ensure that attribute's type matches that of the instance attribute, or the class
	attribute, if _use_class_attr is True.  If the instance or class attribute is set
	to None, no type checking is performed.

	If _default_to_none is True, return None when accessing non-existent attributes
	instead of raising AttributeError.
	"""
	_autolock = True
	_locked = False
	_use_class_attr = False
	_default_to_none = False
	_skip_type_check = ()
	_delete_ok = ()

	def _lock(self):
		self._locked = True

	def __getattr__(self, name):
		if self._locked and self._default_to_none:
			return None
		else:
			raise AttributeError(f'{type(self).__name__} object has no attribute {name!r}')

	def __setattr__(self, name, value):

		if self._locked:
			assert name != '_locked', 'lock can be set only once'

			def do_error(name, value, ref_val):
				raise AttributeError(
					f'{value!r}: invalid value for attribute {name!r}'
					+ ' of {} object (must be of type {}, not {})'.format(
						type(self).__name__,
						type(ref_val).__name__,
						type(value).__name__))

			if not (name in self.__dict__ or hasattr(type(self), name)):
				raise AttributeError(f'{type(self).__name__} object has no attribute {name!r}')

			ref_val = getattr(type(self), name) if self._use_class_attr else getattr(self, name)

			if (
				(name not in self._skip_type_check)
				and (ref_val is not None)
				and not isinstance(value, type(ref_val))
			):
				do_error(name, value, ref_val)

		return object.__setattr__(self, name, value)

	def __delattr__(self, name):
		if self._locked and not name in self._delete_ok:
			raise AttributeError('attribute cannot be deleted')
		return object.__delattr__(self, name)

class Lockable(AttrCtrl):
	"""
	After instance is locked, its attributes become read-only, with the following exceptions:
	  - if an attribute's name is in _set_ok, it can be set once after locking, if unset
	  - if an attribute's name is in _reset_ok, read-only restrictions are bypassed and only
	    AttrCtrl checking is performed

	An attribute is considered unset if its value is None, or if it evaluates to False but is
	not zero; or if it is not present in the instance __dict__ when _use_class_attr is True.
	"""
	_set_ok = ()
	_reset_ok = ()

	def _lock(self):
		for name in ('_set_ok', '_reset_ok'):
			for attr in getattr(self, name):
				assert hasattr(self, attr), (
					f'attribute {attr!r} in {name!r} not found in {type(self).__name__} object {id(self)}')
		super()._lock()

	def __setattr__(self, name, value):
		if self._locked and (name in self.__dict__ or hasattr(type(self), name)):
			val = getattr(self, name)
			if name not in (self._set_ok + self._reset_ok):
				raise AttributeError(f'attribute {name!r} of {type(self).__name__} object is read-only')
			elif name not in self._reset_ok:
				if not (
					(val != 0 and not val) or
					(self._use_class_attr and name not in self.__dict__)):
					raise AttributeError(
						f'attribute {name!r} of {type(self).__name__} object is already set,'
						+ ' and resetting is forbidden')

		return AttrCtrl.__setattr__(self, name, value)
