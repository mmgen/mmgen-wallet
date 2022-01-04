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
from decimal import *
from string import hexdigits,ascii_letters,digits

from .exception import *
from .globalvars import *
from .color import *

class AsyncInit(type):
	async def __call__(cls,*args,**kwargs):
		instance = cls.__new__(cls,*args,**kwargs)
		await type(instance).__init__(instance,*args,**kwargs)
		return instance

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

def is_mmgen_seed_id(s):   return get_obj(SeedID,     sid=s, silent=True,return_bool=True)
def is_mmgen_idx(s):       return get_obj(AddrIdx,    n=s,   silent=True,return_bool=True)
def is_addrlist_id(s):     return get_obj(AddrListID, sid=s, silent=True,return_bool=True)
def is_seed_split_specifier(s): return get_obj(SeedSplitSpecifier, s=s, silent=True,return_bool=True)

def is_mmgen_id(proto,s):  return get_obj(MMGenID,  proto=proto, id_str=s, silent=True,return_bool=True)
def is_coin_addr(proto,s): return get_obj(CoinAddr, proto=proto, addr=s,   silent=True,return_bool=True)
def is_wif(proto,s):       return get_obj(WifKey,   proto=proto, wif=s,    silent=True,return_bool=True)

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

class MMGenList(list,MMGenObject): pass
class MMGenDict(dict,MMGenObject): pass
class AddrListData(list,MMGenObject): pass

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

		if hasattr(cls,'passthru_excs') and type(e) in cls.passthru_excs:
			raise
		elif hasattr(cls,'exc'):
			raise cls.exc(errmsg)
		else:
			raise ObjectInitError(errmsg)

	@classmethod
	def method_not_implemented(cls):
		import traceback
		raise NotImplementedError(
			'method {}() not implemented for class {!r}'.format(
				traceback.extract_stack()[-2].name, cls.__name__) )

class Hilite(object):

	color = 'red'
	width = 0
	trunc_ok = True

	@classmethod
	# 'width' is screen width (greater than len(s) for CJK strings)
	# 'append_chars' and 'encl' must consist of single-width chars only
	def fmtc(cls,s,width=None,color=False,encl='',trunc_ok=None,
				center=False,nullrepl='',append_chars='',append_color=False):
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
			return cls.colorize(s.ljust(width-s_wide_count),color=color)

	@classmethod
	def colorize(cls,s,color=True,color_override=''):
		return globals()[color_override or cls.color](s) if color else s

	def fmt(self,*args,**kwargs):
		assert args == () # forbid invocation w/o keywords
		return self.fmtc(self,*args,**kwargs)

	@classmethod
	def hlc(cls,s,color=True,encl=''):
		if encl:
			assert isinstance(encl,str) and len(encl) == 2, "'encl' must be 2-character str"
			s = encl[0] + s + encl[1]
		return cls.colorize(s,color=color)

	def hl(self,*args,**kwargs):
		assert args == () # forbid invocation w/o keywords
		return self.hlc(self,*args,**kwargs)

class Str(str,Hilite): pass

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

class ImmutableAttr: # Descriptor
	"""
	For attributes that are always present in the data instance
	Reassignment and deletion forbidden
	"""
	ok_dtypes = (str,type,type(None),type(lambda:0))

	def __init__(self,dtype,typeconv=True,set_none_ok=False,include_proto=False):
		assert isinstance(dtype,self.ok_dtypes), 'ImmutableAttr_check1'
		if include_proto:
			assert typeconv and type(dtype) == str, 'ImmutableAttr_check2'
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

class MMGenIdx(Int): min_val = 1
class SeedShareIdx(MMGenIdx): max_val = 1024
class SeedShareCount(SeedShareIdx): min_val = 2
class MasterShareIdx(MMGenIdx): max_val = 1024
class AddrIdx(MMGenIdx): max_digits = 7

class AddrIdxList(list,InitErrors,MMGenObject):
	max_len = 1000000
	def __init__(self,fmt_str=None,idx_list=None,sep=','):
		try:
			if idx_list:
				return list.__init__(self,sorted({AddrIdx(i) for i in idx_list}))
			elif fmt_str:
				ret = []
				for i in (fmt_str.split(sep)):
					j = i.split('-')
					if len(j) == 1:
						idx = AddrIdx(i)
						if not idx:
							break
						ret.append(idx)
					elif len(j) == 2:
						beg = AddrIdx(j[0])
						if not beg:
							break
						end = AddrIdx(j[1])
						if not beg or (end < beg):
							break
						ret.extend([AddrIdx(x) for x in range(beg,end+1)])
					else: break
				else:
					return list.__init__(self,sorted(set(ret))) # fell off end of loop - success
				raise ValueError(f'{i!r}: invalid range')
		except Exception as e:
			return type(self).init_fail(e,idx_list or fmt_str)

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

