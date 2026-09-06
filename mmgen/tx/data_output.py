#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
tx.data_output: transaction data output class
"""

from ..obj import InitErrors

class DataOutput(bytes, InitErrors):

	def __new__(base_cls, proto, data_spec):

		cls = proto.base_proto_subclass(base_cls, 'tx.data_output')

		assert isinstance(data_spec, str), f'{cls.desc} argument must be a string'

		if data_spec.startswith('hexdata:'):
			hexdata = data_spec[8:]
			from ..util import is_hex_str
			assert is_hex_str(hexdata), f'{hexdata!r}: {cls.desc} hexdata not in hexadecimal format'
			assert not len(hexdata) % 2, f'{len(hexdata)}: {cls.desc} hexdata of non-even length'
			ret = bytes.fromhex(hexdata)
		elif data_spec.startswith('data:'):
			try:
				ret = data_spec[5:].encode('utf8')
			except:
				raise ValueError(f'{cls.desc} value must be UTF-8 encoded')
		else:
			raise ValueError(f'{cls.desc} argument must start with ‘data:’ or ‘hexdata:’')

		return bytes.__new__(cls, ret)

	def __init__(self, proto, data_spec):

		self.proto = proto

		assert 1 <= len(self) <= self.max_len, (
			f'{len(self)}: invalid {self.desc} length: not in range 1-{self.max_len}')

	def __repr__(self):
		'return an initialization string'
		ret = str(self)
		return ('hexdata:' if self.display_hex else 'data:') + ret

	def __str__(self):
		'return something suitable for display to the user'
		self.display_hex = True
		try:
			ret = self.decode('utf8')
		except:
			return self.hex()
		else:
			import unicodedata
			for ch in ret:
				if ch == '\n' or unicodedata.category(ch)[0] in ('C', 'M'): # see MMGenLabel
					return self.hex()
			self.display_hex = False
			return ret

	def hl(self, *, add_label=False):
		'colorize and optionally label the result of str()'
		from ..color import blue, pink
		ret = str(self)
		if add_label:
			return blue(self.desc + (' (hex): ' if self.display_hex else ': ')) + pink(ret)
		else:
			return pink(ret)
