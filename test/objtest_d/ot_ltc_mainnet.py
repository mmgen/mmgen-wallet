#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>

"""
test.objtest_d.ot_ltc_mainnet: LTC mainnet test vectors for MMGen data objects
"""

from decimal import Decimal

from mmgen.amt import LTCAmt
from mmgen.addr import CoinAddr
from mmgen.key import WifKey, PrivKey
from mmgen.protocol import init_proto

from .ot_common import r16, r32
from ..include.common import cfg

proto = init_proto(cfg, 'ltc', need_amt=True)

tests = {
	'LTCAmt': {
		'bad': ('-3.2', '0.123456789', 123, '123L', '88000000', 80999999.12345678),
		'good': (('80999999.12345678', Decimal('80999999.12345678')),)
	},
	'CoinAddr': {
		'bad': (
			{'addr': 1,   'proto': proto},
			{'addr': 'x', 'proto': proto},
			{'addr': 'я', 'proto': proto},
		),
		'good': (
			{'addr': 'LXYx4j8PDGE8GEwDFnEQhcLyHFGsRxSJwt', 'proto': proto},
			{'addr': 'MEnuCzUGHaQx9fK5WYvLwR1NK4SAo8HmSr', 'proto': proto},
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
			{'proto': proto, 'wif': '6udBAGS6B9RfGyvEQDkVDsWy3Kqv9eTULqtEfVkJtTJyHdLvojw',  'ret_idx': 1},
			{'proto': proto, 'wif': 'T7kCSp5E71jzV2zEJW4q5qU1SMB5CSz8D9VByxMBkamv1uM3Jjca', 'ret_idx': 1},
		)
	},
	'PrivKey': {
		'bad': (
			{'proto': proto, 'wif': 1},
			{'proto': proto, 'wif': '1'},
			{'proto': proto, 'wif': 'cMsqcmDYZP1LdKgqRh9L4ZRU9br28yvdmTPwW2YQwVSN9aQiMAoR'},
			{'proto': proto, 's': r32, 'wif': '6ufJhtQQiRYA3w2QvDuXNXuLgPFp15i3HR1Wp8An2mx1JnhhJAh'},
			{'proto': proto, 'pubkey_type': 'std'},
			{'proto': proto, 's': r32},
			{'proto': proto, 's': r32, 'compressed': 'yes'},
			{'proto': proto, 's': r32, 'compressed': 'yes', 'pubkey_type': 'std'},
			{'proto': proto, 's': r32, 'compressed': True, 'pubkey_type': 'nonstd'},
			{'proto': proto, 's': r32+b'x', 'compressed': True, 'pubkey_type': 'std'}
		),
		'good': (
			{'proto': proto, 'wif': '6ufJhtQQiRYA3w2QvDuXNXuLgPFp15i3HR1Wp8An2mx1JnhhJAh',
			'ret': bytes.fromhex('470a974ffca9fca1299b706b09142077bea3acbab6d6480b87dbba79d5fd279b')},
			{'proto': proto, 'wif': 'T41Fm7J3mtZLKYPMCLVSFARz4QF8nvSDhLAfW97Ds56Zm9hRJgn8',
			'ret': bytes.fromhex('1c6feab55a4c3b4ad1823d4ecacd1565c64228c01828cf44fb4db1e2d82c3d56')},
			{'proto': proto, 's': r32, 'compressed': False, 'pubkey_type': 'std', 'ret': r32},
			{'proto': proto, 's': r32, 'compressed': True, 'pubkey_type': 'std', 'ret': r32}
		)
	},
}