class SubSeedIdxRange(MMGenRange):
	min_idx = 1
	max_idx = 1000000

class UnknownCoinAmt(Decimal): pass

class DecimalNegateResult(Decimal): pass

class CoinAmt(Decimal,Hilite,InitErrors): # abstract class
	"""
	Instantiating with 'from_decimal' rounds value down to 'max_prec' precision.
	For addition and subtraction, operand types must match.
	For multiplication and division, operand types may differ.
	Negative amounts, floor division and modulus operation are unimplemented.
	"""
	color = 'yellow'
	forbidden_types = (float,int)

	max_prec = 0      # number of decimal places for this coin
	max_amt  = None   # coin supply if known, otherwise None
	units    = ()     # defined unit names, e.g. ('satoshi',...)
	amt_fs   = '0.0'  # format string for the fmt() method

	def __new__(cls,num,from_unit=None,from_decimal=False):
		if type(num) == cls:
			return num
		try:
			if from_unit:
				assert from_unit in cls.units, f'{from_unit!r}: unrecognized denomination for {cls.__name__}'
				assert type(num) == int,'value is not an integer'
				me = Decimal.__new__(cls,num * getattr(cls,from_unit))
			elif from_decimal:
				assert type(num) == Decimal, f'number must be of type Decimal, not {type(num).__name__})'
				me = Decimal.__new__(cls,num.quantize(Decimal('10') ** -cls.max_prec))
			else:
				for t in cls.forbidden_types:
					assert type(num) is not t, f'number is of forbidden type {t.__name__}'
				me = Decimal.__new__(cls,str(num))
			assert me.normalize().as_tuple()[-1] >= -cls.max_prec,'too many decimal places in coin amount'
			if cls.max_amt:
				assert me <= cls.max_amt, f'{me}: coin amount too large (>{cls.max_amt})'
			assert me >= 0,'coin amount cannot be negative'
			return me
		except Exception as e:
			return cls.init_fail(e,num)

	def to_unit(self,unit,show_decimal=False):
		ret = Decimal(self) // getattr(self,unit)
		if show_decimal and ret < 1:
			return f'{ret:.8f}'.rstrip('0')
		return int(ret)

	@classmethod
	def fmtc(cls):
		cls.method_not_implemented()

	def fmt(self,fs=None,color=False,suf='',prec=1000):
		if fs == None:
			fs = self.amt_fs
		s = self.__str__()
		if '.' in fs:
			p1,p2 = list(map(int,fs.split('.',1)))
			ss = s.split('.',1)
			if len(ss) == 2:
				a,b = ss
				ret = a.rjust(p1) + '.' + ((b+suf).ljust(p2+len(suf)))[:prec]
			else:
				ret = s.rjust(p1) + suf + (' ' * (p2+1))[:prec+1-len(suf)]
		else:
			ret = s.ljust(int(fs))
		return self.colorize(ret,color=color)

	def hl(self,color=True):
		return self.colorize(self.__str__(),color=color)

	def hl2(self,color=True,encl=''): # display with coin symbol
		return (
			encl[:-1]
			+ self.colorize(self.__str__(),color=color)
			+ ' ' + type(self).__name__[:-3]
			+ encl[1:]
		)

	def __str__(self): # format simply, with no exponential notation
		return str(int(self)) if int(self) == self else self.normalize().__format__('f')

	def __repr__(self):
		return "{}('{}')".format(type(self).__name__,self.__str__())

	def __add__(self,other,*args,**kwargs):
		"""
		we must allow other to be int(0) to use the sum() builtin
		"""
		if type(other) not in ( type(self), DecimalNegateResult ) and other != 0:
			raise ValueError(
				f'operand {other} of incorrect type ({type(other).__name__} != {type(self).__name__})')
		return type(self)(Decimal.__add__(self,other,*args,**kwargs))

	__radd__ = __add__

	def __sub__(self,other,*args,**kwargs):
		if type(other) is not type(self):
			raise ValueError(
				f'operand {other} of incorrect type ({type(other).__name__} != {type(self).__name__})')
		return type(self)(Decimal.__sub__(self,other,*args,**kwargs))

	def copy_negate(self,*args,**kwargs):
		"""
		We implement this so that __add__() can check type, because:
			class Decimal:
				def __sub__(self, other, ...):
					...
					return self.__add__(other.copy_negate(), ...)
		"""
		return DecimalNegateResult(Decimal.copy_negate(self,*args,**kwargs))

	def __mul__(self,other,*args,**kwargs):
		return type(self)('{:0.{p}f}'.format(
			Decimal.__mul__(self,Decimal(other),*args,**kwargs),
			p = self.max_prec
		))

	__rmul__ = __mul__

	def __truediv__(self,other,*args,**kwargs):
		return type(self)('{:0.{p}f}'.format(
			Decimal.__truediv__(self,Decimal(other),*args,**kwargs),
			p = self.max_prec
		))

	def __neg__(self,*args,**kwargs):
		self.method_not_implemented()

	def __floordiv__(self,*args,**kwargs):
		self.method_not_implemented()

	def __mod__(self,*args,**kwargs):
		self.method_not_implemented()

