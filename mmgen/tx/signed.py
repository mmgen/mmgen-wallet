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
tx.signed: signed transaction class
"""

from .completed import Completed

class Signed(Completed):
	desc = 'signed transaction'
	ext  = 'sigtx'
	signed = True

class AutomountSigned(Signed):
	desc = 'signed automount transaction'
	ext  = 'asigtx'
