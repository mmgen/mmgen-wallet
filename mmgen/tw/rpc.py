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
tw.rpc: Tracking wallet RPC class for the MMGen suite
"""

from ..objmethods import MMGenObject

class TwRPC:

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(proto.base_proto_subclass(cls,'tw.rpc'))

	def __init__(self,proto,rpc,twctl):
		self.proto = proto
		self.rpc = rpc
		self.twctl = twctl
