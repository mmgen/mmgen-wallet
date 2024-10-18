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
proto.eth.addrgen: Ethereum address generation class for the MMGen suite
"""

from ...addrgen import addr_generator, check_data

class ethereum(addr_generator.keccak):

	@check_data
	def to_addr(self, data):
		return self.proto.pubhash2addr(self.keccak_256(data.pubkey[1:]).digest()[12:], 'p2pkh')
