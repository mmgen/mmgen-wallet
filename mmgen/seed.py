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
seed: Seed-related classes and methods for the MMGen suite
"""

from .util import make_chksum_8, hexdigits_uc, die
from .objmethods import HiliteStr, InitErrors, MMGenObject
from .obj import ImmutableAttr, get_obj

class SeedID(HiliteStr, InitErrors):
	color = 'blue'
	width = 8
	trunc_ok = False
	def __new__(cls, seed=None, sid=None):
		if isinstance(sid, cls):
			return sid
		try:
			if seed:
				assert isinstance(seed, SeedBase), 'not a subclass of SeedBase'
				return str.__new__(cls, make_chksum_8(seed.data))
			elif sid:
				assert set(sid) <= set(hexdigits_uc), 'not uppercase hex digits'
				assert len(sid) == cls.width, f'not {cls.width} characters wide'
				return str.__new__(cls, sid)
			raise ValueError('no arguments provided')
		except Exception as e:
			return cls.init_fail(e, seed or sid)

def is_seed_id(s):
	return get_obj(SeedID, sid=s, silent=True, return_bool=True)

class SeedBase(MMGenObject):

	lens = (128, 192, 256)
	dfl_len = 256

	data = ImmutableAttr(bytes, typeconv=False)
	sid  = ImmutableAttr(SeedID, typeconv=False)

	def __init__(self, cfg, seed_bin=None, nSubseeds=None):

		if not seed_bin:
			from .crypto import Crypto
			from hashlib import sha256
			# Truncate random data for smaller seed lengths
			seed_bin = sha256(Crypto(cfg).get_random(1033)).digest()[:(cfg.seed_len or self.dfl_len)//8]
		elif len(seed_bin)*8 not in self.lens:
			die(3, f'{len(seed_bin)*8}: invalid seed bit length')

		self.cfg = cfg
		self.data = seed_bin
		self.sid  = SeedID(seed=self)
		self.nSubseeds = nSubseeds # overrides cfg.subseeds

	@property
	def bitlen(self):
		return len(self.data) * 8

	@property
	def byte_len(self):
		return len(self.data)

	@property
	def fn_stem(self):
		return self.sid

class Seed(SeedBase):

	@property
	def subseeds(self):
		if not hasattr(self, '_subseeds'):
			from .subseed import SubSeedList
			self._subseeds = SubSeedList(
				self,
				length = self.nSubseeds or self.cfg.subseeds)
		return self._subseeds

	def subseed(self, *args, **kwargs):
		return self.subseeds.get_subseed_by_ss_idx(*args, **kwargs)

	def subseed_by_seed_id(self, *args, **kwargs):
		return self.subseeds.get_subseed_by_seed_id(*args, **kwargs)

	def split(self, *args, **kwargs):
		from .seedsplit import SeedShareList
		return SeedShareList(self, *args, **kwargs)

	@staticmethod
	def join_shares(*args, **kwargs):
		from .seedsplit import join_shares
		return join_shares(*args, **kwargs)
