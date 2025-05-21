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
proto.xchain.addrgen: Cross-chain address generation classes for the MMGen suite
"""

from ...addrgen import addr_generator, check_data
from ..btc.common import hash160

class bech32x(addr_generator.base):

	@check_data
	def to_addr(self, data):
		return self.proto.encode_addr_bech32x(hash160(data.pubkey))
