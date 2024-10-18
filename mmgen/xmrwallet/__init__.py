#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
xmrwallet.__init__: Monero wallet ops for the MMGen Suite
"""

import re, importlib
from collections import namedtuple

from ..proto.btc.common import b58a

from ..util import capfirst

tx_priorities = {
	1: 'low',
	2: 'normal',
	3: 'high',
	4: 'highest'
}

uargs = namedtuple('xmrwallet_uargs', [
	'infile',
	'wallets',
	'spec',
])

uarg_info = (
	lambda e, hp: {
		'daemon':          e('HOST:PORT', hp),
		'tx_relay_daemon': e('HOST:PORT[:PROXY_IP:PROXY_PORT]',     rf'({hp})(?::({hp}))?'),
		'newaddr_spec':    e('WALLET[:ACCOUNT][,"label text"]',     r'(\d+)(?::(\d+))?(?:,(.*))?'),
		'transfer_spec':   e('SOURCE:ACCOUNT:ADDRESS,AMOUNT',       rf'(\d+):(\d+):([{b58a}]+),([0-9.]+)'),
		'sweep_spec':      e('SOURCE:ACCOUNT[,DEST[:ACCOUNT]]',     r'(\d+):(\d+)(?:,(\d+)(?::(\d+))?)?'),
		'label_spec':      e('WALLET:ACCOUNT:ADDRESS,"label text"', r'(\d+):(\d+):(\d+),(.*)'),
	})(
		namedtuple('uarg_info_entry', ['annot','pat']),
		r'(?:[^:]+):(?:\d+)'
	)

# canonical op names mapped to their respective modules:
op_names = {
	'create':              'create',
	'create_offline':      'create',
	'sync':                'sync',
	'list':                'view',
	'view':                'view',
	'listview':            'view',
	'new':                 'new',
	'transfer':            'sweep',
	'sweep':               'sweep',
	'sweep_all':           'sweep',
	'relay':               'relay',
	'txview':              'txview',
	'txlist':              'txview',
	'label':               'label',
	'sign':                'sign',
	'submit':              'submit',
	'resubmit':            'submit',
	'abort':               'submit',
	'dump':                'dump',
	'restore':             'restore',
	'export_outputs':      'export',
	'export_outputs_sign': 'export',
	'import_outputs':      'import',
	'import_key_images':   'import',
	'wallet':              'wallet', # virtual class
}

kafile_arg_ops = (
	'create',
	'sync',
	'list',
	'view',
	'listview',
	'label',
	'new',
	'transfer',
	'sweep',
	'sweep_all',
	'dump',
	'restore')

opts = (
	'wallet_dir',
	'daemon',
	'tx_relay_daemon',
	'use_internal_keccak_module',
	'hash_preset',
	'restore_height',
	'no_start_wallet_daemon',
	'no_stop_wallet_daemon',
	'no_relay',
	'watch_only',
	'autosign',
	'skip_empty_accounts',
	'skip_empty_addresses')

pat_opts = ('daemon', 'tx_relay_daemon')

def op_cls(op_name):
	def upper(m):
		return m[1].upper()
	clsname = 'Op' + capfirst(re.sub(r'_(.)', upper, op_name))
	cls = getattr(importlib.import_module(f'.ops.{op_names[op_name]}', 'mmgen.xmrwallet'), clsname)
	cls.name = op_name
	return cls

def op(op, cfg, infile, wallets, spec=None):
	return op_cls(op.replace('-', '_'))(cfg, uargs(infile, wallets, spec))
