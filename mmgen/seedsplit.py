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
seedsplit: Seed split classes and methods for the MMGen suite
"""

from .color import yellow
from .util import msg, die
from .objmethods import MMGenObject, HiliteStr, InitErrors
from .obj import ImmutableAttr, MMGenPWIDString, MMGenIdx, get_obj, IndexedDict
from .seed import Seed, SeedBase
from .subseed import SubSeedList, SubSeedIdx, SubSeed
from .crypto import Crypto

class SeedShareIdx(MMGenIdx):
	max_val = 1024

class SeedShareCount(SeedShareIdx):
	min_val = 2

class MasterShareIdx(MMGenIdx):
	max_val = 1024

class SeedSplitSpecifier(HiliteStr, InitErrors, MMGenObject):
	color = 'red'
	def __new__(cls, s):
		if isinstance(s, cls):
			return s
		try:
			me = str.__new__(cls, s)
			match s.split(':', 2):
				case [id_str, idx, count]:
					me.id = SeedSplitIDString(id_str)
				case [idx, count]:
					me.id = SeedSplitIDString('default')
				case _:
					raise ValueError('seed split specifier cannot be parsed')
			me.idx = SeedShareIdx(idx)
			me.count = SeedShareCount(count)
			assert me.idx <= me.count, 'share index greater than share count'
			return me
		except Exception as e:
			return cls.init_fail(e, s)

def is_seed_split_specifier(s):
	return get_obj(SeedSplitSpecifier, s=s, silent=True, return_bool=True)

class SeedSplitIDString(MMGenPWIDString):
	desc = 'seed split ID string'

class SeedShareList(SubSeedList):
	have_short = False
	split_type = 'N-of-N'

	count  = ImmutableAttr(SeedShareCount)
	id_str = ImmutableAttr(SeedSplitIDString)

	def __init__(self, parent_seed, count, *, id_str=None, master_idx=None, debug_last_share=False):
		self.member_type = SeedShare
		self.parent_seed = parent_seed
		self.id_str = id_str or 'default'
		self.count = count
		self.len = 2 # placeholder, always overridden

		def make_master_share():
			for nonce in range(SeedShare.max_nonce+1):
				ms = SeedShareMaster(self, master_idx, nonce)
				if ms.sid == parent_seed.sid:
					if parent_seed.cfg.debug_subseed:
						msg(f'master_share seed ID collision with parent seed, incrementing nonce to {nonce+1}')
				else:
					return ms
			die('SubSeedNonceRangeExceeded', 'nonce range exceeded')

		def last_share_debug(last_share):
			if not debug_last_share:
				return False
			sid_len = self.debug_last_share_sid_len
			lsid = last_share.sid[:sid_len]
			psid = parent_seed.sid[:sid_len]
			ssids = [d[:sid_len] for d in self.data['long'].keys]
			return (lsid in ssids or lsid == psid)

		self.master_share = make_master_share() if master_idx else None

		for nonce in range(SeedShare.max_nonce+1):
			self.nonce_start = nonce
			self.data = {'long': IndexedDict(), 'short': IndexedDict()} # 'short' is required as a placeholder
			if self.master_share:
				self.data['long'][self.master_share.sid] = (1, self.master_share.nonce)
			self._generate(count-1)
			self.last_share = ls = SeedShareLast(self)
			if last_share_debug(ls) or ls.sid in self.data['long'] or ls.sid == parent_seed.sid:
				# collision: throw out entire split list and redo with new start nonce
				if parent_seed.cfg.debug_subseed:
					self._collision_debug_msg(
						ls.sid, count, nonce, nonce_desc='nonce_start', debug_last_share=debug_last_share)
			else:
				self.data['long'][ls.sid] = (count, nonce)
				break
		else:
			die('SubSeedNonceRangeExceeded', 'nonce range exceeded')

		if parent_seed.cfg.debug_subseed:
			A = parent_seed.data
			B = self.join().data
			assert A == B, f'Data mismatch!\noriginal seed: {A!r}\nrejoined seed: {B!r}'

	def get_share_by_idx(self, idx, *, base_seed=False):
		match idx:
			case self.count:
				return self.last_share
			case 1 if self.master_share:
				return self.master_share if base_seed else self.master_share.derived_seed
			case x if x >= 1 or x <= self.count:
				return self.get_subseed_by_ss_idx(SubSeedIdx(str(idx) + 'L'))
			case x:
				die('RangeError', f'{x}: share index out of range')

	def get_share_by_seed_id(self, sid, *, base_seed=False):
		if sid == self.data['long'].key(self.count-1):
			return self.last_share
		elif self.master_share and sid == self.data['long'].key(0):
			return self.master_share if base_seed else self.master_share.derived_seed
		else:
			return self.get_subseed_by_seed_id(sid)

	def join(self):
		return Seed.join_shares(
			self.parent_seed.cfg,
			[self.get_share_by_idx(i+1) for i in range(len(self))])

	def format(self):
		assert self.split_type == 'N-of-N'
		fs1 = '    {}\n'
		fs2 = '{i:>5}: {}\n'
		mfs1, mfs2, midx, msid = ('', '', '', '')
		if self.master_share:
			mfs1, mfs2 = (' with master share #{} ({})', ' (master share #{})')
			midx, msid = (self.master_share.idx, self.master_share.sid)

		hdr  = '    {} {} ({} bits)\n'.format('Seed:', self.parent_seed.sid.hl(), self.parent_seed.bitlen)
		hdr += '    {} {c}-of-{c} (XOR){m}\n'.format('Split Type:', c=self.count, m=mfs1.format(midx, msid))
		hdr += '    {} {}\n\n'.format('ID String:', self.id_str.hl())
		hdr += fs1.format('Shares')
		hdr += fs1.format('------')

		sl = self.data['long'].keys
		body1 = fs2.format(sl[0]+mfs2.format(midx), i=1)
		body = (fs2.format(sl[n], i=n+1) for n in range(1, len(self)))

		return hdr + body1 + ''.join(body)

class SeedShareBase(MMGenObject):

	@property
	def fn_stem(self):
		pl = self.parent_list
		msdata = f'_with_master{pl.master_share.idx}' if pl.master_share else ''
		return '{}-{}-{}of{}{}[{}]'.format(
			pl.parent_seed.sid,
			pl.id_str,
			self.idx,
			pl.count,
			msdata,
			self.sid)

	@property
	def desc(self):
		return self.get_desc()

	def get_desc(self, *, ui=False):
		pl = self.parent_list
		mss = f', with master share #{pl.master_share.idx}' if pl.master_share else ''
		if ui:
			m   = (yellow("(share {} of {} of ")
					+ pl.parent_seed.sid.hl()
					+ yellow(', split id ')
					+ pl.id_str.hl2(encl='‘’')
					+ yellow('{})'))
		else:
			m = "share {} of {} of " + pl.parent_seed.sid + ", split id '" + pl.id_str + "'{}"
		return m.format(self.idx, pl.count, mss)

class SeedShare(SeedShareBase, SubSeed):

	@staticmethod
	def make_subseed_bin(parent_list, idx: int, nonce: int, length: str):
		seed = parent_list.parent_seed
		assert parent_list.have_short is False
		assert length == 'long'
		# field maximums: id_str: none (256 chars), count: 65535 (1024), idx: 65535 (1024), nonce: 65535 (1000)
		scramble_key = (
			f'{parent_list.split_type}:{parent_list.id_str}:'.encode() +
			parent_list.count.to_bytes(2, 'big') +
			idx.to_bytes(2, 'big') +
			nonce.to_bytes(2, 'big')
		)
		if parent_list.master_share:
			scramble_key += (
				b':master:' +
				parent_list.master_share.idx.to_bytes(2, 'big')
			)
		return Crypto(parent_list.parent_seed.cfg).scramble_seed(seed.data, scramble_key)[:seed.byte_len]

class SeedShareLast(SeedShareBase, SeedBase):

	idx = ImmutableAttr(SeedShareIdx)
	nonce = 0

	def __init__(self, parent_list):
		self.idx = parent_list.count
		self.parent_list = parent_list
		SeedBase.__init__(
			self,
			parent_list.parent_seed.cfg,
			seed_bin=self.make_subseed_bin(parent_list))

	@staticmethod
	def make_subseed_bin(parent_list):
		seed_list = (parent_list.get_share_by_idx(i+1) for i in range(len(parent_list)))
		seed = parent_list.parent_seed

		ret = int(seed.data.hex(), 16)
		for ss in seed_list:
			ret ^= int(ss.data.hex(), 16)

		return ret.to_bytes(seed.byte_len, 'big')

class SeedShareMaster(SeedBase, SeedShareBase):

	idx   = ImmutableAttr(MasterShareIdx)
	nonce = ImmutableAttr(int, typeconv=False)

	def __init__(self, parent_list, idx, nonce):
		self.idx = idx
		self.nonce = nonce
		self.parent_list = parent_list
		self.cfg = parent_list.parent_seed.cfg

		SeedBase.__init__(self, self.cfg, seed_bin=self.make_base_seed_bin())

		self.derived_seed = SeedBase(
			self.cfg,
			seed_bin = self.make_derived_seed_bin(parent_list.id_str, parent_list.count))

	@property
	def fn_stem(self):
		return '{}-MASTER{}[{}]'.format(self.parent_list.parent_seed.sid, self.idx, self.sid)

	def make_base_seed_bin(self):
		seed = self.parent_list.parent_seed
		# field maximums: idx: 65535 (1024)
		scramble_key = b'master_share:' + self.idx.to_bytes(2, 'big') + self.nonce.to_bytes(2, 'big')
		return Crypto(self.cfg).scramble_seed(seed.data, scramble_key)[:seed.byte_len]

	# Don't bother with avoiding seed ID collision here, as sid of derived seed is not used
	# by user as an identifier
	def make_derived_seed_bin(self, id_str, count):
		# field maximums: id_str: none (256 chars), count: 65535 (1024)
		scramble_key = id_str.encode() + b':' + count.to_bytes(2, 'big')
		return Crypto(self.cfg).scramble_seed(self.data, scramble_key)[:self.byte_len]

	def get_desc(self, *, ui=False):
		psid = self.parent_list.parent_seed.sid
		mss = f'master share #{self.idx} of '
		return yellow('(' + mss) + psid.hl() + yellow(')') if ui else mss + psid

class SeedShareMasterJoining(SeedShareMaster):

	id_str = ImmutableAttr(SeedSplitIDString)
	count  = ImmutableAttr(SeedShareCount)

	def __init__(self, cfg, idx, base_seed, id_str, count):

		SeedBase.__init__(self, cfg, seed_bin=base_seed.data)

		self.cfg = cfg
		self.id_str = id_str or 'default'
		self.count = count
		self.derived_seed = SeedBase(
			cfg,
			seed_bin = self.make_derived_seed_bin(self.id_str, self.count))

def join_shares(
		cfg,
		seed_list,
		*,
		master_idx = None,
		id_str     = None):

	if not hasattr(seed_list, '__next__'): # seed_list can be iterator or iterable
		seed_list = iter(seed_list)

	class d:
		byte_len, ret, count = None, 0, 0

	def add_share(ss):
		if d.byte_len:
			assert ss.byte_len == d.byte_len, f'Seed length mismatch! {ss.byte_len} != {d.byte_len}'
		else:
			d.byte_len = ss.byte_len
		d.ret ^= int(ss.data.hex(), 16)
		d.count += 1

	if master_idx:
		master_share = next(seed_list)

	for ss in seed_list:
		add_share(ss)

	if master_idx:
		add_share(SeedShareMasterJoining(cfg, master_idx, master_share, id_str, d.count+1).derived_seed)

	SeedShareCount(d.count) # check that d.count is in valid range

	return Seed(cfg, seed_bin=d.ret.to_bytes(d.byte_len, 'big'))