class BTCAmt(CoinAmt):
	max_prec = 8
	max_amt = 21000000
	satoshi = Decimal('0.00000001')
	units = ('satoshi',)
	amt_fs = '4.8'

class BCHAmt(BTCAmt): pass
class B2XAmt(BTCAmt): pass
class LTCAmt(BTCAmt): max_amt = 84000000

class XMRAmt(CoinAmt):
	max_prec = 12
	atomic = Decimal('0.000000000001')
	units = ('atomic',)
	amt_fs = '4.12'

from .altcoins.eth.obj import ETHAmt,ETHNonce

class CoinAddr(str,Hilite,InitErrors,MMGenObject):
	color = 'cyan'
	hex_width = 40
	width = 1
	trunc_ok = False
	def __new__(cls,proto,addr):
		if type(addr) == cls:
			return addr
		try:
			assert set(addr) <= set(ascii_letters+digits),'contains non-alphanumeric characters'
			me = str.__new__(cls,addr)
			ap = proto.parse_addr(addr)
			assert ap, f'coin address {addr!r} could not be parsed'
			me.addr_fmt = ap.fmt
			me.hex = ap.bytes.hex()
			me.proto = proto
			return me
		except Exception as e:
			return cls.init_fail(e,addr,objname=f'{proto.cls_name} address')

	@classmethod
	def fmtc(cls,addr,**kwargs):
		w = kwargs['width'] or cls.width
		return super().fmtc(addr[:w-2]+'..' if w < len(addr) else addr, **kwargs)

class TokenAddr(CoinAddr):
	color = 'blue'

class ViewKey(object):
	def __new__(cls,proto,viewkey):
		if proto.name == 'Zcash':
			return ZcashViewKey.__new__(ZcashViewKey,proto,viewkey)
		elif proto.name == 'Monero':
			return MoneroViewKey.__new__(MoneroViewKey,viewkey)
		else:
			raise ValueError(f'{proto.name}: protocol does not support view keys')

class ZcashViewKey(CoinAddr): hex_width = 128

class SeedID(str,Hilite,InitErrors):
	color = 'blue'
	width = 8
	trunc_ok = False
	def __new__(cls,seed=None,sid=None):
		if type(sid) == cls:
			return sid
		try:
			if seed:
				from .seed import SeedBase
				assert isinstance(seed,SeedBase),'not a subclass of SeedBase'
				from .util import make_chksum_8
				return str.__new__(cls,make_chksum_8(seed.data))
			elif sid:
				assert set(sid) <= set(hexdigits.upper()),'not uppercase hex digits'
				assert len(sid) == cls.width, f'not {cls.width} characters wide'
				return str.__new__(cls,sid)
			raise ValueError('no arguments provided')
		except Exception as e:
			return cls.init_fail(e,seed or sid)

