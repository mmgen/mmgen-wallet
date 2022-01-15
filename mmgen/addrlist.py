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
addrlist.py: Address list classes for the MMGen suite
"""

from hashlib import sha256,sha512
from .util import qmsg,qmsg_r,suf,make_chksum_N,Msg
from .objmethods import MMGenObject,Hilite,InitErrors
from .obj import MMGenListItem,ListItemAttr,MMGenDict,WalletPassword
from .seed import SeedID
from .key import PrivKey
from .addr import MMGenID,MMGenAddrType,CoinAddr,AddrIdx,AddrListID,ViewKey

def dmsg_sc(desc,data):
	from .globalvars import g
	if g.debug_addrlist:
		Msg(f'sc_debug_{desc}: {data}')

class AddrIdxList(list,InitErrors,MMGenObject):
	max_len = 1000000
	def __init__(self,fmt_str=None,idx_list=None,sep=','):
		try:
			if idx_list:
				return list.__init__(self,sorted({AddrIdx(i) for i in idx_list}))
			elif fmt_str:
				ret = []
				for i in (fmt_str.split(sep)):
					j = i.split('-')
					if len(j) == 1:
						idx = AddrIdx(i)
						if not idx:
							break
						ret.append(idx)
					elif len(j) == 2:
						beg = AddrIdx(j[0])
						if not beg:
							break
						end = AddrIdx(j[1])
						if not beg or (end < beg):
							break
						ret.extend([AddrIdx(x) for x in range(beg,end+1)])
					else: break
				else:
					return list.__init__(self,sorted(set(ret))) # fell off end of loop - success
				raise ValueError(f'{i!r}: invalid range')
		except Exception as e:
			return type(self).init_fail(e,idx_list or fmt_str)

class AddrListEntryBase(MMGenListItem):
	invalid_attrs = {'proto'}
	def __init__(self,proto,**kwargs):
		self.__dict__['proto'] = proto
		MMGenListItem.__init__(self,**kwargs)

class AddrListEntry(AddrListEntryBase):
	addr          = ListItemAttr(CoinAddr,include_proto=True)
	idx           = ListItemAttr(AddrIdx) # not present in flat addrlists
	label         = ListItemAttr('TwComment',reassign_ok=True)
	sec           = ListItemAttr(PrivKey,include_proto=True)
	viewkey       = ListItemAttr(ViewKey,include_proto=True)
	wallet_passwd = ListItemAttr('WalletPassword')

class AddrListChksum(str,Hilite):
	color = 'pink'
	trunc_ok = False

	def __new__(cls,addrlist):
		ea = addrlist.al_id.mmtype.extra_attrs or () # add viewkey and passwd to the mix, if present
		lines = [' '.join(
					addrlist.chksum_rec_f(e) +
					tuple(getattr(e,a) for a in ea if getattr(e,a))
				) for e in addrlist.data]
		return str.__new__(cls,make_chksum_N(' '.join(lines), nchars=16, sep=True))

class AddrListIDStr(str,Hilite):
	color = 'green'
	trunc_ok = False

	def __new__(cls,addrlist,fmt_str=None):
		idxs = [e.idx for e in addrlist.data]
		prev = idxs[0]
		ret = prev,
		for i in idxs[1:]:
			if i == prev + 1:
				if i == idxs[-1]:
					ret += '-', i
			else:
				if prev != ret[-1]:
					ret += '-', prev
				ret += ',', i
			prev = i
		s = ''.join(map(str,ret))

		if fmt_str:
			ret = fmt_str.format(s)
		else:
			bc = (addrlist.proto.base_coin,addrlist.proto.coin)[addrlist.proto.base_coin=='ETH']
			mt = addrlist.al_id.mmtype
			ret = '{}{}{}[{}]'.format(
				addrlist.al_id.sid,
				('-'+bc,'')[bc == 'BTC'],
				('-'+mt,'')[mt in ('L','E')],
				s )

		dmsg_sc('id_str',ret[8:].split('[')[0])

		return str.__new__(cls,ret)

class AddrListData(list,MMGenObject):
	pass

class AddrList(MMGenObject): # Address info for a single seed ID
	entry_type   = AddrListEntry
	main_attr    = 'addr'
	desc         = 'address'
	gen_desc     = 'address'
	gen_desc_pl  = 'es'
	gen_addrs    = True
	gen_passwds  = False
	gen_keys     = False
	has_keys     = False
	chksum_rec_f = lambda foo,e: ( str(e.idx), e.addr )

	def __init__(self,proto,
			addrfile  = '',
			al_id     = '',
			adata     = [],
			seed      = '',
			addr_idxs = '',
			src       = '',
			addrlist  = '',
			keylist   = '',
			mmtype    = None,
			skip_key_address_validity_check = False,
			skip_chksum = False,
		):

		self.skip_ka_check = skip_key_address_validity_check
		self.proto = proto
		do_chksum = False

		mmtype = mmtype or proto.dfl_mmtype
		assert mmtype in MMGenAddrType.mmtypes, f'{mmtype}: mmtype not in {MMGenAddrType.mmtypes!r}'

		from .protocol import CoinProtocol
		self.bitcoin_addrtypes = tuple(
			MMGenAddrType(CoinProtocol.Bitcoin,key).name for key in CoinProtocol.Bitcoin.mmtypes)

		if seed and addr_idxs and mmtype: # data from seed + idxs
			self.al_id,src = AddrListID(seed.sid,mmtype),'gen'
			adata = self.generate(seed,addr_idxs)
			do_chksum = True
		elif addrfile:           # data from MMGen address file
			self.infile = addrfile
			adata = self.get_file().parse_file(addrfile) # sets self.al_id
			do_chksum = True
		elif al_id and adata:    # data from tracking wallet
			self.al_id = al_id
		elif addrlist:           # data from flat address list
			self.al_id = None
			from .util import remove_dups
			addrlist = remove_dups(addrlist,edesc='address',desc='address list')
			adata = AddrListData([AddrListEntry(proto=proto,addr=a) for a in addrlist])
		elif keylist:            # data from flat key list
			self.al_id = None
			keylist = remove_dups(keylist,edesc='key',desc='key list',hide=True)
			adata = AddrListData([AddrListEntry(proto=proto,sec=PrivKey(proto=proto,wif=k)) for k in keylist])
		elif seed or addr_idxs:
			die(3,'Must specify both seed and addr indexes')
		elif al_id or adata:
			die(3,'Must specify both al_id and adata')
		else:
			die(3,f'Incorrect arguments for {type(self).__name__}')

		# al_id,adata now set
		self.data = adata
		self.num_addrs = len(adata)
		self.fmt_data = ''
		self.chksum = None

		if self.al_id == None:
			return

		self.id_str = AddrListIDStr(self)

		if type(self) == KeyList:
			return

		if do_chksum and not skip_chksum:
			self.chksum = AddrListChksum(self)
			self.do_chksum_msg(record=src=='gen')

	def do_chksum_msg(self,record):
		chk = 'Check this value against your records'
		rec = f'Record this checksum: it will be used to verify the {self.desc} file in the future'
		qmsg(
			f'Checksum for {self.desc} data {self.id_str.hl()}: {self.chksum.hl()}\n' +
			(chk,rec)[record] )

	def generate(self,seed,addr_idxs):
		assert type(addr_idxs) is AddrIdxList

		seed = self.scramble_seed(seed.data)
		dmsg_sc('seed',seed[:8].hex())

		mmtype = self.al_id.mmtype

		gen_wallet_passwd = type(self) == KeyAddrList and 'wallet_passwd' in mmtype.extra_attrs
		gen_viewkey       = type(self) == KeyAddrList and 'viewkey' in mmtype.extra_attrs

		if self.gen_addrs:
			from .addr import KeyGenerator,AddrGenerator
			kg = KeyGenerator( self.proto, mmtype )
			ag = AddrGenerator( self.proto, mmtype )

		t_addrs,out = ( len(addr_idxs), AddrListData() )
		le = self.entry_type
		num,pos = (0,0)

		from .globalvars import g

		while pos != t_addrs:
			seed = sha512(seed).digest()
			num += 1 # round

			if num != addr_idxs[pos]:
				continue

			pos += 1

			if not g.debug:
				qmsg_r(f'\rGenerating {self.gen_desc} #{num} ({pos} of {t_addrs})')

			e = le(proto=self.proto,idx=num)

			# Secret key is double sha256 of seed hash round /num/
			e.sec = PrivKey(
				self.proto,
				sha256(sha256(seed).digest()).digest(),
				compressed  = mmtype.compressed,
				pubkey_type = mmtype.pubkey_type )

			if self.gen_addrs:
				pubhex = kg.to_pubhex(e.sec)
				e.addr = ag.to_addr(pubhex)
				if gen_viewkey:
					e.viewkey = ag.to_viewkey(pubhex)
				if gen_wallet_passwd:
					e.wallet_passwd = ag.to_wallet_passwd(e.sec)
			elif self.gen_passwds:
				e.passwd = self.gen_passwd(e.sec) # TODO - own type

			out.append(e)

			if g.debug_addrlist:
				Msg(f'generate():\n{e.pfmt()}')

		qmsg('\r{}: {} {}{} generated{}'.format(
			self.al_id.hl(),
			t_addrs,
			self.gen_desc,
			suf(t_addrs,self.gen_desc_pl),
			' ' * 15 ))

		return out

	def gen_wallet_passwd(self,privbytes):
		from .protocol import hash256
		return WalletPassword( hash256(privbytes)[:16].hex() )

	def check_format(self,addr):
		return True # format is checked when added to list entry object

	def scramble_seed(self,seed):
		is_btcfork = self.proto.base_coin == 'BTC'
		if is_btcfork and self.al_id.mmtype == 'L' and not self.proto.testnet:
			dmsg_sc('str','(none)')
			return seed
		if self.proto.base_coin == 'ETH':
			scramble_key = self.proto.coin.lower()
		else:
			scramble_key = (self.proto.coin.lower()+':','')[is_btcfork] + self.al_id.mmtype.name
		from .crypto import scramble_seed
		if self.proto.testnet:
			scramble_key += ':' + self.proto.network
		dmsg_sc('str',scramble_key)
		return scramble_seed(seed,scramble_key.encode())

	def idxs(self):
		return [e.idx for e in self.data]

	def addrs(self):
		return [f'{self.al_id.sid}:{e.idx}' for e in self.data]

	def addrpairs(self):
		return [(e.idx,e.addr) for e in self.data]

	def coinaddrs(self):
		return [e.addr for e in self.data]

	def comments(self):
		return [e.label for e in self.data]

	def entry(self,idx):
		for e in self.data:
			if idx == e.idx:
				return e

	def coinaddr(self,idx):
		for e in self.data:
			if idx == e.idx:
				return e.addr

	def comment(self,idx):
		for e in self.data:
			if idx == e.idx:
				return e.label

	def set_comment(self,idx,comment):
		for e in self.data:
			if idx == e.idx:
				e.label = comment

	def make_reverse_dict_addrlist(self,coinaddrs):
		d = MMGenDict()
		b = coinaddrs
		for e in self.data:
			try:
				d[b[b.index(e.addr)]] = ( MMGenID(self.proto, f'{self.al_id}:{e.idx}'), e.label )
			except ValueError:
				pass
		return d

	def add_wifs(self,key_list):
		"""
		Match WIF keys in a flat list to addresses in self by generating all
		possible addresses for each key.
		"""
		def gen_addr(pk,t):
			at = self.proto.addr_type(t)
			from .addr import KeyGenerator,AddrGenerator
			kg = KeyGenerator(self.proto,at)
			ag = AddrGenerator(self.proto,at)
			return ag.to_addr(kg.to_pubhex(pk))

		compressed_types = set(self.proto.mmtypes) - {'L','E'}
		uncompressed_types = set(self.proto.mmtypes) & {'L','E'}

		def gen():
			for wif in key_list:
				pk = PrivKey(proto=self.proto,wif=wif)
				for t in (compressed_types if pk.compressed else uncompressed_types):
					yield ( gen_addr(pk,t), pk )

		addrs4keys = dict(gen())

		for d in self.data:
			if d.addr in addrs4keys:
				d.sec = addrs4keys[d.addr]

	def list_missing(self,attr):
		return [d.addr for d in self.data if not getattr(d,attr)]

	def get_file(self):
		import mmgen.addrfile as mod
		return getattr( mod, type(self).__name__.replace('List','File') )(self)

class KeyAddrList(AddrList):
	desc         = 'key-address'
	gen_desc     = 'key/address pair'
	gen_desc_pl  = 's'
	gen_keys     = True
	has_keys     = True
	chksum_rec_f = lambda foo,e: (str(e.idx), e.addr, e.sec.wif)

class KeyList(KeyAddrList):
	desc         = 'key'
	gen_desc     = 'key'
	gen_addrs    = False
