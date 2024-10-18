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
addrlist: Address list classes for the MMGen suite
"""

from .util import suf, make_chksum_N, Msg, die
from .objmethods import MMGenObject, HiliteStr, InitErrors
from .obj import MMGenListItem, ListItemAttr, MMGenDict, TwComment, WalletPassword
from .key import PrivKey
from .addr import MMGenID, MMGenAddrType, CoinAddr, AddrIdx, AddrListID, ViewKey

class AddrIdxList(tuple, InitErrors, MMGenObject):

	max_len = 1000000

	def __new__(cls, fmt_str=None, idx_list=None, sep=','):
		try:
			if fmt_str:
				def gen():
					for i in (fmt_str.split(sep)):
						j = [int(x) for x in i.split('-')]
						if len(j) == 1:
							yield j[0]
						elif len(j) == 2:
							if j[0] > j[1]:
								raise ValueError(f'{i}: invalid range')
							yield from range(j[0], j[1] + 1)
						else:
							raise ValueError(f'{i}: invalid range')
				idx_list = tuple(gen())
			return tuple.__new__(cls, sorted({AddrIdx(i) for i in (idx_list or [])}))
		except Exception as e:
			return cls.init_fail(e, idx_list or fmt_str)

	@property
	def id_str(self):

		def gen():
			i_save = self[0]
			yield f'{i_save}'
			in_range = False

			for i in self[1:]:
				if i - i_save == 1:
					in_range = True
				else:
					if in_range:
						in_range = False
						yield f'-{i_save}'
					yield f',{i}'
				i_save = i

			if in_range:
				yield f'-{i_save}'

		return ''.join(gen()) if self else ''

class AddrListEntryBase(MMGenListItem):
	invalid_attrs = {'proto'}
	def __init__(self, proto, **kwargs):
		self.__dict__['proto'] = proto
		MMGenListItem.__init__(self, **kwargs)

class AddrListEntry(AddrListEntryBase):
	addr          = ListItemAttr(CoinAddr, include_proto=True)
	addr_p2pkh    = ListItemAttr(CoinAddr, include_proto=True)
	idx           = ListItemAttr(AddrIdx) # not present in flat addrlists
	comment       = ListItemAttr(TwComment, reassign_ok=True)
	sec           = ListItemAttr(PrivKey, include_proto=True)
	viewkey       = ListItemAttr(ViewKey, include_proto=True)
	wallet_passwd = ListItemAttr(WalletPassword)

class AddrListChksum(HiliteStr):
	color = 'pink'
	trunc_ok = False

	def __new__(cls, addrlist):
		ea = addrlist.al_id.mmtype.extra_attrs or () # add viewkey and passwd to the mix, if present
		lines = [' '.join(
					addrlist.chksum_rec_f(e) +
					tuple(getattr(e, a) for a in ea if getattr(e, a))
				) for e in addrlist.data]
		return str.__new__(cls, make_chksum_N(' '.join(lines), nchars=16, sep=True))

class AddrListIDStr(HiliteStr):
	color = 'green'
	trunc_ok = False

	def __new__(cls, addrlist, fmt_str=None):
		idxs = [e.idx for e in addrlist.data]
		prev = idxs[0]
		ret = [prev]
		for i in idxs[1:]:
			if i == prev + 1:
				if i == idxs[-1]:
					ret.extend(['-', i])
			else:
				if prev != ret[-1]:
					ret.extend(['-', prev])
				ret.extend([',', i])
			prev = i
		s = ''.join(map(str, ret))

		if fmt_str:
			ret = fmt_str.format(s)
		else:
			proto = addrlist.proto
			coin = 'BTC' if proto.coin == 'BCH' and not addrlist.cfg.cashaddr else proto.coin
			mmtype = addrlist.al_id.mmtype
			ret = '{}{}{}[{}]'.format(
				addrlist.al_id.sid,
				(f'-{coin}', '')[coin == 'BTC'],
				(f'-{mmtype}', '')[mmtype in ('L', 'E')],
				s)

		addrlist.dmsg_sc('id_str', ret[8:].split('[')[0])

		return str.__new__(cls, ret)

class AddrListData(list, MMGenObject):
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
	chksum_rec_f = lambda foo, e: (str(e.idx), e.addr.views[e.addr.view_pref])

	def dmsg_sc(self, desc, data):
		Msg(f'sc_debug_{desc}: {data}')

	def noop(self, desc, data):
		pass

	def __init__(
			self,
			cfg,
			proto,
			addrfile  = '',
			al_id     = '',
			adata     = [],
			seed      = '',
			addr_idxs = '',
			src       = '',
			addrlist  = '',
			keylist   = '',
			mmtype    = None,
			key_address_validity_check = None, # None=prompt user, True=check without prompt, False=skip check
			skip_chksum = False,
			skip_chksum_msg = False,
			add_p2pkh = False):

		self.cfg = cfg
		self.ka_validity_chk = key_address_validity_check
		self.add_p2pkh = add_p2pkh
		self.proto = proto
		do_chksum = False

		if not cfg.debug_addrlist:
			self.dmsg_sc = self.noop

		if seed and addr_idxs:   # data from seed + idxs
			self.al_id = AddrListID(sid=seed.sid, mmtype=MMGenAddrType(proto, mmtype or proto.dfl_mmtype))
			src = 'gen'
			adata = self.generate(seed, addr_idxs if isinstance(addr_idxs, AddrIdxList) else AddrIdxList(addr_idxs))
			do_chksum = True
		elif addrfile:           # data from MMGen address file
			self.infile = addrfile
			adata = self.file.parse_file(addrfile) # sets self.al_id
			do_chksum = True
		elif al_id and adata:    # data from tracking wallet
			self.al_id = al_id
		elif addrlist:           # data from flat address list
			self.al_id = None
			from .util import remove_dups
			addrlist = remove_dups(addrlist, edesc='address', desc='address list')
			adata = AddrListData([AddrListEntry(proto=proto, addr=a) for a in addrlist])
		elif keylist:            # data from flat key list
			self.al_id = None
			from .util import remove_dups
			keylist = remove_dups(keylist, edesc='key', desc='key list', hide=True)
			adata = AddrListData([AddrListEntry(proto=proto, sec=PrivKey(proto=proto, wif=k)) for k in keylist])
		elif seed or addr_idxs:
			die(3, 'Must specify both seed and addr indexes')
		elif al_id or adata:
			die(3, 'Must specify both al_id and adata')
		else:
			die(3, f'Incorrect arguments for {type(self).__name__}')

		# al_id, adata now set
		self.data = adata
		self.num_addrs = len(adata)
		self.fmt_data = ''
		self.chksum = None

		if self.al_id is None:
			return

		if type(self) is ViewKeyAddrList:
			if not 'viewkey' in self.al_id.mmtype.extra_attrs:
				die(1, f'viewkeys not supported for address type {self.al_id.mmtype.desc!r}')

		self.id_str = AddrListIDStr(self)

		if type(self) is KeyList:
			return

		if do_chksum and not skip_chksum:
			self.chksum = AddrListChksum(self)
			if not skip_chksum_msg:
				self.do_chksum_msg(record=src=='gen')

	def do_chksum_msg(self, record):
		chk = 'Check this value against your records'
		rec = f'Record this checksum: it will be used to verify the {self.desc} file in the future'
		self.cfg._util.qmsg(
			f'Checksum for {self.desc} data {self.id_str.hl()}: {self.chksum.hl()}\n' +
			(chk, rec)[record])

	def generate(self, seed, addr_idxs):

		seed = self.scramble_seed(seed.data)
		self.dmsg_sc('seed', seed[:8].hex())

		mmtype = self.al_id.mmtype

		gen_wallet_passwd = type(self) in (KeyAddrList, ViewKeyAddrList) and 'wallet_passwd' in mmtype.extra_attrs
		gen_viewkey       = type(self) in (KeyAddrList, ViewKeyAddrList) and 'viewkey' in mmtype.extra_attrs

		if self.gen_addrs:
			from .keygen import KeyGenerator
			from .addrgen import AddrGenerator
			kg = KeyGenerator(self.cfg, self.proto, mmtype.pubkey_type)
			ag = AddrGenerator(self.cfg, self.proto, mmtype)
			if self.add_p2pkh:
				ag2 = AddrGenerator(self.cfg, self.proto, 'compressed')

		from .derive import derive_coin_privkey_bytes

		t_addrs = len(addr_idxs)
		le = self.entry_type
		out = AddrListData()
		CR = '\n' if self.cfg.debug_addrlist else '\r'

		for pk_bytes in derive_coin_privkey_bytes(seed, addr_idxs):

			if not self.cfg.debug:
				self.cfg._util.qmsg_r(
					f'{CR}Generating {self.gen_desc} #{pk_bytes.idx} ({pk_bytes.pos} of {t_addrs})')

			e = le(proto=self.proto, idx=pk_bytes.idx)

			e.sec = PrivKey(
				self.proto,
				pk_bytes.data,
				compressed  = mmtype.compressed,
				pubkey_type = mmtype.pubkey_type)

			if self.gen_addrs:
				data = kg.gen_data(e.sec)
				e.addr = ag.to_addr(data)
				if self.add_p2pkh:
					e.addr_p2pkh = ag2.to_addr(data)
				if gen_viewkey:
					e.viewkey = ag.to_viewkey(data)
				if gen_wallet_passwd:
					e.wallet_passwd = self.gen_wallet_passwd(
						e.viewkey.encode() if type(self) is ViewKeyAddrList else e.sec)
			elif self.gen_passwds:
				e.passwd = self.gen_passwd(e.sec) # TODO - own type

			out.append(e)

		self.cfg._util.qmsg('{}{}: {} {}{} generated{}'.format(
			CR,
			self.al_id.hl(),
			t_addrs,
			self.gen_desc,
			suf(t_addrs, self.gen_desc_pl),
			' ' * 15))

		return out

	def gen_wallet_passwd(self, privbytes):
		from .proto.btc.common import hash256
		return WalletPassword(hash256(privbytes)[:16].hex())

	def check_format(self, addr):
		return True # format is checked when added to list entry object

	def scramble_seed(self, seed):
		is_btcfork = self.proto.base_coin == 'BTC'
		if is_btcfork and self.al_id.mmtype == 'L' and not self.proto.testnet:
			self.dmsg_sc('str', '(none)')
			return seed
		if self.proto.base_coin == 'ETH':
			scramble_key = self.proto.coin.lower()
		else:
			scramble_key = (self.proto.coin.lower()+':', '')[is_btcfork] + self.al_id.mmtype.name
		from .crypto import Crypto
		if self.proto.testnet:
			scramble_key += ':' + self.proto.network
		self.dmsg_sc('str', scramble_key)
		return Crypto(self.cfg).scramble_seed(seed, scramble_key.encode())

	def idxs(self):
		return [e.idx for e in self.data]

	def addrs(self):
		return [f'{self.al_id.sid}:{e.idx}' for e in self.data]

	def addrpairs(self):
		return [(e.idx, e.addr) for e in self.data]

	def coinaddrs(self):
		return [e.addr for e in self.data]

	def comments(self):
		return [e.comment for e in self.data]

	def entry(self, idx):
		for e in self.data:
			if idx == e.idx:
				return e

	def coinaddr(self, idx):
		for e in self.data:
			if idx == e.idx:
				return e.addr

	def comment(self, idx):
		for e in self.data:
			if idx == e.idx:
				return e.comment

	def set_comment(self, idx, comment):
		for e in self.data:
			if idx == e.idx:
				e.comment = comment

	def make_reverse_dict_addrlist(self, coinaddrs):
		d = MMGenDict()
		b = coinaddrs
		for e in self.data:
			try:
				d[b[b.index(e.addr)]] = (MMGenID(self.proto, f'{self.al_id}:{e.idx}'), e.comment)
			except ValueError:
				pass
		return d

	def add_wifs(self, key_list):
		"""
		Match WIF keys in a flat list to addresses in self by generating all
		possible addresses for each key.
		"""
		def gen_addr(pk, t):
			at = self.proto.addr_type(t)
			from .keygen import KeyGenerator
			from .addrgen import AddrGenerator
			kg = KeyGenerator(self.cfg, self.proto, at.pubkey_type)
			ag = AddrGenerator(self.cfg, self.proto, at)
			return ag.to_addr(kg.gen_data(pk))

		compressed_types = set(self.proto.mmtypes) - {'L', 'E'}
		uncompressed_types = set(self.proto.mmtypes) & {'L', 'E'}

		def gen():
			for wif in key_list:
				pk = PrivKey(proto=self.proto, wif=wif)
				for t in (compressed_types if pk.compressed else uncompressed_types):
					yield (gen_addr(pk, t), pk)

		addrs4keys = dict(gen())

		for d in self.data:
			if d.addr in addrs4keys:
				d.sec = addrs4keys[d.addr]

	def list_missing(self, attr):
		return [d.addr for d in self.data if not getattr(d, attr)]

	@property
	def file(self):
		if not hasattr(self, '_file'):
			from . import addrfile
			self._file = getattr(addrfile, type(self).__name__.replace('List', 'File'))(self)
		return self._file

class KeyAddrList(AddrList):
	desc         = 'key-address'
	gen_desc     = 'key/address pair'
	gen_desc_pl  = 's'
	gen_keys     = True
	has_keys     = True
	chksum_rec_f = lambda foo, e: (str(e.idx), e.addr.views[e.addr.view_pref], e.sec.wif)

class ViewKeyAddrList(KeyAddrList):
	desc         = 'viewkey-address'
	gen_desc     = 'viewkey/address pair'
	chksum_rec_f = lambda foo, e: (str(e.idx), e.addr)

class KeyList(KeyAddrList):
	desc         = 'key'
	gen_desc     = 'key'
	gen_addrs    = False
