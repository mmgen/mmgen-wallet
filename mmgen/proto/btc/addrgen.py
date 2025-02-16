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
proto.btc.addrgen: Bitcoin address generation classes for the MMGen suite
"""

from ...addrgen import addr_generator, check_data
from .common import hash160

class p2pkh(addr_generator.base):

	@check_data
	def to_addr(self, data):
		return self.proto.pubhash2addr(hash160(data.pubkey), 'p2pkh')

class legacy(p2pkh):
	pass

class compressed(p2pkh):
	pass

class segwit(addr_generator.base):

	@check_data
	def to_addr(self, data):
		return self.proto.pubhash2segwitaddr(hash160(data.pubkey))

	def to_segwit_redeem_script(self, data): # NB: returns hex
		return self.proto.pubhash2redeem_script(hash160(data.pubkey)).hex()

class bech32(addr_generator.base):

	@check_data
	def to_addr(self, data):
		return self.proto.pubhash2bech32addr(hash160(data.pubkey))
