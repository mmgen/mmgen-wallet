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
subseed: Subseed classes and methods for the MMGen suite
"""

from .color import green
from .util import msg_r, msg, die, make_chksum_8
from .objmethods import MMGenObject, HiliteStr, InitErrors
from .obj import MMGenRange, IndexedDict, ImmutableAttr
from .seed import SeedBase, SeedID

class SubSeedIdxRange(MMGenRange):
	min_idx = 1
	max_idx = 1000000

class SubSeedIdx(HiliteStr, InitErrors):
	color = 'red'
	trunc_ok = False
	def __new__(cls, s):
		if isinstance(s, cls):
			return s
		try:
			assert isinstance(s, str), 'not a string or string subclass'
			idx = s[:-1] if s[-1] in 'SsLl' else s
			from .util import is_int
			assert is_int(idx), "valid format: an integer, plus optional letter 'S', 's', 'L' or 'l'"
			idx = int(idx)
			assert idx >= SubSeedIdxRange.min_idx, f'subseed index < {SubSeedIdxRange.min_idx:,}'
			assert idx <= SubSeedIdxRange.max_idx, f'subseed index > {SubSeedIdxRange.max_idx:,}'

			sstype, ltr = ('short', 'S') if s[-1] in 'Ss' else ('long', 'L')
			me = str.__new__(cls, str(idx)+ltr)
			me.idx = idx
			me.type = sstype
			return me
		except Exception as e:
			return cls.init_fail(e, s)

class SubSeed(SeedBase):

	idx    = ImmutableAttr(int, typeconv=False)
	nonce  = ImmutableAttr(int, typeconv=False)
	ss_idx = ImmutableAttr(SubSeedIdx)
	max_nonce = 1000

	def __init__(self, parent_list, idx, nonce, length):
		self.idx = idx
		self.nonce = nonce
		self.ss_idx = str(idx) + {'long': 'L', 'short': 'S'}[length]
		self.parent_list = parent_list
		SeedBase.__init__(
			self,
			parent_list.parent_seed.cfg,
			seed_bin=self.make_subseed_bin(parent_list, idx, nonce, length))

	@staticmethod
	def make_subseed_bin(parent_list, idx: int, nonce: int, length: str):
		seed = parent_list.parent_seed
		short = {'short': True, 'long': False}[length]
		# field maximums: idx: 4294967295 (1000000), nonce: 65535 (1000), short: 255 (1)
		scramble_key  = idx.to_bytes(4, 'big') + nonce.to_bytes(2, 'big') + short.to_bytes(1, 'big')
		from .crypto import Crypto
		return Crypto(parent_list.parent_seed.cfg).scramble_seed(
			seed.data, scramble_key)[:16 if short else seed.byte_len]

class SubSeedList(MMGenObject):
	have_short = True
	nonce_start = 0
	debug_last_share_sid_len = 3
	dfl_len = 100

	def __init__(self, parent_seed, *, length=None):
		self.member_type = SubSeed
		self.parent_seed = parent_seed
		self.data = {'long': IndexedDict(), 'short': IndexedDict()}
		self.len = length or self.dfl_len

	def __len__(self):
		return len(self.data['long'])

	def get_subseed_by_ss_idx(self, ss_idx_in, *, print_msg=False):
		ss_idx = SubSeedIdx(ss_idx_in)
		if print_msg:
			msg_r('{} {} of {}...'.format(
				green('Generating subseed'),
				ss_idx.hl(),
				self.parent_seed.sid.hl(),
			))

		if ss_idx.idx > len(self):
			self._generate(ss_idx.idx)

		sid = self.data[ss_idx.type].key(ss_idx.idx-1)
		idx, nonce = self.data[ss_idx.type][sid]
		if idx != ss_idx.idx:
			die(3, "{} != {}: self.data[{t!r}].key(i) does not match self.data[{t!r}][i]!".format(
				idx,
				ss_idx.idx,
				t = ss_idx.type))

		if print_msg:
			msg(f'\b\b\b => {SeedID.hlc(sid)}')

		seed = self.member_type(self, idx, nonce, length=ss_idx.type)
		assert seed.sid == sid, f'{seed.sid} != {sid}: Seed ID mismatch!'
		return seed

	def get_subseed_by_seed_id(self, sid, *, last_idx=None, print_msg=False):

		def get_existing_subseed_by_seed_id(sid):
			for k in ('long', 'short') if self.have_short else ('long',):
				if sid in self.data[k]:
					idx, nonce = self.data[k][sid]
					return self.member_type(self, idx, nonce, length=k)

		def do_msg(subseed):
			if print_msg:
				self.parent_seed.cfg._util.qmsg('{} {} ({}:{})'.format(
					green('Found subseed'),
					subseed.sid.hl(),
					self.parent_seed.sid.hl(),
					subseed.ss_idx.hl(),
				))

		if last_idx is None:
			last_idx = self.len

		subseed = get_existing_subseed_by_seed_id(sid)
		if subseed:
			do_msg(subseed)
			return subseed

		if len(self) >= last_idx:
			return None

		self._generate(last_idx, last_sid=sid)

		subseed = get_existing_subseed_by_seed_id(sid)
		if subseed:
			do_msg(subseed)
			return subseed

	def _collision_debug_msg(self, sid, idx, nonce, *, nonce_desc='nonce', debug_last_share=False):
		slen = 'short' if sid in self.data['short'] else 'long'
		m1 = f'add_subseed(idx={idx},{slen}):'
		if sid == self.parent_seed.sid:
			m2 = f'collision with parent Seed ID {sid},'
		else:
			if debug_last_share:
				sl = self.debug_last_share_sid_len
				colliding_idx = [d[:sl] for d in self.data[slen].keys].index(sid[:sl]) + 1
				sid = sid[:sl]
			else:
				colliding_idx = self.data[slen][sid][0]
			m2 = f'collision with ID {sid} (idx={colliding_idx},{slen}),'
		msg(f'{m1:30} {m2:46} incrementing {nonce_desc} to {nonce+1}')

	def _generate(self, last_idx=None, *, last_sid=None):

		if last_idx is None:
			last_idx = self.len

		first_idx = len(self) + 1

		if first_idx > last_idx:
			return None

		if last_sid is not None:
			last_sid = SeedID(sid=last_sid)

		def add_subseed(idx, length):
			for nonce in range(self.nonce_start, self.member_type.max_nonce+1): # handle SeedID collisions
				sid = make_chksum_8(self.member_type.make_subseed_bin(self, idx, nonce, length))
				if sid in self.data['long'] or sid in self.data['short'] or sid == self.parent_seed.sid:
					if self.parent_seed.cfg.debug_subseed: # should get ≈450 collisions for first 1,000,000 subseeds
						self._collision_debug_msg(sid, idx, nonce)
				else:
					self.data[length][sid] = (idx, nonce)
					return last_sid == sid
			# must exit here, as this could leave self.data in inconsistent state
			die('SubSeedNonceRangeExceeded', 'add_subseed(): nonce range exceeded')

		for idx in SubSeedIdxRange(first_idx, last_idx).iterate():
			match1 = add_subseed(idx, 'long')
			match2 = add_subseed(idx, 'short') if self.have_short else False
			if match1 or match2:
				break

	def format(self, first_idx, last_idx):

		r = SubSeedIdxRange(first_idx, last_idx)

		if len(self) < last_idx:
			self._generate(last_idx)

		fs1 = '{:>18} {:>18}\n'
		fs2 = '{i:>7}L: {:8} {i:>7}S: {:8}\n'

		hdr = f'    Parent Seed: {self.parent_seed.sid.hl()} ({self.parent_seed.bitlen} bits)\n\n'
		hdr += fs1.format('Long Subseeds', 'Short Subseeds')
		hdr += fs1.format('-------------', '--------------')

		sl = self.data['long'].keys
		ss = self.data['short'].keys
		body = (fs2.format(sl[n-1], ss[n-1], i=n) for n in r.iterate())

		return hdr + ''.join(body)