class SubSeedIdx(str,Hilite,InitErrors):
	color = 'red'
	trunc_ok = False
	def __new__(cls,s):
		if type(s) == cls:
			return s
		try:
			assert isinstance(s,str),'not a string or string subclass'
			idx = s[:-1] if s[-1] in 'SsLl' else s
			from .util import is_int
			assert is_int(idx),"valid format: an integer, plus optional letter 'S','s','L' or 'l'"
			idx = int(idx)
			assert idx >= SubSeedIdxRange.min_idx, f'subseed index < {SubSeedIdxRange.min_idx:,}'
			assert idx <= SubSeedIdxRange.max_idx, f'subseed index > {SubSeedIdxRange.max_idx:,}'

			sstype,ltr = ('short','S') if s[-1] in 'Ss' else ('long','L')
			me = str.__new__(cls,str(idx)+ltr)
			me.idx = idx
			me.type = sstype
			return me
		except Exception as e:
			return cls.init_fail(e,s)

class MMGenID(str,Hilite,InitErrors,MMGenObject):
	color = 'orange'
	width = 0
	trunc_ok = False
	def __new__(cls,proto,id_str):
		try:
			ss = str(id_str).split(':')
			assert len(ss) in (2,3),'not 2 or 3 colon-separated items'
			t = proto.addr_type((ss[1],proto.dfl_mmtype)[len(ss)==2])
			me = str.__new__(cls,'{}:{}:{}'.format(ss[0],t,ss[-1]))
			me.sid = SeedID(sid=ss[0])
			me.idx = AddrIdx(ss[-1])
			me.mmtype = t
			assert t in proto.mmtypes, f'{t}: invalid address type for {proto.cls_name}'
			me.al_id = str.__new__(AddrListID,me.sid+':'+me.mmtype) # checks already done
			me.sort_key = '{}:{}:{:0{w}}'.format(me.sid,me.mmtype,me.idx,w=me.idx.max_digits)
			me.proto = proto
			return me
		except Exception as e:
			return cls.init_fail(e,id_str)

class TwMMGenID(str,Hilite,InitErrors,MMGenObject):
	color = 'orange'
	width = 0
	trunc_ok = False
	def __new__(cls,proto,id_str):
		if type(id_str) == cls:
			return id_str
		ret = None
		try:
			ret = MMGenID(proto,id_str)
			sort_key,idtype = ret.sort_key,'mmgen'
		except Exception as e:
			try:
				assert id_str.split(':',1)[0] == proto.base_coin.lower(),(
					f'not a string beginning with the prefix {proto.base_coin.lower()!r}:' )
				assert set(id_str[4:]) <= set(ascii_letters+digits),'contains non-alphanumeric characters'
				assert len(id_str) > 4,'not more that four characters long'
				ret,sort_key,idtype = str(id_str),'z_'+id_str,'non-mmgen'
			except Exception as e2:
				return cls.init_fail(e,id_str,e2=e2)

		me = str.__new__(cls,ret)
		me.obj = ret
		me.sort_key = sort_key
		me.type = idtype
		me.proto = proto
		return me

# non-displaying container for TwMMGenID,TwComment
class TwLabel(str,InitErrors,MMGenObject):
	exc = BadTwLabel
	passthru_excs = (BadTwComment,)
	def __new__(cls,proto,text):
		if type(text) == cls:
			return text
		try:
			ts = text.split(None,1)
			mmid = TwMMGenID(proto,ts[0])
			comment = TwComment(ts[1] if len(ts) == 2 else '')
			me = str.__new__( cls, mmid + (' ' + comment if comment else '') )
			me.mmid = mmid
			me.comment = comment
			me.proto = proto
			return me
		except Exception as e:
			return cls.init_fail(e,text)

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
		try:
			assert isinstance(s,str),'not a string or string subclass'
			assert case in ('upper','lower'), f'{case!r} incorrect case specifier'
			assert set(s) <= set(getattr(hexdigits,case)()), f'not {case}case hexadecimal symbols'
			assert not len(s) % 2,'odd-length string'
			if cls.width:
				assert len(s) == cls.width, f'Value is not {cls.width} characters wide'
			return str.__new__(cls,s)
		except Exception as e:
			return cls.init_fail(e,s)

class CoinTxID(HexStr):       color,width,hexcase = 'purple',64,'lower'
class WalletPassword(HexStr): color,width,hexcase = 'blue',32,'lower'
class MoneroViewKey(HexStr):  color,width,hexcase = 'cyan',64,'lower' # FIXME - no checking performed
class MMGenTxID(HexStr):      color,width,hexcase = 'red',6,'upper'

class WifKey(str,Hilite,InitErrors):
	"""
	Initialize a WIF key, checking its well-formedness.
	The numeric validity of the private key it encodes is not checked.
	"""
	width = 53
	color = 'blue'
	def __new__(cls,proto,wif):
		if type(wif) == cls:
			return wif
		try:
			assert set(wif) <= set(ascii_letters+digits),'not an ascii alphanumeric string'
			proto.parse_wif(wif) # raises exception on error
			return str.__new__(cls,wif)
		except Exception as e:
			return cls.init_fail(e,wif)

