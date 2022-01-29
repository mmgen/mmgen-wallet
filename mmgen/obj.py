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
obj.py: MMGen native classes
"""

import sys,os,re,unicodedata

from .objmethods import *
from .exception import BadTwComment

def get_obj(objname,*args,**kwargs):
	"""
	Wrapper for data objects
	- If the object throws an exception on instantiation, return False, otherwise return the object.
	- If silent is True, suppress display of the exception.
	- If return_bool is True, return True instead of the object.
	Only keyword args are accepted.
	"""
	assert args == (), 'get_obj_chk1'

	silent,return_bool = (False,False)
	if 'silent' in kwargs:
		silent = kwargs['silent']
		del kwargs['silent']
	if 'return_bool' in kwargs:
		return_bool = kwargs['return_bool']
		del kwargs['return_bool']

	try:
		ret = objname(**kwargs)
	except Exception as e:
		if not silent:
			from .util import msg
			msg(f'{e!s}')
		return False
	else:
		return True if return_bool else ret

# dict that keeps a list of keys for efficient lookup by index
class IndexedDict(dict):

	def __init__(self,*args,**kwargs):
		if args or kwargs:
			self.die('initializing values via constructor')
		self.__keylist = []
		return dict.__init__(self,*args,**kwargs)

	def __setitem__(self,key,value):
		if key in self:
			self.die('reassignment to existing key')
		self.__keylist.append(key)
		return dict.__setitem__(self,key,value)

	@property
	def keys(self):
		return self.__keylist

	def key(self,idx):
		return self.__keylist[idx]

	def __delitem__(self,*args): self.die('item deletion')
	def move_to_end(self,*args): self.die('item moving')
	def clear(self,*args):       self.die('clearing')
	def update(self,*args):      self.die('updating')

	def die(self,desc):
		raise NotImplementedError(f'{desc} not implemented for type {type(self).__name__}')

class MMGenList(list,MMGenObject):
	pass

class MMGenDict(dict,MMGenObject):
	pass

class ImmutableAttr: # Descriptor
	"""
	For attributes that are always present in the data instance
	Reassignment and deletion forbidden
	"""
	ok_dtypes = (str,type,type(None),type(lambda:0))

	def __init__(self,dtype,typeconv=True,set_none_ok=False,include_proto=False):
		assert isinstance(dtype,self.ok_dtypes), 'ImmutableAttr_check1'
		if include_proto:
			assert typeconv, 'ImmutableAttr_check2'
		if set_none_ok:
			assert typeconv and type(dtype) != str, 'ImmutableAttr_check3'

		if dtype is None:
			'use instance-defined conversion function for this attribute'
			self.conv = lambda instance,value: getattr(instance.conv_funcs,self.name)(instance,value)
		elif typeconv:
			"convert this attribute's type"
			if type(dtype) == str:
				if include_proto:
					self.conv = lambda instance,value: globals()[dtype](instance.proto,value)
				else:
					self.conv = lambda instance,value: globals()[dtype](value)
			else:
				if set_none_ok:
					self.conv = lambda instance,value: None if value is None else dtype(value)
				elif include_proto:
					self.conv = lambda instance,value: dtype(instance.proto,value)
				else:
					self.conv = lambda instance,value: dtype(value)
		else:
			"check this attribute's type"
			def assign_with_check(instance,value):
				if type(value) == dtype:
					return value
				raise TypeError('Attribute {!r} of {} instance must of type {}'.format(
					self.name,
					type(instance).__name__,
					dtype ))
			self.conv = assign_with_check

	def __set_name__(self,owner,name):
		self.name = name

	def __get__(self,instance,owner):
		return instance.__dict__[self.name]

	def setattr_condition(self,instance):
		'forbid all reassignment'
		return not self.name in instance.__dict__

	def __set__(self,instance,value):
		if not self.setattr_condition(instance):
			raise AttributeError(f'Attribute {self.name!r} of {type(instance)} instance cannot be reassigned')
		instance.__dict__[self.name] = self.conv(instance,value)

	def __delete__(self,instance):
		raise AttributeError(
			f'Attribute {self.name!r} of {type(instance).__name__} instance cannot be deleted')

class ListItemAttr(ImmutableAttr):
	"""
	For attributes that might not be present in the data instance
	Reassignment or deletion allowed if specified
	"""
	def __init__(self,dtype,typeconv=True,include_proto=False,reassign_ok=False,delete_ok=False):
		self.reassign_ok = reassign_ok
		self.delete_ok = delete_ok
		ImmutableAttr.__init__(self,dtype,typeconv=typeconv,include_proto=include_proto)

	def __get__(self,instance,owner):
		"return None if attribute doesn't exist"
		try: return instance.__dict__[self.name]
		except: return None

	def setattr_condition(self,instance):
		return getattr(instance,self.name) == None or self.reassign_ok

	def __delete__(self,instance):
		if self.delete_ok:
			if self.name in instance.__dict__:
				del instance.__dict__[self.name]
		else:
			ImmutableAttr.__delete__(self,instance)

class MMGenListItem(MMGenObject):
	valid_attrs = set()
	valid_attrs_extra = set()
	invalid_attrs = {
		'pfmt',
		'pmsg',
		'pdie',
		'valid_attrs',
		'valid_attrs_extra',
		'invalid_attrs',
		'immutable_attr_init_check',
		'conv_funcs',
		'_asdict',
	}

	def __init__(self,*args,**kwargs):
		# generate valid_attrs, or use the class valid_attrs if set
		self.__dict__['valid_attrs'] = self.valid_attrs or (
				( {e for e in dir(self) if e[:2] != '__'} | self.valid_attrs_extra )
				- MMGenListItem.invalid_attrs
				- self.invalid_attrs
			)

		if args:
			raise ValueError(f'Non-keyword args not allowed in {type(self).__name__!r} constructor')

		for k,v in kwargs.items():
			if v != None:
				setattr(self,k,v)

		# Require all immutables to be initialized.  Check performed only when testing.
		self.immutable_attr_init_check()

	# allow only valid attributes to be set
	def __setattr__(self,name,value):
		if name not in self.valid_attrs:
			raise AttributeError(f'{name!r}: no such attribute in class {type(self)}')
		return object.__setattr__(self,name,value)

	def _asdict(self):
		return dict((k,v) for k,v in self.__dict__.items() if k in self.valid_attrs)

class MMGenRange(tuple,InitErrors,MMGenObject):

	min_idx = None
	max_idx = None

	def __new__(cls,*args):
		try:
			if len(args) == 1:
				s = args[0]
				if type(s) == cls:
					return s
				assert isinstance(s,str),'not a string or string subclass'
				ss = s.split('-',1)
				first = int(ss[0])
				last = int(ss.pop())
			else:
				s = repr(args) # needed if exception occurs
				assert len(args) == 2,'one format string arg or two start,stop args required'
				first,last = args
			assert first <= last, 'start of range greater than end of range'
			if cls.min_idx is not None:
				assert first >= cls.min_idx, f'start of range < {cls.min_idx:,}'
			if cls.max_idx is not None:
				assert last <= cls.max_idx, f'end of range > {cls.max_idx:,}'
			return tuple.__new__(cls,(first,last))
		except Exception as e:
			return cls.init_fail(e,s)

	@property
	def first(self):
		return self[0]

	@property
	def last(self):
		return self[1]

	def iterate(self):
		return range(self[0],self[1]+1)

	@property
	def items(self):
		return list(self.iterate())

class Int(int,Hilite,InitErrors):
	min_val = None
	max_val = None
	max_digits = None
	color = 'red'

	def __new__(cls,n,base=10):
		if type(n) == cls:
			return n
		try:
			me = int.__new__(cls,str(n),base)
			if cls.min_val != None:
				assert me >= cls.min_val, f'is less than cls.min_val ({cls.min_val})'
			if cls.max_val != None:
				assert me <= cls.max_val, f'is greater than cls.max_val ({cls.max_val})'
			if cls.max_digits != None:
				assert len(str(me)) <= cls.max_digits, f'has more than {cls.max_digits} digits'
			return me
		except Exception as e:
			return cls.init_fail(e,n)

	@classmethod
	def fmtc(cls,*args,**kwargs):
		cls.method_not_implemented()

	@classmethod
	def colorize(cls,n,color=True):
		return super().colorize(repr(n),color=color)

class MMGenIdx(Int):
	min_val = 1

class ETHNonce(Int):
	min_val = 0

class Str(str,Hilite):
	pass

class HexStr(str,Hilite,InitErrors):
	color = 'red'
	width = None
	hexcase = 'lower'
	trunc_ok = False
	def __new__(cls,s,case=None):
		if type(s) == cls:
			return s
		if case == None:
			case = cls.hexcase
		from .util import hexdigits_lc,hexdigits_uc
		try:
			assert isinstance(s,str),'not a string or string subclass'
			assert case in ('upper','lower'), f'{case!r} incorrect case specifier'
			assert set(s) <= set(hexdigits_lc if case == 'lower' else hexdigits_uc), (
				f'not {case}case hexadecimal symbols' )
			assert not len(s) % 2,'odd-length string'
			if cls.width:
				assert len(s) == cls.width, f'Value is not {cls.width} characters wide'
			return str.__new__(cls,s)
		except Exception as e:
			return cls.init_fail(e,s)

class CoinTxID(HexStr):
	color,width,hexcase = ('purple',64,'lower')

class WalletPassword(HexStr):
	color,width,hexcase = ('blue',32,'lower')

class MMGenTxID(HexStr):
	color,width,hexcase = ('red',6,'upper')

class MMGenLabel(str,Hilite,InitErrors):
	color = 'pink'
	allowed = []
	forbidden = []
	max_len = 0
	min_len = 0
	max_screen_width = 0 # if != 0, overrides max_len
	desc = 'label'
	def __new__(cls,s,msg=None):
		if type(s) == cls:
			return s
		for k in ( cls.forbidden, cls.allowed ):
			assert type(k) == list
			for ch in k:
				assert type(ch) == str and len(ch) == 1
		try:
			s = s.strip()
			for ch in s:
				# Allow:    (L)etter,(N)umber,(P)unctuation,(S)ymbol,(Z)space
				# Disallow: (C)ontrol,(M)combining
				# Combining characters create width formatting issues, so disallow them for now
				if unicodedata.category(ch)[0] in ('C','M'):
					raise ValueError('{!a}: {} characters not allowed'.format(ch,
						{ 'C':'control', 'M':'combining' }[unicodedata.category(ch)[0]] ))

			me = str.__new__(cls,s)

			if cls.max_screen_width:
				me.screen_width = len(s) + len([1 for ch in s if unicodedata.east_asian_width(ch) in ('F','W')])
				assert me.screen_width <= cls.max_screen_width, f'too wide (>{cls.max_screen_width} screen width)'
			else:
				assert len(s) <= cls.max_len, f'too long (>{cls.max_len} symbols)'

			assert len(s) >= cls.min_len, f'too short (<{cls.min_len} symbols)'

			if cls.allowed and not set(list(s)).issubset(set(cls.allowed)):
				raise ValueError('contains non-allowed symbols: ' + ' '.join(set(list(s)) - set(cls.allowed)) )

			if cls.forbidden and any(ch in s for ch in cls.forbidden):
				raise ValueError('contains one of these forbidden symbols: ' + ' '.join(cls.forbidden) )

			return me
		except Exception as e:
			return cls.init_fail(e,s)

class MMGenWalletLabel(MMGenLabel):
	max_len = 48
	desc = 'wallet label'

class TwComment(MMGenLabel):
	max_screen_width = 80
	desc = 'tracking wallet comment'
	exc = BadTwComment

class MMGenTxLabel(MMGenLabel):
	max_len = 72
	desc = 'transaction label'

class MMGenPWIDString(MMGenLabel):
	max_len = 256
	min_len = 1
	desc = 'password ID string'
	forbidden = list(' :/\\')
	trunc_ok = False
