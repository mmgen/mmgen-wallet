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
amt: MMGen CoinAmt and related classes
"""

from decimal import Decimal
from .objmethods import Hilite, InitErrors

class CoinAmt(Decimal, Hilite, InitErrors): # abstract class
	"""
	Instantiating with 'from_decimal' rounds value down to 'max_prec' precision.
	For addition and subtraction, operand types must match.
	For multiplication and division, operand types may differ.
	Negative amounts, floor division and modulus operation are unimplemented.

	Decimal precision is set in init_proto()
	"""
	coin = 'Coin'
	color = 'yellow'

	max_prec = 0      # number of decimal places for this coin
	max_amt  = None   # coin supply if known, otherwise None
	units    = ()     # defined unit names, e.g. ('satoshi',...)

	def __new__(cls, num, from_unit=None, from_decimal=False):

		if isinstance(num, CoinAmt):
			raise TypeError(f'CoinAmt: {num} is instance of {cls.__name__}')

		try:
			if from_unit:
				assert from_unit in cls.units, f'{from_unit!r}: unrecognized coin unit for {cls.__name__}'
				assert type(num) is int, 'value is not an integer'
				me = Decimal.__new__(cls, num * getattr(cls, from_unit))
			elif from_decimal:
				assert isinstance(num, Decimal), f'number must be of type Decimal, not {type(num).__name__})'
				me = Decimal.__new__(cls, num.quantize(Decimal('10') ** -cls.max_prec))
			else:
				assert isinstance(num, str), f'non-string passed to {cls.__name__} initializer'
				me = Decimal.__new__(cls, num)
			assert me.normalize().as_tuple()[-1] >= -cls.max_prec, 'too many decimal places in coin amount'
			if cls.max_amt:
				assert me <= cls.max_amt, f'{me}: coin amount too large (>{cls.max_amt})'
			assert me >= 0, 'coin amount cannot be negative'
			return me
		except Exception as e:
			return cls.init_fail(e, num)

	def to_unit(self, unit):
		return int(Decimal(self) // getattr(self, unit))

	@classmethod
	def fmtc(cls, *args, **kwargs):
		cls.method_not_implemented()

	def fmt(self, color=False, iwidth=1, prec=None): # iwidth: width of the integer part
		prec = prec or self.max_prec
		if '.' in (s := str(self)):
			a, b = s.split('.', 1)
			return self.colorize(
				a.rjust(iwidth) + '.' + b.ljust(prec)[:prec], # truncation, not rounding!
				color = color)
		else:
			return self.colorize(
				s.rjust(iwidth).ljust(iwidth+prec+1),
				color = color)

	def hl(self, color=True):
		return self.colorize(str(self), color=color)

	# fancy highlighting with coin unit, enclosure, formatting
	def hl2(self, color=True, unit=False, fs='{}', encl=''):
		res = fs.format(self)
		return (
			encl[:-1]
			+ self.colorize(
				(res.rstrip('0').rstrip('.') if '.' in res else res) +
				(' ' + self.coin if unit else ''),
				color = color)
			+ encl[1:]
		)

	def __str__(self): # format simply, with no exponential notation
		return str(int(self)) if int(self) == self else self.normalize().__format__('f')

	def __repr__(self):
		return "{}('{}')".format(type(self).__name__, self.__str__())

	def __add__(self, other, *args, **kwargs):
		"""
		we must allow other to be int(0) to use the sum() builtin
		"""
		if type(other) is type(self) or (other == 0 and isinstance(other, int)):
			return type(self)(Decimal.__add__(self, other, *args, **kwargs),  from_decimal=True)
		raise TypeError(
			f'operand {other} is of incorrect type ({type(other).__name__} != {type(self).__name__})')

	__radd__ = __add__

	def __sub__(self, other, *args, **kwargs):
		if type(other) is type(self):
			return type(self)(Decimal.__sub__(self, other, *args, **kwargs),  from_decimal=True)
		raise TypeError(
			f'operand {other} is of incorrect type ({type(other).__name__} != {type(self).__name__})')

	def __rsub__(self, other, *args, **kwargs):
		if type(other) is type(self):
			return type(self)(Decimal.__rsub__(self, other, *args, **kwargs),  from_decimal=True)
		raise TypeError(
			f'operand {other} is of incorrect type ({type(other).__name__} != {type(self).__name__})')

	def __mul__(self, other, *args, **kwargs):
		return type(self)('{:0.{p}f}'.format(
			Decimal.__mul__(self, Decimal(other), *args, **kwargs),
			p = self.max_prec
		))

	__rmul__ = __mul__

	def __truediv__(self, other, *args, **kwargs):
		return type(self)('{:0.{p}f}'.format(
			Decimal.__truediv__(self, Decimal(other), *args, **kwargs),
			p = self.max_prec
		))

	def __rtruediv__(self, other, *args, **kwargs):
		return type(self)('{:0.{p}f}'.format(
			Decimal.__rtruediv__(self, Decimal(other), *args, **kwargs),
			p = self.max_prec
		))

	def __neg__(self, *args, **kwargs):
		self.method_not_implemented()

	def __floordiv__(self, *args, **kwargs):
		self.method_not_implemented()

	def __mod__(self, *args, **kwargs):
		self.method_not_implemented()

class BTCAmt(CoinAmt):
	coin = 'BTC'
	max_prec = 8
	max_amt = 21000000
	satoshi = Decimal('0.00000001')
	units = ('satoshi',)

class BCHAmt(BTCAmt):
	coin = 'BCH'

class LTCAmt(BTCAmt):
	coin = 'LTC'
	max_amt = 84000000

class XMRAmt(CoinAmt):
	coin = 'XMR'
	max_prec = 12
	atomic = Decimal('0.000000000001')
	units = ('atomic',)

# Kwei (babbage) 3, Mwei (lovelace) 6, Gwei (shannon) 9, µETH (szabo) 12, mETH (finney) 15, ETH 18
class ETHAmt(CoinAmt):
	coin    = 'ETH'
	max_prec = 18
	wei     = Decimal('0.000000000000000001')
	Kwei    = Decimal('0.000000000000001')
	Mwei    = Decimal('0.000000000001')
	Gwei    = Decimal('0.000000001')
	szabo   = Decimal('0.000001')
	finney  = Decimal('0.001')
	units   = ('wei', 'Kwei', 'Mwei', 'Gwei', 'szabo', 'finney')

	def toWei(self):
		return int(Decimal(self) // self.wei)

class ETCAmt(ETHAmt):
	coin = 'ETC'

def CoinAmtChk(proto, num):
	assert type(num) is proto.coin_amt, f'CoinAmtChk: {type(num)} != {proto.coin_amt}'
	return num
