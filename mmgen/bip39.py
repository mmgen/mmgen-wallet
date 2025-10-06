#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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
bip39.py - Data and routines for BIP39 mnemonic seed phrases
"""

from hashlib import sha256

from .baseconv import baseconv
from .util import is_hex_str, die

def is_bip39_mnemonic(s):
	return bool(bip39().tohex(s.split()))

# implements a subset of the baseconv API
class bip39(baseconv):

	desc            = baseconv.dt('BIP39 mnemonic', 'BIP39 mnemonic seed phrase')
	wl_chksum       = 'f18b9a84'
	seedlen_map     = {16:12, 24:18, 32:24}
	seedlen_map_rev = {12:16, 18:24, 24:32}

	from collections import namedtuple
	bc = namedtuple('bip39_constants', ['chk_len', 'mn_len'])
	#    ENT   CS  MS
	constants = {
		128: bc(4, 12),
		160: bc(5, 15),
		192: bc(6, 18),
		224: bc(7, 21),
		256: bc(8, 24)}

	def __init__(self, wl_id='bip39'):
		assert wl_id == 'bip39', "initialize with 'bip39' for compatibility with baseconv API"
		from .wordlist.bip39 import words
		self.digits = words
		self.wl_id = 'bip39'

	@classmethod
	def nwords2seedlen(cls, nwords, /, *, in_bytes=False, in_hex=False):
		for k, v in cls.constants.items():
			if v.mn_len == nwords:
				return k//8 if in_bytes else k//4 if in_hex else k
		die('MnemonicError', f'{nwords!r}: invalid word length for BIP39 mnemonic')

	@classmethod
	def seedlen2nwords(cls, seed_len, /, *, in_bytes=False, in_hex=False):
		seed_bits = seed_len * 8 if in_bytes else seed_len * 4 if in_hex else seed_len
		try:
			return cls.constants[seed_bits].mn_len
		except Exception as e:
			raise ValueError(f'{seed_bits!r}: invalid seed length for BIP39 mnemonic') from e

	def tohex(self, words_arg, /, *, pad=None):
		return self.tobytes(words_arg, pad=pad).hex()

	def tobytes(self, words_arg, /, *, pad=None):
		assert isinstance(words_arg, list | tuple), 'words_arg must be list or tuple'
		assert pad in (None, 'seed'), f"{pad}: invalid 'pad' argument (must be None or 'seed')"

		wl = self.digits

		for n, w in enumerate(words_arg):
			if w not in wl:
				die('MnemonicError', f'word #{n+1} is not in the BIP39 word list')

		res = ''.join(f'{wl.index(w):011b}' for w in words_arg)

		for k, v in self.constants.items():
			if len(words_arg) == v.mn_len:
				bitlen = k
				break
		else:
			die('MnemonicError', f'{len(words_arg)}: invalid BIP39 seed phrase length')

		seed_bin = res[:bitlen]
		chk_bin = res[bitlen:]

		seed_hex = f'{int(seed_bin, 2):0{bitlen//4}x}'
		seed_bytes = bytes.fromhex(seed_hex)

		chk_len = self.constants[bitlen].chk_len
		chk_hex_chk = sha256(seed_bytes).hexdigest()
		chk_bin_chk = f'{int(chk_hex_chk, 16):0256b}'[:chk_len]

		if chk_bin != chk_bin_chk:
			die('MnemonicError', f'invalid BIP39 seed phrase checksum ({chk_bin} != {chk_bin_chk})')

		return seed_bytes

	def fromhex(self, hexstr, /, *, pad=None, tostr=False):
		assert is_hex_str(hexstr), 'seed data not a hexadecimal string'
		return self.frombytes(bytes.fromhex(hexstr), pad=pad, tostr=tostr)

	def frombytes(self, seed_bytes, /, *, pad=None, tostr=False):
		assert tostr is False, "'tostr' must be False for 'bip39'"
		assert pad in (None, 'seed'), f"{pad}: invalid 'pad' argument (must be None or 'seed')"

		wl = self.digits
		bitlen = len(seed_bytes) * 8

		assert bitlen in self.constants, f'{bitlen}: invalid seed bit length'
		c = self.constants[bitlen]

		chk_hex = sha256(seed_bytes).hexdigest()

		seed_bin = f'{int(seed_bytes.hex(), 16):0{bitlen}b}'
		chk_bin  = f'{int(chk_hex, 16):0256b}'

		res = seed_bin + chk_bin

		return tuple(wl[int(res[i*11:(i+1)*11], 2)] for i in range(c.mn_len))

	def generate_seed(self, words_arg, /, *, passwd=''):

		self.tohex(words_arg) # validate

		from hashlib import pbkdf2_hmac
		return pbkdf2_hmac(
			hash_name  = 'sha512',
			password   = ' '.join(words_arg).encode(),
			salt       = b'mnemonic' + passwd.encode(),
			iterations = 2048,
			dklen      = 64)
