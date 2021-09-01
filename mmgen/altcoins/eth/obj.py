#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2021 The MMGen Project <mmgen@tuta.io>
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

from decimal import Decimal
from mmgen.obj import BTCAmt,Int

# Kwei (babbage) 3, Mwei (lovelace) 6, Gwei (shannon) 9, µETH (szabo) 12, mETH (finney) 15, ETH 18
class ETHAmt(BTCAmt):
	max_prec = 18
	max_amt = None
	wei     = Decimal('0.000000000000000001')
	Kwei    = Decimal('0.000000000000001')
	Mwei    = Decimal('0.000000000001')
	Gwei    = Decimal('0.000000001')
	szabo   = Decimal('0.000001')
	finney  = Decimal('0.001')
	units = ('wei','Kwei','Mwei','Gwei','szabo','finney')
	amt_fs = '4.18'

	def toWei(self):    return int(Decimal(self) // self.wei)
	def toKwei(self):   return int(Decimal(self) // self.Kwei)
	def toMwei(self):   return int(Decimal(self) // self.Mwei)
	def toGwei(self):   return int(Decimal(self) // self.Gwei)
	def toSzabo(self):  return int(Decimal(self) // self.szabo)
	def toFinney(self): return int(Decimal(self) // self.finney)

class ETHNonce(Int):
	min_val = 0
