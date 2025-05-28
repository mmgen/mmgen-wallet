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
rpc.remote: remote RPC client class for the MMGen Project
"""

class RemoteRPCClient:

	is_remote = True

	def __init__(self, cfg, proto):
		self.cfg = cfg
		self.proto = proto

	def get_block_from_minconf(self, minconf):
		return None
