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
proto.btc.tx.op_return_data: Bitcoin OP_RETURN data class
"""

from ....obj import InitErrors

class OpReturnData(bytes, InitErrors):

	def __new__(cls, proto, data_spec):

		desc = 'OP_RETURN data'

		assert isinstance(data_spec, str), f'{desc} argument must be a string'

		if data_spec.startswith('hexdata:'):
			hexdata = data_spec[8:]
			from ....util import is_hex_str
			assert is_hex_str(hexdata), f'{hexdata!r}: {desc} hexdata not in hexadecimal format'
			assert not len(hexdata) % 2, f'{len(hexdata)}: {desc} hexdata of non-even length'
			ret = bytes.fromhex(hexdata)
		elif data_spec.startswith('data:'):
			try:
				ret = data_spec[5:].encode('utf8')
			except:
				raise ValueError(f'{desc} value must be UTF-8 encoded')
		else:
			raise ValueError(f'{desc} argument must start with ‘data:’ or ‘hexdata:’')

		assert 1 <= len(ret) <= proto.max_op_return_data_len, (
			f'{len(ret)}: invalid {desc} length: not in range 1-{proto.max_op_return_data_len}')

		return bytes.__new__(cls, ret)

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
		from ....color import blue, pink
		ret = str(self)
		if add_label:
			return blue('OP_RETURN data' + (' (hex): ' if self.display_hex else ': ')) + pink(ret)
		else:
			return pink(ret)
