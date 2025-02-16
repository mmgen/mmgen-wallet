#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
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
derive: coin private key secret derivation for the MMGen suite
"""

from collections import namedtuple
from hashlib import sha512, sha256
from .addrlist import AddrIdxList

pk_bytes = namedtuple('coin_privkey_bytes', ['idx', 'pos', 'data'])

def derive_coin_privkey_bytes(seed, idxs):

	assert isinstance(idxs, AddrIdxList), f'{type(idxs)}: idx list not of type AddrIdxList'

	t_keys = len(idxs)
	pos = 0

	for idx in range(1, AddrIdxList.max_len + 1): # key/addr indexes begin from one

		seed = sha512(seed).digest()

		if idx == idxs[pos]:

			pos += 1

			# secret is double sha256 of seed hash round /idx/
			yield pk_bytes(idx, pos, sha256(sha256(seed).digest()).digest())

			if pos == t_keys:
				break
