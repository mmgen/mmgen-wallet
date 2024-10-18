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
proto.bch.cashaddr: Bitcoin Cash cashaddr implementation for the MMGen Project
"""

# Specification: https://upgradespecs.bitcoincashnode.org/cashaddr

import re
from collections import namedtuple

b32_matrix = """
	q  p  z  r  y  9  x  8
	g  f  2  t  v  d  w  0
	s  3  j  n  5  4  k  h
	c  e  6  m  u  a  7  l
"""

b32a = re.sub(r'\s', '', b32_matrix)

cashaddr_addr_types = {
	'p2pkh':        0,
	'p2sh':         1,
	'token_pubkey': 2,
	'token_script': 3,
	'unknown':      15,
}
addr_types_rev = {v:k for k, v in cashaddr_addr_types.items()}

data_sizes = (160, 192, 224, 256, 320, 384, 448, 512)

def PolyMod(v):
	c = 1
	for d in v:
		c0 = c >> 35
		c = ((c & 0x07ffffffff) << 5) ^ d
		if (c0 & 1): c ^= 0x98f2bc8e61
		if (c0 & 2): c ^= 0x79b76d99e2
		if (c0 & 4): c ^= 0xf33e5fb3c4
		if (c0 & 8): c ^= 0xae2eabe2a8
		if (c0 & 16): c ^= 0x1e4f43e470
	return c ^ 1

def parse_ver_byte(ver):
	assert not (ver >> 7), 'invalid version byte: most-significant bit must be zero'
	t = namedtuple('parsed_version_byte', ['addr_type', 'bitlen'])
	return t(addr_types_rev[ver >> 3], data_sizes[ver & 7])

def make_ver_byte(addr_type, bitlen):
	assert addr_type in addr_types_rev, f'{addr_type}: invalid addr type'
	return (addr_type << 3) | data_sizes.index(bitlen)

def bin2vec(data_bin):
	assert not len(data_bin) % 5, f'{len(data_bin)}: data length not a multiple of 5'
	return [int(data_bin[i*5:(i*5)+5], 2) for i in range(len(data_bin) // 5)]

def make_polymod_vec(pfx, payload_vec):
	return ([ord(c) & 31  for c in pfx] + [0] + payload_vec)

def cashaddr_parse_addr(addr):
	t = namedtuple('parsed_cashaddr', ['pfx', 'payload'])
	return t(*addr.split(':', 1))

def cashaddr_encode_addr(addr_type, size, pfx, data):
	t = namedtuple('encoded_cashaddr', ['addr', 'pfx', 'payload'])
	payload_bin = (
		'{:08b}'.format(make_ver_byte(addr_type, size * 8)) +
		'{:0{w}b}'.format(int.from_bytes(data), w=len(data) * 8)
	)
	payload_vec = bin2vec(payload_bin + '0' * (-len(payload_bin) % 5))
	chksum_vec = bin2vec('{:040b}'.format(PolyMod(make_polymod_vec(pfx, payload_vec + [0] * 8))))
	payload = ''.join(b32a[i] for i in payload_vec + chksum_vec)
	return t(f'{pfx}:{payload}', pfx, payload)

def cashaddr_decode_addr(addr):
	t = namedtuple('decoded_cashaddr', ['pfx', 'payload', 'addr_type', 'bytes', 'chksum'])
	a = cashaddr_parse_addr(addr.lower())
	data_bin = ''.join(f'{b32a.index(c):05b}' for c in a.payload)
	vi = parse_ver_byte(int(data_bin[:8], 2))
	assert len(data_bin) >= vi.bitlen + 48, 'cashaddr data length too short!'
	data    = int(data_bin[8:8+vi.bitlen], 2).to_bytes(vi.bitlen // 8)
	chksum  = int(data_bin[-40:], 2).to_bytes(5)
	pad_bin = data_bin[8+vi.bitlen:-40]
	assert not pad_bin or pad_bin in '0000', f'{pad_bin}: invalid cashaddr data'
	if chksum_chk := PolyMod(make_polymod_vec(a.pfx, [b32a.index(c) for c in a.payload])) != 0:
		raise ValueError(
			'checksum check failed\n'
			f'  address:  {addr}\n'
			f'  result:   0x{chksum_chk:x}\n'
			f'  checksum: 0x{chksum.hex()}')
	return t(a.pfx, a.payload, vi.addr_type, data, chksum)
