#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
tool/common.py: Base class and shared routines for the 'mmgen-tool' utility
"""

def options_annot_str(l):
	return "(valid options: '{}')".format( "','".join(l) )

class tool_cmd_base:

	def __init__(self,proto=None,mmtype=None):
		pass

	@property
	def user_commands(self):
		return {k:v for k,v in type(self).__dict__.items() if not k.startswith('_')}
