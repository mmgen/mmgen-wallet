#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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
			die(3,'{}: invalid seed length'.format(len(seed_bin)))

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
			m = "{} != {}: self.data[{t!r}].key(i) does not match self.data[{t!r}][i]!"
			die(3,m.format(idx,ss_idx.idx,t=ss_idx.type))

		if print_msg:
			msg('\b\b\b => {}'.format(SeedID.hlc(sid)))

		seed = self.member_type(self,idx,nonce,length=ss_idx.type)
		assert seed.sid == sid,'{} != {}: Seed ID mismatch!'.format(seed.sid,sid)
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
		m1 = 'add_subseed(idx={},{}):'.format(idx,slen)
		if sid == self.parent_seed.sid:
			m2 = 'collision with parent Seed ID {},'.format(sid)
		else:
			if debug_last_share:
				sl = self.debug_last_share_sid_len
				colliding_idx = [d[:sl] for d in self.data[slen].keys].index(sid[:sl]) + 1
				sid = sid[:sl]
			else:
				colliding_idx = self.data[slen][sid][0]
			m2 = 'collision with ID {} (idx={},{}),'.format(sid,colliding_idx,slen)
		msg('{:30} {:46} incrementing {} to {}'.format(m1,m2,nonce_desc,nonce+1))

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

		hdr = '{:>16} {} ({} bits)\n\n'.format('Parent Seed:',self.parent_seed.sid.hl(),self.parent_seed.bitlen)
		hdr += fs1.format('Long Subseeds','Short Subseeds')
		hdr += fs1.format('-------------','--------------')

		sl = self.data['long'].keys
		ss = self.data['short'].keys
		body = (fs2.format(sl[n-1],ss[n-1],i=n) for n in r.iterate())

		return hdr + ''.join(body)

class Seed(SeedBase):

	def __init__(self,seed_bin=None):
		self.subseeds = SubSeedList(self)
		SeedBase.__init__(self,seed_bin=seed_bin)

	def subseed(self,ss_idx_in,print_msg=False):
		return self.subseeds.get_subseed_by_ss_idx(ss_idx_in,print_msg=print_msg)

	def subseed_by_seed_id(self,sid,last_idx=None,print_msg=False):
		return self.subseeds.get_subseed_by_seed_id(sid,last_idx=last_idx,print_msg=print_msg)

	def split(self,count,id_str=None,master_idx=None):
		return SeedShareList(self,count,id_str,master_idx)

	@staticmethod
	def join_shares(seed_list,master_idx=None,id_str=None):
		if not hasattr(seed_list,'__next__'): # seed_list can be iterator or iterable
			seed_list = iter(seed_list)

		class d(object):
			byte_len,ret,count = None,0,0

		def add_share(ss):
			if d.byte_len:
				assert ss.byte_len == d.byte_len,'Seed length mismatch! {} != {}'.format(ss.byte_len,d.byte_len)
			else:
				d.byte_len = ss.byte_len
			d.ret ^= int(ss.data.hex(),16)
			d.count += 1

		if master_idx:
			master_share = next(seed_list)

		for ss in seed_list:
			add_share(ss)

		if master_idx:
			add_share(SeedShareMasterJoining(master_idx,master_share,id_str,d.count+1).derived_seed)

		SeedShareCount(d.count)
		return Seed(seed_bin=d.ret.to_bytes(d.byte_len,'big'))

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

class SeedShareList(SubSeedList):
	have_short = False
	split_type = 'N-of-N'

	count  = ImmutableAttr(SeedShareCount)
	id_str = ImmutableAttr(SeedSplitIDString)

	def __init__(self,parent_seed,count,id_str=None,master_idx=None,debug_last_share=False):
		self.member_type = SeedShare
		self.parent_seed = parent_seed
		self.id_str = id_str or 'default'
		self.count = count

		def make_master_share():
			for nonce in range(SeedShare.max_nonce+1):
				ms = SeedShareMaster(self,master_idx,nonce)
				if ms.sid == parent_seed.sid:
					if g.debug_subseed:
						m = 'master_share seed ID collision with parent seed, incrementing nonce to {}'
						msg(m.format(nonce+1))
				else:
					return ms
			raise SubSeedNonceRangeExceeded('nonce range exceeded')

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
			self.data = { 'long': IndexedDict(), 'short': IndexedDict() } # 'short' is required as a placeholder
			if self.master_share:
				self.data['long'][self.master_share.sid] = (1,self.master_share.nonce)
			self._generate(count-1)
			self.last_share = ls = SeedShareLast(self)
			if last_share_debug(ls) or ls.sid in self.data['long'] or ls.sid == parent_seed.sid:
				# collision: throw out entire split list and redo with new start nonce
				if g.debug_subseed:
					self._collision_debug_msg(ls.sid,count,nonce,'nonce_start',debug_last_share)
			else:
				self.data['long'][ls.sid] = (count,nonce)
				break
		else:
			raise SubSeedNonceRangeExceeded('nonce range exceeded')

		if g.debug_subseed:
			A = parent_seed.data
			B = self.join().data
			assert A == B,'Data mismatch!\noriginal seed: {!r}\nrejoined seed: {!r}'.format(A,B)

	def get_share_by_idx(self,idx,base_seed=False):
		if idx < 1 or idx > self.count:
			raise RangeError('{}: share index out of range'.format(idx))
		elif idx == self.count:
			return self.last_share
		elif self.master_share and idx == 1:
			return self.master_share if base_seed else self.master_share.derived_seed
		else:
			ss_idx = SubSeedIdx(str(idx) + 'L')
			return self.get_subseed_by_ss_idx(ss_idx)

	def get_share_by_seed_id(self,sid,base_seed=False):
		if sid == self.data['long'].key(self.count-1):
			return self.last_share
		elif self.master_share and sid == self.data['long'].key(0):
			return self.master_share if base_seed else self.master_share.derived_seed
		else:
			return self.get_subseed_by_seed_id(sid)

	def join(self):
		return Seed.join_shares(self.get_share_by_idx(i+1) for i in range(len(self)))

	def format(self):
		assert self.split_type == 'N-of-N'
		fs1 = '    {}\n'
		fs2 = '{i:>5}: {}\n'
		mfs1,mfs2,midx,msid = ('','','','')
		if self.master_share:
			mfs1,mfs2 = (' with master share #{} ({})',' (master share #{})')
			midx,msid = (self.master_share.idx,self.master_share.sid)

		hdr  = '    {} {} ({} bits)\n'.format('Seed:',self.parent_seed.sid.hl(),self.parent_seed.bitlen)
		hdr += '    {} {c}-of-{c} (XOR){m}\n'.format('Split Type:',c=self.count,m=mfs1.format(midx,msid))
		hdr += '    {} {}\n\n'.format('ID String:',self.id_str.hl())
		hdr += fs1.format('Shares')
		hdr += fs1.format('------')

		sl = self.data['long'].keys
		body1 = fs2.format(sl[0]+mfs2.format(midx),i=1)
		body = (fs2.format(sl[n],i=n+1) for n in range(1,len(self)))

		return hdr + body1 + ''.join(body)

