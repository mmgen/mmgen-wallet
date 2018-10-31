#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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
altcoins.eth.obj: Ethereum data type classes for the MMGen suite
"""

# Kwei (babbage) 3, Mwei (lovelace) 6, Gwei (shannon) 9, µETH (szabo) 12, mETH (finney) 15, ETH 18
from decimal import Decimal
from mmgen.color import *
from mmgen.obj import *
class ETHAmt(BTCAmt):
	max_prec = 18
	max_amt = None
	wei     = Decimal('0.000000000000000001')
	Kwei    = Decimal('0.000000000000001')
	Mwei    = Decimal('0.000000000001')
	Gwei    = Decimal('0.000000001')
	szabo   = Decimal('0.000001')
	finney  = Decimal('0.001')
	min_coin_unit = wei
	units = ('wei','Kwei','Mwei','Gwei','szabo','finney')
	amt_fs = '4.18'

	def toWei(self):    return int(Decimal(self) // self.wei)
	def toKwei(self):   return int(Decimal(self) // self.Kwei)
	def toMwei(self):   return int(Decimal(self) // self.Mwei)
	def toGwei(self):   return int(Decimal(self) // self.Gwei)
	def toSzabo(self):  return int(Decimal(self) // self.szabo)
	def toFinney(self): return int(Decimal(self) // self.finney)

class ETHNonce(int,Hilite,InitErrors): # WIP
	def __new__(cls,n,on_fail='die'):
		if type(n) == cls: return n
		cls.arg_chk(cls,on_fail)
		from mmgen.util import is_int
		try:
			assert is_int(n),"'{}': value is not an integer".format(n)
			me = int.__new__(cls,n)
			return me
		except Exception as e:
			m = "{!r}: value cannot be converted to ETH nonce ({})"
			return cls.init_fail(m.format(n,e.message),on_fail)

	@classmethod
	def colorize(cls,s,color=True):
		k = color if type(color) is str else cls.color # hack: override color with str value
		return globals()[k](str(s)) if (color or cls.color_always) else str(s)
