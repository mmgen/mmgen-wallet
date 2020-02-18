#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>

"""
test.objtest_py_d.ot_ltc_mainnet: LTC mainnet test vectors for MMGen data objects
"""

from collections import OrderedDict

from mmgen.obj import *
from .ot_common import *

tests = OrderedDict([
	('LTCAmt', {
		'bad':  ('-3.2','0.123456789',123,'123L','88000000',80999999.12345678),
		'good': (('80999999.12345678',Decimal('80999999.12345678')),)
	}),
	('CoinAddr', {
		'bad':  (1,'x','я'),
		'good': ('LXYx4j8PDGE8GEwDFnEQhcLyHFGsRxSJwt','MEnuCzUGHaQx9fK5WYvLwR1NK4SAo8HmSr'),
	}),
	('WifKey', {
		'bad':  (1,[],'\0','\1','я','g','gg','FF','f00',r16.hex(),'2MspvWFjBbkv2wzQGqhxJUYPCk3Y2jMaxLN'),
		'good': ('6udBAGS6B9RfGyvEQDkVDsWy3Kqv9eTULqtEfVkJtTJyHdLvojw',
				'T7kCSp5E71jzV2zEJW4q5qU1SMB5CSz8D9VByxMBkamv1uM3Jjca'),
	}),
	('PrivKey', {
		'bad': (
			{'wif':1},
			{'wif':'1'},
			{'wif':'cMsqcmDYZP1LdKgqRh9L4ZRU9br28yvdmTPwW2YQwVSN9aQiMAoR'},
			{'s':r32,'wif':'6ufJhtQQiRYA3w2QvDuXNXuLgPFp15i3HR1Wp8An2mx1JnhhJAh'},
			{'pubkey_type':'std'},
			{'s':r32},
			{'s':r32,'compressed':'yes'},
			{'s':r32,'compressed':'yes','pubkey_type':'std'},
			{'s':r32,'compressed':True,'pubkey_type':'nonstd'},
			{'s':r32+b'x','compressed':True,'pubkey_type':'std'}
		),
		'good': (
			{'wif':'6ufJhtQQiRYA3w2QvDuXNXuLgPFp15i3HR1Wp8An2mx1JnhhJAh',
			'ret':'470a974ffca9fca1299b706b09142077bea3acbab6d6480b87dbba79d5fd279b'},
			{'wif':'T41Fm7J3mtZLKYPMCLVSFARz4QF8nvSDhLAfW97Ds56Zm9hRJgn8',
			'ret':'1c6feab55a4c3b4ad1823d4ecacd1565c64228c01828cf44fb4db1e2d82c3d56'},
			{'s':r32,'compressed':False,'pubkey_type':'std','ret':r32.hex()},
			{'s':r32,'compressed':True,'pubkey_type':'std','ret':r32.hex()}
		)
	}),
])
