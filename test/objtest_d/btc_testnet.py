#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>

"""
test.objtest_d.btc_testnet: BTC testnet test vectors for MMGen data objects
"""

from mmgen.key import PrivKey, WifKey
from mmgen.addr import CoinAddr
from mmgen.protocol import init_proto

from .common import r16, r32
from ..include.common import cfg

proto = init_proto(cfg, 'btc', network='testnet', need_amt=True)

tests = {
	'CoinAddr': {
		'bad': (
			{'addr': 1,   'proto': proto},
			{'addr': 'x', 'proto': proto},
			{'addr': 'я', 'proto': proto},
		),
		'good': (
			{'addr': 'n2FgXPKwuFkCXF946EnoxWJDWF2VwQ6q8J', 'proto': proto},
			{'addr': '2MspvWFjBbkv2wzQGqhxJUYPCk3Y2jMaxLN', 'proto': proto},
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
			{'proto': proto, 'wif': '93HsQEpH75ibaUJYi3QwwiQxnkW4dUuYFPXZxcbcKds7XrqHkY6',  'ret_idx': 1},
			{'proto': proto, 'wif': 'cMsqcmDYZP1LdKgqRh9L4ZRU9br28yvdmTPwW2YQwVSN9aQiMAoR', 'ret_idx': 1},
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
			{'proto': proto, 'wif': '93HsQEpH75ibaUJYi3QwwiQxnkW4dUuYFPXZxcbcKds7XrqHkY6',
			'ret': bytes.fromhex('e0aef965b905a2fedf907151df8e0a6bac832aa697801c51f58bd2ecb4fd381c')},
			{'proto': proto, 'wif': 'cMsqcmDYZP1LdKgqRh9L4ZRU9br28yvdmTPwW2YQwVSN9aQiMAoR',
			'ret': bytes.fromhex('08d0ed83b64b68d56fa064be48e2385060ed205be2b1e63cd56d218038c3a05f')},
			{'proto': proto, 's': r32, 'compressed': False, 'pubkey_type': 'std', 'ret': r32},
			{'proto': proto, 's': r32, 'compressed': True, 'pubkey_type': 'std', 'ret': r32}
		),
	},
}
