#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>

"""
test.objtest_py_d.ot_ltc_testnet: LTC testnet test vectors for MMGen data objects
"""

from mmgen.obj import *
from .ot_common import *

tests = {
	'CoinAddr': {
		'bad':  (1,'x','я'),
		'good': ('n2D3joAy3yE5fqxUeCp38X6uPUcVn7EFw9','QN59YbnHsPQcbKWSq9PmTpjrhBnHGQqRmf')
	},
	'WifKey': {
		'bad':  (1,[],'\0','\1','я','g','gg','FF','f00',r16.hex(),'2MspvWFjBbkv2wzQGqhxJUYPCk3Y2jMaxLN'),
		'good': ('936Fd4qs3Zy2ZiYHH7vZ3UpT23KtCAiGiG2xBTkjHo7jE9aWA2f',
				'cQY3EumdaSNuttvDSUuPdiMYLyw8aVmYfFqxo9kdPuWbJBN4Ny66')
	},
	'PrivKey': {
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
			{'wif':'92iqzh6NqiKawyB1ronw66YtEHrU4rxRJ5T4aHniZqvuSVZS21f',
			'ret':'95b2aa7912550eacdd3844dcc14bee08ce7bc2434ad4858beb136021e945afeb'},
			{'wif':'cSaJAXBAm9ooHpVJgoxqjDG3AcareFy29Cz8mhnNTRijjv2HLgta',
			'ret':'94fa8b90c11fea8fb907c9376b919534b0a75b9a9621edf71a78753544b4101c'},
			{'s':r32,'compressed':False,'pubkey_type':'std','ret':r32.hex()},
			{'s':r32,'compressed':True,'pubkey_type':'std','ret':r32.hex()}
		)
	},
}
