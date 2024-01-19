#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
tx.unsigned: unsigned transaction class
"""

from .completed import Completed
from ..util import remove_dups

class Unsigned(Completed):
	desc = 'unsigned transaction'
	ext  = 'rawtx'

	def delete_attrs(self,desc,attr):
		for e in getattr(self,desc):
			if hasattr(e,attr):
				delattr(e,attr)

	def get_sids(self,desc):
		return remove_dups(
			(e.mmid.sid for e in getattr(self,desc) if e.mmid),
			quiet = True )
