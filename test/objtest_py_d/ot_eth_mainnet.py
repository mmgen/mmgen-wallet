#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>

"""
test.objtest_py_d.ot_eth_mainnet: ETH mainnet test vectors for MMGen data objects
"""

from collections import OrderedDict

from mmgen.obj import *
from .ot_common import *

tests = OrderedDict([
	('ETHAmt', {
		'bad':  ('-3.2','0.1234567891234567891',123,'123L',
					{'num':'1','from_decimal':True},
					{'num':1,'from_decimal':True},
				),
		'good': (('123.123456789123456789',Decimal('123.123456789123456789')),
				{   'num':Decimal('1.12345678912345678892345'), # rounding
					'from_decimal':True,
					'ret':Decimal('1.123456789123456789')},
				{'num':Decimal('1.234'),'from_decimal':True,'ret':Decimal('1.234')},
				{'num':Decimal('0.0'),'from_decimal':True,'ret':Decimal('0')},
				{'num':1234,'from_unit':'wei','ret':Decimal('0.000000000000001234')},
				{'num':1234,'from_unit':'Mwei','ret':Decimal('0.000000001234')},
		)
	}),
	('ETHNonce', {
		'bad': ('U','z','я',-1),
		'good':  (('0',0),('1',1),('100',100),1,100)
	}),
])
