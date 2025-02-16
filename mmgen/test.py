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
test: functions required by the MMGen test suite
"""

import sys
from hashlib import sha256
rand_h = sha256('.'.join(sys.argv).encode())

def fake_urandom(n):

	def gen(rounds):
		for _ in range(rounds):
			rand_h.update(b'foo')
			yield rand_h.digest()

	return b''.join(gen(int(n/32)+1))[:n]
