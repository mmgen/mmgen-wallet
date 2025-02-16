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
proto.xmr.addrgen: Monero address generation class for the MMGen suite
"""

from ...addrgen import addr_generator, check_data
from ...addr import CoinAddr

class monero(addr_generator.keccak):

	def b58enc(self, addr_bytes):
		from ...baseconv import baseconv
		enc = baseconv('b58').frombytes
		l = len(addr_bytes)
		a = ''.join([enc(addr_bytes[i*8:i*8+8], pad=11, tostr=True) for i in range(l//8)])
		b = enc(addr_bytes[l-l%8:], pad=7, tostr=True)
		return a + b

	@check_data
	def to_addr(self, data):
		step1 = self.proto.addr_fmt_to_ver_bytes['monero'] + data.pubkey
		return CoinAddr(
			proto = self.proto,
			addr = self.b58enc(step1 + self.keccak_256(step1).digest()[:4]))

	@check_data
	def to_viewkey(self, data):
		return self.proto.viewkey(data.viewkey_bytes.hex())
