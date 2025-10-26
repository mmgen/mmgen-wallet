#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>

"""
test.objtest_d.xmr_mainnet: XMR mainnet test vectors for MMGen data objects
"""

from mmgen.protocol import init_proto

from mmgen.addr import MMGenID

from ..include.common import cfg

proto = init_proto(cfg, 'xmr', need_amt=True)

tests = {
	'MMGenID': {
		'arg1': 'id_str',
		'bad': (
			{'id_str': 'F00BAA12',          'proto': proto},
			{'id_str': 'F00BAA12:C:99',     'proto': proto},
			{'id_str': 'F00BAA12:M',        'proto': proto},
			{'id_str': 'F00BAA12:M:',       'proto': proto},
			{'id_str': 'F00BAA12:M:99-FOO', 'proto': proto},
			{'id_str': 'F00BAA12:M:99-1',   'proto': proto},
			{'id_str': 'F00BAA12:M:99-x/y', 'proto': proto},
			{'id_str': 'F00BAA12:M:99-1/y', 'proto': proto},
			{'id_str': 'F00BAA12:M:0-1/1',  'proto': proto},
			{'id_str': 'F00BAA12:M:1-0/-1', 'proto': proto},
			{'id_str': 'F00BAA12:1-0/0',    'proto': proto},
			{'id_str': 'F00BAA12:M:1-111111/3', 'proto': proto},
		),
		'good': (
			{'id_str': 'F00BAA12:M:1', 'proto': proto},
			{'id_str': 'F00BAA12:M:1-0/0', 'proto': proto},
			{'id_str': 'F00BAA12:M:9999999-99999/99999', 'proto': proto},
		),
	},
}
