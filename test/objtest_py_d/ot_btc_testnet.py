#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>

"""
test.objtest_py_d.ot_btc_testnet: BTC testnet test vectors for MMGen data objects
"""

from collections import OrderedDict

from mmgen.obj import *
from .ot_common import *

tests = OrderedDict([
	('CoinAddr', {
		'bad':  (1,'x','я'),
		'good': ('n2FgXPKwuFkCXF946EnoxWJDWF2VwQ6q8J','2MspvWFjBbkv2wzQGqhxJUYPCk3Y2jMaxLN'),
	}),
	('WifKey', {
		'bad':  (1,[],'\0','\1','я','g','gg','FF','f00',r16.hex(),'2MspvWFjBbkv2wzQGqhxJUYPCk3Y2jMaxLN'),
		'good': ('93HsQEpH75ibaUJYi3QwwiQxnkW4dUuYFPXZxcbcKds7XrqHkY6',
				'cMsqcmDYZP1LdKgqRh9L4ZRU9br28yvdmTPwW2YQwVSN9aQiMAoR'),
	}),
	('PrivKey', {
		'bad': (
			{'wif':1},
			{'wif':'1'},
			{'wif':'5KXEpVzjWreTcQoG5hX357s1969MUKNLuSfcszF6yu84kpsNZKb'},
			{'s':r32,'wif':'5KXEpVzjWreTcQoG5hX357s1969MUKNLuSfcszF6yu84kpsNZKb'},
			{'pubkey_type':'std'},
			{'s':r32},
			{'s':r32,'compressed':'yes'},
			{'s':r32,'compressed':'yes','pubkey_type':'std'},
			{'s':r32,'compressed':True,'pubkey_type':'nonstd'},
			{'s':r32+b'x','compressed':True,'pubkey_type':'std'}
		),
		'good': (
			{'wif':'93HsQEpH75ibaUJYi3QwwiQxnkW4dUuYFPXZxcbcKds7XrqHkY6',
			'ret':'e0aef965b905a2fedf907151df8e0a6bac832aa697801c51f58bd2ecb4fd381c'},
			{'wif':'cMsqcmDYZP1LdKgqRh9L4ZRU9br28yvdmTPwW2YQwVSN9aQiMAoR',
			'ret':'08d0ed83b64b68d56fa064be48e2385060ed205be2b1e63cd56d218038c3a05f'},
			{'s':r32,'compressed':False,'pubkey_type':'std','ret':r32.hex()},
			{'s':r32,'compressed':True,'pubkey_type':'std','ret':r32.hex()}
		)
	})
])
