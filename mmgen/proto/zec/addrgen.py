#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
proto.zec.addrgen: Zcash-Z address generation class for the MMGen suite
"""

from ...addrgen import addr_generator,check_data
from ...addr import CoinAddr,ZcashViewKey
from ..common import b58chk_encode

class zcash_z(addr_generator.base):

	@check_data
	def to_addr(self,data):
		ret = b58chk_encode(
			self.proto.addr_fmt_to_ver_bytes['zcash_z']
			+ data.pubkey )
		return CoinAddr( self.proto, ret )

	@check_data
	def to_viewkey(self,data):
		ret = b58chk_encode(
			self.proto.addr_fmt_to_ver_bytes['viewkey']
			+ data.viewkey_bytes )
		return ZcashViewKey( self.proto, ret )