class PubKey(HexStr,MMGenObject): # TODO: add some real checks
	def __new__(cls,s,privkey):
		try:
			me = HexStr.__new__(cls,s,case='lower')
			me.privkey = privkey
			me.compressed = privkey.compressed
			return me
		except Exception as e:
			return cls.init_fail(e,s)

class PrivKey(str,Hilite,InitErrors,MMGenObject):
	"""
	Input:   a) raw, non-preprocessed bytes; or b) WIF key.
	Output:  preprocessed hexadecimal key, plus WIF key in 'wif' attribute
	For coins without a WIF format, 'wif' contains the preprocessed hex.
	The numeric validity of the resulting key is always checked.
	"""
	color = 'red'
	width = 64
	trunc_ok = False

	compressed = ImmutableAttr(bool,typeconv=False)
	wif        = ImmutableAttr(WifKey,typeconv=False)

	# initialize with (priv_bin,compressed), WIF or self
	def __new__(cls,proto,s=None,compressed=None,wif=None,pubkey_type=None):
		if type(s) == cls:
			return s
		if wif:
			try:
				assert s == None,"'wif' and key hex args are mutually exclusive"
				assert set(wif) <= set(ascii_letters+digits),'not an ascii alphanumeric string'
				k = proto.parse_wif(wif) # raises exception on error
				me = str.__new__(cls,k.sec.hex())
				me.compressed = k.compressed
				me.pubkey_type = k.pubkey_type
				me.wif = str.__new__(WifKey,wif) # check has been done
				me.orig_hex = None
				if k.sec != proto.preprocess_key(k.sec,k.pubkey_type):
					raise PrivateKeyError(
						f'{proto.cls_name} WIF key {me.wif!r} encodes private key with invalid value {me}')
				me.proto = proto
				return me
			except Exception as e:
				return cls.init_fail(e,s,objname=f'{proto.coin} WIF key')
		else:
			try:
				assert s,'private key bytes data missing'
				assert pubkey_type is not None,"'pubkey_type' arg missing"
				assert len(s) == cls.width // 2, f'key length must be {cls.width // 2} bytes'
				if pubkey_type == 'password': # skip WIF creation and pre-processing for passwds
					me = str.__new__(cls,s.hex())
				else:
					assert compressed is not None, "'compressed' arg missing"
					assert type(compressed) == bool,(
						f"'compressed' must be of type bool, not {type(compressed).__name__}" )
					me = str.__new__(cls,proto.preprocess_key(s,pubkey_type).hex())
					me.wif = WifKey(proto,proto.hex2wif(me,pubkey_type,compressed))
					me.compressed = compressed
				me.pubkey_type = pubkey_type
				me.orig_hex = s.hex() # save the non-preprocessed key
				me.proto = proto
				return me
			except Exception as e:
				return cls.init_fail(e,s)

class AddrListID(str,Hilite,InitErrors,MMGenObject):
	width = 10
	trunc_ok = False
	color = 'yellow'
	def __new__(cls,sid,mmtype):
		try:
			assert type(sid) == SeedID, f'{sid!r} not a SeedID instance'
			if not isinstance(mmtype,(MMGenAddrType,MMGenPasswordType)):
				raise ValueError(f'{mmtype!r}: not an instance of MMGenAddrType or MMGenPasswordType')
			me = str.__new__(cls,sid+':'+mmtype)
			me.sid = sid
			me.mmtype = mmtype
			return me
		except Exception as e:
			return cls.init_fail(e, f'sid={sid}, mmtype={mmtype}')

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
		for k in cls.forbidden,cls.allowed:
			assert type(k) == list
			for ch in k: assert type(ch) == str and len(ch) == 1
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

class SeedSplitSpecifier(str,Hilite,InitErrors,MMGenObject):
	color = 'red'
	def __new__(cls,s):
		if type(s) == cls:
			return s
		try:
			arr = s.split(':')
			assert len(arr) in (2,3), 'cannot be parsed'
			a,b,c = arr if len(arr) == 3 else ['default'] + arr
			me = str.__new__(cls,s)
			me.id = SeedSplitIDString(a)
			me.idx = SeedShareIdx(b)
			me.count = SeedShareCount(c)
			assert me.idx <= me.count, 'share index greater than share count'
			return me
		except Exception as e:
			return cls.init_fail(e,s)

