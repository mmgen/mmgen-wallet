#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
rpc.util: RPC library utility functions for the MMGen Project
"""

import re, json
from collections import namedtuple

from ..util import msg, pp_fmt
from ..objmethods import HiliteStr, InitErrors

def dmsg_rpc(fs, data=None, *, is_json=False):
	msg(
		fs if data is None else
		fs.format(pp_fmt(json.loads(data) if is_json else data))
	)

def dmsg_rpc_backend(host_url, host_path, payload):
	msg(
		f'\n    RPC URL: {host_url}{host_path}' +
		'\n    RPC PAYLOAD data (httplib) ==>' +
		f'\n{pp_fmt(payload)}\n')

def noop(*args, **kwargs):
	pass

auth_data = namedtuple('rpc_auth_data', ['user', 'passwd'])

class json_encoder(json.JSONEncoder):
	def default(self, o):
		if type(o).__name__.endswith('Amt'):
			return str(o)
		else:
			return json.JSONEncoder.default(self, o)

class IPPort(HiliteStr, InitErrors):
	color = 'yellow'
	width = 0
	trunc_ok = False
	min_len = 9  # 0.0.0.0:0
	max_len = 21 # 255.255.255.255:65535
	def __new__(cls, s):
		if isinstance(s, cls):
			return s
		try:
			m = re.fullmatch(r'{q}\.{q}\.{q}\.{q}:(\d{{1,10}})'.format(q=r'([0-9]{1,3})'), s)
			assert m is not None, f'{s!r}: invalid IP:HOST specifier'
			for e in m.groups():
				if len(e) != 1 and e[0] == '0':
					raise ValueError(f'{e}: leading zeroes not permitted in dotted decimal element or port number')
			res = [int(e) for e in m.groups()]
			for e in res[:4]:
				assert e <= 255, f'{e}: dotted decimal element > 255'
			assert res[4] <= 65535, f'{res[4]}: port number > 65535'
			me = str.__new__(cls, s)
			me.ip = '{}.{}.{}.{}'.format(*res)
			me.ip_num = sum(res[i] * (2 ** (-(i-3)*8)) for i in range(4))
			me.port = res[4]
			return me
		except Exception as e:
			return cls.init_fail(e, s)
