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
amt.py: MMGen CoinAmt and related classes
"""

from decimal import Decimal
from .objmethods import Hilite,InitErrors

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

class BCHAmt(BTCAmt):
	pass

class B2XAmt(BTCAmt):
	pass

class LTCAmt(BTCAmt):
	max_amt = 84000000

class XMRAmt(CoinAmt):
	max_prec = 12
	atomic = Decimal('0.000000000001')
	units = ('atomic',)
	amt_fs = '4.12'
