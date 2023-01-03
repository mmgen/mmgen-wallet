#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
proto.eth.addrgen: Ethereum address generation class for the MMGen suite
"""

from ...addrgen import addr_generator,check_data
from ...addr import CoinAddr

class ethereum(addr_generator.keccak):

	@check_data
	def to_addr(self,data):
		return CoinAddr(
			self.proto,
			self.keccak_256(data.pubkey[1:]).hexdigest()[24:] )
