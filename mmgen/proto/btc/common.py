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
proto.btc.common: Shared Bitcoin functions and constants
"""

import hashlib

b58a = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def hash160(in_bytes): # OP_HASH160
	return hashlib.new('ripemd160', hashlib.sha256(in_bytes).digest()).digest()

def hash256(in_bytes): # OP_HASH256
	return hashlib.sha256(hashlib.sha256(in_bytes).digest()).digest()

# From en.bitcoin.it:
#  The Base58 encoding used is home made, and has some differences.
#  Especially, leading zeroes are kept as single zeroes when conversion happens.
# Test: 5JbQQTs3cnoYN9vDYaGY6nhQ1DggVsY4FJNBUfEfpSQqrEp3srk
# The 'zero address':
# 1111111111111111111114oLvT2 (pubkeyhash = '\0'*20)

def b58chk_encode(in_bytes):
	lzeroes = len(in_bytes) - len(in_bytes.lstrip(b'\x00'))
	def do_enc(n):
		while n:
			yield b58a[n % 58]
			n //= 58
	return ('1' * lzeroes) + ''.join(do_enc(int.from_bytes(in_bytes+hash256(in_bytes)[:4], 'big')))[::-1]

def b58chk_decode(s):
	lzeroes = len(s) - len(s.lstrip('1'))
	res = sum(b58a.index(ch) * 58**n for n, ch in enumerate(s[::-1]))
	bl = res.bit_length()
	out = b'\x00' * lzeroes + res.to_bytes(bl//8 + bool(bl%8), 'big')
	if out[-4:] != hash256(out[:-4])[:4]:
		raise ValueError('b58chk_decode(): incorrect checksum')
	return out[:-4]
