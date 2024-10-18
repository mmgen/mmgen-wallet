#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>

"""
test.objtest_d.ot_ltc_testnet: LTC testnet test vectors for MMGen data objects
"""

from mmgen.addr import CoinAddr
from mmgen.key import WifKey, PrivKey
from mmgen.protocol import init_proto

from .ot_common import r16, r32
from ..include.common import cfg

proto = init_proto(cfg, 'ltc', network='testnet', need_amt=True)

tests = {
	'CoinAddr': {
		'bad': (
			{'addr': 1,   'proto': proto},
			{'addr': 'x', 'proto': proto},
			{'addr': 'я', 'proto': proto},
		),
		'good': (
			{'addr': 'n2D3joAy3yE5fqxUeCp38X6uPUcVn7EFw9', 'proto': proto},
			{'addr': 'QN59YbnHsPQcbKWSq9PmTpjrhBnHGQqRmf', 'proto': proto},
		),
	},
	'WifKey': {
		'bad': (
			{'proto': proto, 'wif': 1},
			{'proto': proto, 'wif': []},
			{'proto': proto, 'wif': '\0'},
			{'proto': proto, 'wif': '\1'},
			{'proto': proto, 'wif': 'я'},
			{'proto': proto, 'wif': 'g'},
			{'proto': proto, 'wif': 'gg'},
			{'proto': proto, 'wif': 'FF'},
			{'proto': proto, 'wif': 'f00'},
			{'proto': proto, 'wif': r16.hex()},
			{'proto': proto, 'wif': '2MspvWFjBbkv2wzQGqhxJUYPCk3Y2jMaxLN'},
		),
		'good': (
			{'proto': proto, 'wif': '936Fd4qs3Zy2ZiYHH7vZ3UpT23KtCAiGiG2xBTkjHo7jE9aWA2f',  'ret_idx': 1},
			{'proto': proto, 'wif': 'cQY3EumdaSNuttvDSUuPdiMYLyw8aVmYfFqxo9kdPuWbJBN4Ny66', 'ret_idx': 1},
		)
	},
	'PrivKey': {
		'bad': (
			{'proto': proto, 'wif': 1},
			{'proto': proto, 'wif': '1'},
			{'proto': proto, 'wif': '5KXEpVzjWreTcQoG5hX357s1969MUKNLuSfcszF6yu84kpsNZKb'},
			{'proto': proto, 's': r32, 'wif': '5KXEpVzjWreTcQoG5hX357s1969MUKNLuSfcszF6yu84kpsNZKb'},
			{'proto': proto, 'pubkey_type': 'std'},
			{'proto': proto, 's': r32},
			{'proto': proto, 's': r32, 'compressed': 'yes'},
			{'proto': proto, 's': r32, 'compressed': 'yes', 'pubkey_type': 'std'},
			{'proto': proto, 's': r32, 'compressed': True, 'pubkey_type': 'nonstd'},
			{'proto': proto, 's': r32+b'x', 'compressed': True, 'pubkey_type': 'std'}
		),
		'good': (
			{'proto': proto, 'wif': '92iqzh6NqiKawyB1ronw66YtEHrU4rxRJ5T4aHniZqvuSVZS21f',
			'ret': bytes.fromhex('95b2aa7912550eacdd3844dcc14bee08ce7bc2434ad4858beb136021e945afeb')},
			{'proto': proto, 'wif': 'cSaJAXBAm9ooHpVJgoxqjDG3AcareFy29Cz8mhnNTRijjv2HLgta',
			'ret': bytes.fromhex('94fa8b90c11fea8fb907c9376b919534b0a75b9a9621edf71a78753544b4101c')},
			{'proto': proto, 's': r32, 'compressed': False, 'pubkey_type': 'std', 'ret': r32},
			{'proto': proto, 's': r32, 'compressed': True, 'pubkey_type': 'std', 'ret': r32}
		)
	},
}
