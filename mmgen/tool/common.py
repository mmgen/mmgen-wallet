#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
tool.common: Base class and shared routines for the 'mmgen-tool' utility
"""

from ..objmethods import MMGenObject

def options_annot_str(l):
	return "(valid choices: '{}')".format("','".join(l))

class tool_cmd_base(MMGenObject):

	need_proto = False
	need_addrtype = False
	need_amt = False

	def __init__(self, cfg, cmdname=None, proto=None, mmtype=None):

		self.cfg = cfg

		if self.need_proto:
			from ..protocol import init_proto_from_cfg
			self.proto = proto or cfg._proto or init_proto_from_cfg(cfg, need_amt=True)
			if cfg.token:
				self.proto.tokensym = cfg.token.upper()

		if self.need_addrtype:
			from ..addr import MMGenAddrType
			self.mmtype = MMGenAddrType(
				self.proto,
				mmtype or cfg.type or self.proto.dfl_mmtype)

	@property
	def user_commands(self):
		return {k:v for k, v in type(self).__dict__.items() if callable(v) and not k.startswith('_')}
