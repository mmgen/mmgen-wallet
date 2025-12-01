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
proto.xmr.tx.completed: Monero completed transaction class
"""

from ....cfg import Config

from .base import Base

class Completed(Base):

	def __init__(self, cfg, *args, proto, filename, **kwargs):
		self.cfg = Config({
			'_clone':  cfg,
			'coin':    'XMR',
			'network': proto.network})
		self.proto = proto
		self.filename = filename
