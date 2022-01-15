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
seed.py:  Seed-related classes and methods for the MMGen suite
"""

from .common import *
from .obj import *
from .crypto import get_random,scramble_seed

class SeedBase(MMGenObject):

	data = ImmutableAttr(bytes,typeconv=False)
	sid  = ImmutableAttr(SeedID,typeconv=False)

	def __init__(self,seed_bin=None):
		if not seed_bin:
			# Truncate random data for smaller seed lengths
			seed_bin = sha256(get_random(1033)).digest()[:(opt.seed_len or g.dfl_seed_len)//8]
		elif len(seed_bin)*8 not in g.seed_lens:
			die(3,f'{len(seed_bin)}: invalid seed length')

		self.data = seed_bin
		self.sid  = SeedID(seed=self)

	@property
	def bitlen(self):
		return len(self.data) * 8

	@property
	def byte_len(self):
		return len(self.data)

	@property
	def hexdata(self):
		return self.data.hex()

	@property
	def fn_stem(self):
		return self.sid

class SubSeedList(MMGenObject):
	have_short = True
	nonce_start = 0
	debug_last_share_sid_len = 3

	def __init__(self,parent_seed):
		self.member_type = SubSeed
		self.parent_seed = parent_seed
		self.data = { 'long': IndexedDict(), 'short': IndexedDict() }

	def __len__(self):
		return len(self.data['long'])

	def get_subseed_by_ss_idx(self,ss_idx_in,print_msg=False):
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
		idx,nonce = self.data[ss_idx.type][sid]
		if idx != ss_idx.idx:
			die(3, "{} != {}: self.data[{t!r}].key(i) does not match self.data[{t!r}][i]!".format(
				idx,
				ss_idx.idx,
				t = ss_idx.type ))

		if print_msg:
			msg(f'\b\b\b => {SeedID.hlc(sid)}')

		seed = self.member_type(self,idx,nonce,length=ss_idx.type)
		assert seed.sid == sid, f'{seed.sid} != {sid}: Seed ID mismatch!'
		return seed

	def get_subseed_by_seed_id(self,sid,last_idx=None,print_msg=False):

		def get_existing_subseed_by_seed_id(sid):
			for k in ('long','short') if self.have_short else ('long',):
				if sid in self.data[k]:
					idx,nonce = self.data[k][sid]
					return self.member_type(self,idx,nonce,length=k)

		def do_msg(subseed):
			if print_msg:
				qmsg('{} {} ({}:{})'.format(
					green('Found subseed'),
					subseed.sid.hl(),
					self.parent_seed.sid.hl(),
					subseed.ss_idx.hl(),
				))

		if last_idx == None:
			last_idx = g.subseeds

		subseed = get_existing_subseed_by_seed_id(sid)
		if subseed:
			do_msg(subseed)
			return subseed

		if len(self) >= last_idx:
			return None

		self._generate(last_idx,last_sid=sid)

		subseed = get_existing_subseed_by_seed_id(sid)
		if subseed:
			do_msg(subseed)
			return subseed

	def _collision_debug_msg(self,sid,idx,nonce,nonce_desc='nonce',debug_last_share=False):
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

	def _generate(self,last_idx=None,last_sid=None):

		if last_idx == None:
			last_idx = g.subseeds

		first_idx = len(self) + 1

		if first_idx > last_idx:
			return None

		if last_sid != None:
			last_sid = SeedID(sid=last_sid)

		def add_subseed(idx,length):
			for nonce in range(self.nonce_start,self.member_type.max_nonce+1): # handle SeedID collisions
				sid = make_chksum_8(self.member_type.make_subseed_bin(self,idx,nonce,length))
				if sid in self.data['long'] or sid in self.data['short'] or sid == self.parent_seed.sid:
					if g.debug_subseed: # should get ≈450 collisions for first 1,000,000 subseeds
						self._collision_debug_msg(sid,idx,nonce)
				else:
					self.data[length][sid] = (idx,nonce)
					return last_sid == sid
			else: # must exit here, as this could leave self.data in inconsistent state
				raise SubSeedNonceRangeExceeded('add_subseed(): nonce range exceeded')

		for idx in SubSeedIdxRange(first_idx,last_idx).iterate():
			match1 = add_subseed(idx,'long')
			match2 = add_subseed(idx,'short') if self.have_short else False
			if match1 or match2:
				break

	def format(self,first_idx,last_idx):

		r = SubSeedIdxRange(first_idx,last_idx)

		if len(self) < last_idx:
			self._generate(last_idx)

		fs1 = '{:>18} {:>18}\n'
		fs2 = '{i:>7}L: {:8} {i:>7}S: {:8}\n'

		hdr = f'    Parent Seed: {self.parent_seed.sid.hl()} ({self.parent_seed.bitlen} bits)\n\n'
		hdr += fs1.format('Long Subseeds','Short Subseeds')
		hdr += fs1.format('-------------','--------------')

		sl = self.data['long'].keys
		ss = self.data['short'].keys
		body = (fs2.format( sl[n-1], ss[n-1], i=n ) for n in r.iterate())

		return hdr + ''.join(body)

class Seed(SeedBase):

	def __init__(self,seed_bin=None):
		self.subseeds = SubSeedList(self)
		SeedBase.__init__(self,seed_bin=seed_bin)

	def subseed(self,ss_idx_in,print_msg=False):
		return self.subseeds.get_subseed_by_ss_idx(ss_idx_in,print_msg=print_msg)

	def subseed_by_seed_id(self,sid,last_idx=None,print_msg=False):
		return self.subseeds.get_subseed_by_seed_id(sid,last_idx=last_idx,print_msg=print_msg)

	def split(self,*args,**kwargs):
		from .seedsplit import SeedShareList
		return SeedShareList(self,*args,**kwargs)

	@staticmethod
	def join_shares(*args,**kwargs):
		from .seedsplit import join_shares
		return join_shares(*args,**kwargs)

class SubSeed(SeedBase):

	idx    = ImmutableAttr(int,typeconv=False)
	nonce  = ImmutableAttr(int,typeconv=False)
	ss_idx = ImmutableAttr(SubSeedIdx)
	max_nonce = 1000

	def __init__(self,parent_list,idx,nonce,length):
		self.idx = idx
		self.nonce = nonce
		self.ss_idx = str(idx) + { 'long': 'L', 'short': 'S' }[length]
		self.parent_list = parent_list
		SeedBase.__init__(self,seed_bin=type(self).make_subseed_bin(parent_list,idx,nonce,length))

	@staticmethod
	def make_subseed_bin(parent_list,idx:int,nonce:int,length:str):
		seed = parent_list.parent_seed
		short = { 'short': True, 'long': False }[length]
		# field maximums: idx: 4294967295 (1000000), nonce: 65535 (1000), short: 255 (1)
		scramble_key  = idx.to_bytes(4,'big') + nonce.to_bytes(2,'big') + short.to_bytes(1,'big')
		return scramble_seed(seed.data,scramble_key)[:16 if short else seed.byte_len]