class SeedSplitIDString(MMGenPWIDString):
	desc = 'seed split ID string'

class IPPort(str,Hilite,InitErrors,MMGenObject):
	color = 'yellow'
	width = 0
	trunc_ok = False
	min_len = 9  # 0.0.0.0:0
	max_len = 21 # 255.255.255.255:65535
	def __new__(cls,s):
		if type(s) == cls:
			return s
		try:
			m = re.fullmatch('{q}\.{q}\.{q}\.{q}:(\d{{1,10}})'.format(q=r'([0-9]{1,3})'),s)
			assert m is not None, f'{s!r}: invalid IP:HOST specifier'
			for e in m.groups():
				if len(e) != 1 and e[0] == '0':
					raise ValueError(f'{e}: leading zeroes not permitted in dotted decimal element or port number')
			res = [int(e) for e in m.groups()]
			for e in res[:4]:
				assert e <= 255, f'{e}: dotted decimal element > 255'
			assert res[4] <= 65535, f'{res[4]}: port number > 65535'
			me = str.__new__(cls,s)
			me.ip = '{}.{}.{}.{}'.format(*res)
			me.ip_num = sum( res[i] * ( 2 ** (-(i-3)*8) ) for i in range(4) )
			me.port = res[4]
			return me
		except Exception as e:
			return cls.init_fail(e,s)

from collections import namedtuple
ati = namedtuple('addrtype_info',
	['name','pubkey_type','compressed','gen_method','addr_fmt','wif_label','extra_attrs','desc'])

class MMGenAddrType(str,Hilite,InitErrors,MMGenObject):
	width = 1
	trunc_ok = False
	color = 'blue'

	name        = ImmutableAttr(str)
	pubkey_type = ImmutableAttr(str)
	compressed  = ImmutableAttr(bool,set_none_ok=True)
	gen_method  = ImmutableAttr(str,set_none_ok=True)
	addr_fmt    = ImmutableAttr(str,set_none_ok=True)
	wif_label   = ImmutableAttr(str,set_none_ok=True)
	extra_attrs = ImmutableAttr(tuple,set_none_ok=True)
	desc        = ImmutableAttr(str)

	mmtypes = {
		'L': ati('legacy',    'std', False,'p2pkh',   'p2pkh',   'wif', (), 'Legacy uncompressed address'),
		'C': ati('compressed','std', True, 'p2pkh',   'p2pkh',   'wif', (), 'Compressed P2PKH address'),
		'S': ati('segwit',    'std', True, 'segwit',  'p2sh',    'wif', (), 'Segwit P2SH-P2WPKH address'),
		'B': ati('bech32',    'std', True, 'bech32',  'bech32',  'wif', (), 'Native Segwit (Bech32) address'),
		'E': ati('ethereum',  'std', False,'ethereum','ethereum','privkey', ('wallet_passwd',),'Ethereum address'),
		'Z': ati('zcash_z','zcash_z',False,'zcash_z', 'zcash_z', 'wif',     ('viewkey',),      'Zcash z-address'),
		'M': ati('monero', 'monero', False,'monero',  'monero',  'spendkey',('viewkey','wallet_passwd'),'Monero address'),
	}
	def __new__(cls,proto,id_str,errmsg=None):
		if isinstance(id_str,cls):
			return id_str
		try:
			for k,v in cls.mmtypes.items():
				if id_str in (k,v.name):
					if id_str == v.name:
						id_str = k
					me = str.__new__(cls,id_str)
					for k in v._fields:
						setattr(me,k,getattr(v,k))
					if me not in proto.mmtypes + ('P',):
						raise ValueError(f'{me.name!r}: invalid address type for {proto.name} protocol')
					me.proto = proto
					return me
			raise ValueError(f'{id_str}: unrecognized address type for protocol {proto.name}')
		except Exception as e:
			return cls.init_fail( e,
				f"{errmsg or ''}{id_str!r}: invalid value for {cls.__name__} ({e!s})",
				preformat = True )

	@classmethod
	def get_names(cls):
		return [v.name for v in cls.mmtypes.values()]

class MMGenPasswordType(MMGenAddrType):
	mmtypes = {
		'P': ati('password', 'password', None, None, None, None, None, 'Password generated from MMGen seed')
	}
