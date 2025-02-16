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
tw.rpc: Tracking wallet RPC class for the MMGen suite
"""

from ..objmethods import MMGenObject

class TwRPC:

	def __new__(cls, proto, *args, **kwargs):
		return MMGenObject.__new__(proto.base_proto_subclass(cls, 'tw.rpc'))

	def __init__(self, proto, rpc, twctl):
		self.proto = proto
		self.rpc = rpc
		self.twctl = twctl
