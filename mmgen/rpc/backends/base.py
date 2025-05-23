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
rpc.backends.base: base RPC backend class for the MMGen Project
"""

class base:

	def __init__(self, caller):
		self.cfg            = caller.cfg
		self.host           = caller.host
		self.port           = caller.port
		self.proxy          = caller.proxy
		self.host_url       = caller.host_url
		self.timeout        = caller.timeout
		self.http_hdrs      = caller.http_hdrs
		self.name           = type(self).__name__
		self.caller         = caller