class SeedShareBase(MMGenObject):

	@property
	def fn_stem(self):
		pl = self.parent_list
		msdata = '_with_master{}'.format(pl.master_share.idx) if pl.master_share else ''
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

	def get_desc(self,ui=False):
		pl = self.parent_list
		mss = ', with master share #{}'.format(pl.master_share.idx) if pl.master_share else ''
		if ui:
			m   = ( yellow("(share {} of {} of ")
					+ pl.parent_seed.sid.hl()
					+ yellow(', split id ')
					+ pl.id_str.hl(encl="''")
					+ yellow('{})') )
		else:
			m = "share {} of {} of " + pl.parent_seed.sid + ", split id '" + pl.id_str + "'{}"
		return m.format(self.idx,pl.count,mss)

class SeedShare(SeedShareBase,SubSeed):

	@staticmethod
	def make_subseed_bin(parent_list,idx:int,nonce:int,length:str):
		seed = parent_list.parent_seed
		assert parent_list.have_short == False
		assert length == 'long'
		# field maximums: id_str: none (256 chars), count: 65535 (1024), idx: 65535 (1024), nonce: 65535 (1000)
		scramble_key = '{}:{}:'.format(parent_list.split_type,parent_list.id_str).encode() + \
						parent_list.count.to_bytes(2,'big') + idx.to_bytes(2,'big') + nonce.to_bytes(2,'big')
		if parent_list.master_share:
			scramble_key += b':master:' + parent_list.master_share.idx.to_bytes(2,'big')
		return scramble_seed(seed.data,scramble_key)[:seed.byte_len]

class SeedShareLast(SeedShareBase,SeedBase):

	idx = ImmutableAttr(SeedShareIdx)
	nonce = 0

	def __init__(self,parent_list):
		self.idx = parent_list.count
		self.parent_list = parent_list
		SeedBase.__init__(self,seed_bin=self.make_subseed_bin(parent_list))

	@staticmethod
	def make_subseed_bin(parent_list):
		seed_list = (parent_list.get_share_by_idx(i+1) for i in range(len(parent_list)))
		seed = parent_list.parent_seed

		ret = int(seed.data.hex(),16)
		for ss in seed_list:
			ret ^= int(ss.data.hex(),16)

		return ret.to_bytes(seed.byte_len,'big')

class SeedShareMaster(SeedBase,SeedShareBase):

	idx   = ImmutableAttr(MasterShareIdx)
	nonce = ImmutableAttr(int,typeconv=False)

	def __init__(self,parent_list,idx,nonce):
		self.idx = idx
		self.nonce = nonce
		self.parent_list = parent_list
		SeedBase.__init__(self,self.make_base_seed_bin())

		self.derived_seed = SeedBase(self.make_derived_seed_bin(parent_list.id_str,parent_list.count))

	@property
	def fn_stem(self):
		return '{}-MASTER{}[{}]'.format(
			self.parent_list.parent_seed.sid,
			self.idx,
			self.sid)

	def make_base_seed_bin(self):
		seed = self.parent_list.parent_seed
		# field maximums: idx: 65535 (1024)
		scramble_key = b'master_share:' + self.idx.to_bytes(2,'big') + self.nonce.to_bytes(2,'big')
		return scramble_seed(seed.data,scramble_key)[:seed.byte_len]

	# Don't bother with avoiding seed ID collision here, as sid of derived seed is not used
	# by user as an identifier
	def make_derived_seed_bin(self,id_str,count):
		# field maximums: id_str: none (256 chars), count: 65535 (1024)
		scramble_key = id_str.encode() + b':' + count.to_bytes(2,'big')
		return scramble_seed(self.data,scramble_key)[:self.byte_len]

	def get_desc(self,ui=False):
		psid = self.parent_list.parent_seed.sid
		mss = 'master share #{} of '.format(self.idx)
		return yellow('(' + mss) + psid.hl() + yellow(')') if ui else mss + psid

class SeedShareMasterJoining(SeedShareMaster):

	id_str = ImmutableAttr(SeedSplitIDString)
	count  = ImmutableAttr(SeedShareCount)

	def __init__(self,idx,base_seed,id_str,count):
		SeedBase.__init__(self,seed_bin=base_seed.data)

		self.id_str = id_str or 'default'
		self.count = count
		self.derived_seed = SeedBase(self.make_derived_seed_bin(self.id_str,self.count))
