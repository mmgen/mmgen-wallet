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
xmrseed: Monero mnemonic conversion class for the MMGen suite
"""

from .baseconv import baseconv
from .util import die

def is_xmrseed(s):
	return bool(xmrseed().tobytes(s.split()))

# implements a subset of the baseconv API
class xmrseed(baseconv):

	desc            = baseconv.dt('Monero mnemonic', 'Monero new-style mnemonic seed phrase')
	wl_chksum       = '3c381ebb'
	seedlen_map     = {32: 25}
	seedlen_map_rev = {25: 32}

	def __init__(self, wl_id='xmrseed'):
		assert wl_id == 'xmrseed', "initialize with 'xmrseed' for compatibility with baseconv API"
		from .wordlist.monero import words
		self.digits = words
		self.wl_id = 'xmrseed'

	@staticmethod
	def monero_mn_checksum(words):
		from binascii import crc32
		wstr = ''.join(word[:3] for word in words)
		return words[crc32(wstr.encode()) % len(words)]

	def tobytes(self, words_arg, pad=None):

		assert isinstance(words_arg, (list, tuple)), 'words must be list or tuple'
		assert pad is None, f"{pad}: invalid 'pad' argument (must be None)"

		words = words_arg

		desc = self.desc.short
		wl = self.digits
		base = len(wl)

		if not set(words) <= set(wl):
			die('MnemonicError',  f'{words!r}: not in {desc} format')

		if len(words) not in self.seedlen_map_rev:
			die('MnemonicError',  f'{len(words)}: invalid seed phrase length for {desc}')

		z = self.monero_mn_checksum(words[:-1])
		if z != words[-1]:
			die('MnemonicError', f'invalid {desc} checksum')

		words = tuple(words[:-1])

		def gen():
			for i in range(len(words)//3):
				w1, w2, w3 = [wl.index(w) for w in words[3*i:3*i+3]]
				x = w1 + base*((w2-w1)%base) + base*base*((w3-w2)%base)
				yield x.to_bytes(4, 'big')[::-1]

		return b''.join(gen())

	def frombytes(self, bytestr, pad=None, tostr=False):
		assert pad is None, f"{pad}: invalid 'pad' argument (must be None)"

		desc = self.desc.short
		wl = self.digits
		base = len(wl)

		if len(bytestr) not in self.seedlen_map:
			die('SeedLengthError', f'{len(bytestr)}: invalid seed byte length for {desc}')

		def num2base_monero(num):
			w1 = num % base
			w2 = (num//base + w1) % base
			w3 = (num//base//base + w2) % base
			return (wl[w1], wl[w2], wl[w3])

		def gen():
			for i in range(len(bytestr)//4):
				yield from num2base_monero(int.from_bytes(bytestr[i*4:i*4+4][::-1], 'big'))

		o = list(gen())
		o.append(self.monero_mn_checksum(o))

		return ' '.join(o) if tostr else tuple(o)
