#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
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
	return "(valid choices: '{}')".format( "','".join(l) )

class tool_cmd_base(MMGenObject):

	need_proto = False
	need_addrtype = False
	need_amt = False

	def __init__(self,cmdname=None,proto=None,mmtype=None):

		if self.need_proto:
			from ..protocol import init_proto_from_opts
			self.proto = proto or init_proto_from_opts(need_amt=self.need_amt)
			from ..globalvars import g
			if g.token:
				self.proto.tokensym = g.token.upper()

		if self.need_addrtype:
			from ..opts import opt
			from ..addr import MMGenAddrType
			self.mmtype = MMGenAddrType(
				self.proto,
				mmtype or opt.type or self.proto.dfl_mmtype )

	@property
	def user_commands(self):
		return {k:v for k,v in type(self).__dict__.items() if callable(v) and not k.startswith('_')}
