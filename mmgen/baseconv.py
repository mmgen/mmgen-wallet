#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>
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
baseconv.py:  base conversion class for the MMGen suite
"""

from hashlib import sha256
from mmgen.exception import *

def is_b58_str(s): return set(list(s)) <= set(baseconv.digits['b58'])
def is_b32_str(s): return set(list(s)) <= set(baseconv.digits['b32'])

class baseconv(object):

	desc = {
		'b58':   ('base58',            'base58-encoded data'),
		'b32':   ('MMGen base32',      'MMGen base32-encoded data created using simple base conversion'),
		'b16':   ('hexadecimal string','base16 (hexadecimal) string data'),
		'b10':   ('base10 string',     'base10 (decimal) string data'),
		'b8':    ('base8 string',      'base8 (octal) string data'),
		'b6d':   ('base6d (die roll)', 'base6 data using the digits from one to six'),
		'tirosh':('Tirosh mnemonic',   'base1626 mnemonic using truncated Tirosh wordlist'), # not used by wallet
		'mmgen': ('MMGen native mnemonic',
		'MMGen native mnemonic seed phrase data created using old Electrum wordlist and simple base conversion'),
	}
	# https://en.wikipedia.org/wiki/Base32#RFC_4648_Base32_alphabet
	# https://tools.ietf.org/html/rfc4648
	digits = {
		'b58': tuple('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'),
		'b32': tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'), # RFC 4648 alphabet
		'b16': tuple('0123456789abcdef'),
		'b10': tuple('0123456789'),
		'b8':  tuple('01234567'),
		'b6d': tuple('123456'),
	}
	mn_base = 1626 # tirosh list is 1633 words long!
	wl_chksums = {
		'mmgen':  '5ca31424',
		'tirosh': '48f05e1f', # tirosh truncated to mn_base (1626)
		# 'tirosh1633': '1a5faeff'
	}
	seedlen_map = {
		'b58': { 16:22, 24:33, 32:44 },
		'b6d': { 16:50, 24:75, 32:100 },
	}
	seedlen_map_rev = {
		'b58': { 22:16, 33:24, 44:32 },
		'b6d': { 50:16, 75:24, 100:32 },
	}

	@classmethod
	def init_mn(cls,mn_id):
		if mn_id in cls.digits:
			return
		if mn_id == 'mmgen':
			from mmgen.mn_electrum import words
			cls.digits[mn_id] = words
		elif mn_id == 'tirosh':
			from mmgen.mn_tirosh import words
			cls.digits[mn_id] = words[:cls.mn_base]
		else:
			raise ValueError('{}: unrecognized mnemonic ID'.format(mn_id))

	@classmethod
	def get_wordlist(cls,wl_id):
		cls.init_mn(wl_id)
		return cls.digits[wl_id]

	@classmethod
	def get_wordlist_chksum(cls,wl_id):
		cls.init_mn(wl_id)
		return sha256(' '.join(cls.digits[wl_id]).encode()).hexdigest()[:8]

	@classmethod
	def check_wordlists(cls):
		for k,v in list(cls.wl_chksums.items()):
			res = cls.get_wordlist_chksum(k)
			assert res == v,'{}: checksum mismatch for {} (should be {})'.format(res,k,v)

	@classmethod
	def check_wordlist(cls,wl_id):
		cls.init_mn(wl_id)

		wl = cls.digits[wl_id]
		from mmgen.util import qmsg,compare_chksums
		qmsg('Wordlist: {}\nLength: {} words'.format(wl_id,len(wl)))
		new_chksum = cls.get_wordlist_chksum(wl_id)

		a,b = 'generated','saved'
		compare_chksums(new_chksum,a,cls.wl_chksums[wl_id],b,die_on_fail=True)

		qmsg('List is sorted') if tuple(sorted(wl)) == wl else die(3,'ERROR: List is not sorted!')

	@classmethod
	def get_pad(cls,pad,seed_pad_func):
		"""
		'pad' argument to baseconv conversion methods must be either None, 'seed' or an integer.
		If None, output of minimum (but never zero) length will be produced.
		If 'seed', output length will be mapped from input length using data in seedlen_map.
		If an integer, the string, hex string or byte output will be padded to this length.
		"""
		if pad == None:
			return 0
		elif type(pad) == int:
			return pad
		elif pad == 'seed':
			return seed_pad_func()
		else:
			m = "{!r}: illegal value for 'pad' (must be None,'seed' or int)"
			raise BaseConversionPadError(m.format(pad))

	@classmethod
	def tohex(cls,words_arg,wl_id,pad=None):
		"convert string or list data of base 'wl_id' to hex string"
		return cls.tobytes(words_arg,wl_id,pad//2 if type(pad)==int else pad).hex()

	@classmethod
	def tobytes(cls,words_arg,wl_id,pad=None):
		"convert string or list data of base 'wl_id' to byte string"

		if wl_id not in cls.digits:
			cls.init_mn(wl_id)

		words = words_arg if isinstance(words_arg,(list,tuple)) else tuple(words_arg.strip())
		desc = cls.desc[wl_id][0]

		if len(words) == 0:
			raise BaseConversionError('empty {} data'.format(desc))

		def get_seed_pad():
			assert wl_id in cls.seedlen_map_rev,'seed padding not supported for base {!r}'.format(wl_id)
			d = cls.seedlen_map_rev[wl_id]
			if not len(words) in d:
				m = '{}: invalid length for seed-padded {} data in base conversion'
				raise BaseConversionError(m.format(len(words),desc))
			return d[len(words)]

		pad_val = max(cls.get_pad(pad,get_seed_pad),1)
		wl = cls.digits[wl_id]
		base = len(wl)

		if not set(words) <= set(wl):
			m = ('{w!r}:','seed data')[pad=='seed'] + ' not in {d} format'
			raise BaseConversionError(m.format(w=words_arg,d=desc))

		ret = sum([wl.index(words[::-1][i])*(base**i) for i in range(len(words))])
		bl = ret.bit_length()
		return ret.to_bytes(max(pad_val,bl//8+bool(bl%8)),'big')

	@classmethod
	def fromhex(cls,hexstr,wl_id,pad=None,tostr=False):
		"convert hex string to list or string data of base 'wl_id'"

		from mmgen.util import is_hex_str
		if not is_hex_str(hexstr):
			m = ('{h!r}:','seed data')[pad=='seed'] + ' not a hexadecimal string'
			raise HexadecimalStringError(m.format(h=hexstr))

		return cls.frombytes(bytes.fromhex(hexstr),wl_id,pad,tostr)

	@classmethod
	def frombytes(cls,bytestr,wl_id,pad=None,tostr=False):
		"convert byte string to list or string data of base 'wl_id'"

		if wl_id not in cls.digits:
			cls.init_mn(wl_id)

		if not bytestr:
			raise BaseConversionError('empty data not allowed in base conversion')

		def get_seed_pad():
			assert wl_id in cls.seedlen_map,'seed padding not supported for base {!r}'.format(wl_id)
			d = cls.seedlen_map[wl_id]
			if not len(bytestr) in d:
				m = '{}: invalid byte length for seed data in seed-padded base conversion'
				raise SeedLengthError(m.format(len(bytestr)))
			return d[len(bytestr)]

		pad = max(cls.get_pad(pad,get_seed_pad),1)
		wl = cls.digits[wl_id]
		base = len(wl)

		num = int.from_bytes(bytestr,'big')
		ret = []
		while num:
			ret.append(num % base)
			num //= base
		o = [wl[n] for n in [0] * (pad-len(ret)) + ret[::-1]]
		return ''.join(o) if tostr else o
