#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
baseconv: base conversion class for the MMGen suite
"""

from collections import namedtuple

from .util import die

def is_b58_str(s):
	return set(list(s)) <= set(baseconv('b58').digits)

def is_b32_str(s):
	return set(list(s)) <= set(baseconv('b32').digits)

def is_mmgen_mnemonic(s):
	try:
		baseconv('mmgen').tobytes(s.split(), pad='seed')
		return True
	except:
		return False

class baseconv:
	mn_base = 1626
	dt = namedtuple('desc_tuple', ['short', 'long'])
	constants = {
	'desc': {
		'b58':   dt('base58',             'base58-encoded data'),
		'b32':   dt('MMGen base32',       'MMGen base32-encoded data created using simple base conversion'),
		'b16':   dt('hexadecimal string', 'base16 (hexadecimal) string data'),
		'b10':   dt('base10 string',      'base10 (decimal) string data'),
		'b8':    dt('base8 string',       'base8 (octal) string data'),
		'b6d':   dt('base6d (die roll)',  'base6 data using the digits from one to six'),
		'mmgen': dt('MMGen native mnemonic',
		'MMGen native mnemonic seed phrase created using old Electrum wordlist and simple base conversion'),
	},
	# https://en.wikipedia.org/wiki/Base32#RFC_4648_Base32_alphabet
	# https://tools.ietf.org/html/rfc4648
	'digits': {
		'b58': tuple('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'),
		'b32': tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'), # RFC 4648 alphabet
		'b16': tuple('0123456789abcdef'),
		'b10': tuple('0123456789'),
		'b8':  tuple('01234567'),
		'b6d': tuple('123456'),
	},
	'wl_chksum': {
		'mmgen':  '5ca31424',
#		'tirosh': '48f05e1f', # tirosh truncated to mn_base
#		'tirosh1633': '1a5faeff' # tirosh list is 1633 words long!
	},
	'seedlen_map': {
		'b58':   {16:22, 24:33, 32:44},
		'b6d':   {16:50, 24:75, 32:100},
		'mmgen': {16:12, 24:18, 32:24},
	},
	'seedlen_map_rev': {
		'b58':   {22:16, 33:24, 44:32},
		'b6d':   {50:16, 75:24, 100:32},
		'mmgen': {12:16, 18:24, 24:32},
	}
	}

	def __init__(self, wl_id):

		if wl_id == 'mmgen':
			from .wordlist.electrum import words
			self.constants['digits'][wl_id] = words
		elif wl_id not in self.constants['digits']:
			raise ValueError(f'{wl_id}: unrecognized mnemonic ID')

		for k, v in self.constants.items():
			if wl_id in v:
				setattr(self, k, v[wl_id])

		self.wl_id = wl_id

	def get_wordlist(self):
		return self.digits

	def get_wordlist_chksum(self):
		from hashlib import sha256
		return sha256(' '.join(self.digits).encode()).hexdigest()[:8]

	def check_wordlist(self, cfg):

		wl = self.digits
		ret = f'Wordlist: {self.wl_id}\nLength: {len(wl)} words'
		new_chksum = self.get_wordlist_chksum()

		cfg._util.compare_chksums(new_chksum, 'generated', self.wl_chksum, 'saved', die_on_fail=True)

		if tuple(sorted(wl)) == wl:
			return ret + '\nList is sorted'
		else:
			die(3, 'ERROR: List is not sorted!')

	@staticmethod
	def get_pad(pad, seed_pad_func):
		"""
		'pad' argument to baseconv conversion methods must be either None, 'seed' or an integer.
		If None, output of minimum (but never zero) length will be produced.
		If 'seed', output length will be mapped from input length using data in seedlen_map.
		If an integer, the string, hex string or byte output will be padded to this length.
		"""
		if pad is None:
			return 0
		elif type(pad) is int:
			return pad
		elif pad == 'seed':
			return seed_pad_func()
		else:
			die('BaseConversionPadError', f"{pad!r}: illegal value for 'pad' (must be None, 'seed' or int)")

	def tohex(self, words_arg, pad=None):
		"convert string or list data of instance base to a hexadecimal string"
		return self.tobytes(words_arg, pad//2 if type(pad) is int else pad).hex()

	def tobytes(self, words_arg, pad=None):
		"convert string or list data of instance base to byte string"

		words = words_arg if isinstance(words_arg, (list, tuple)) else tuple(words_arg.strip())
		desc = self.desc.short

		if len(words) == 0:
			die('BaseConversionError', f'empty {desc} data')

		def get_seed_pad():
			assert hasattr(self, 'seedlen_map_rev'), f'seed padding not supported for base {self.wl_id!r}'
			d = self.seedlen_map_rev
			if not len(words) in d:
				die('BaseConversionError',
					f'{len(words)}: invalid length for seed-padded {desc} data in base conversion')
			return d[len(words)]

		pad_val = max(self.get_pad(pad, get_seed_pad), 1)
		wl = self.digits
		base = len(wl)

		if not set(words) <= set(wl):
			die('BaseConversionError',
				('seed data' if pad == 'seed' else f'{words_arg!r}:') +
				f' not in {desc} format')

		ret = sum(wl.index(words[::-1][i])*(base**i) for i in range(len(words)))
		bl = ret.bit_length()
		return ret.to_bytes(max(pad_val, bl//8+bool(bl%8)), 'big')

	def fromhex(self, hexstr, pad=None, tostr=False):
		"convert a hexadecimal string to a list or string data of instance base"

		from .util import is_hex_str
		if not is_hex_str(hexstr):
			die('HexadecimalStringError',
				('seed data' if pad == 'seed' else f'{hexstr!r}:') +
				' not a hexadecimal string')

		return self.frombytes(bytes.fromhex(hexstr), pad, tostr)

	def frombytes(self, bytestr, pad=None, tostr=False):
		"convert byte string to list or string data of instance base"

		if not bytestr:
			die('BaseConversionError', 'empty data not allowed in base conversion')

		def get_seed_pad():
			assert hasattr(self, 'seedlen_map'), f'seed padding not supported for base {self.wl_id!r}'
			d = self.seedlen_map
			if not len(bytestr) in d:
				die('SeedLengthError',
					f'{len(bytestr)}: invalid byte length for seed data in seed-padded base conversion')
			return d[len(bytestr)]

		pad = max(self.get_pad(pad, get_seed_pad), 1)
		wl = self.digits

		def gen():
			num = int.from_bytes(bytestr, 'big')
			base = len(wl)
			while num:
				yield num % base
				num //= base

		ret = list(gen())
		o = [wl[n] for n in [0] * (pad-len(ret)) + ret[::-1]]

		return (' ' if self.wl_id == 'mmgen' else '').join(o) if tostr else o
