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
addr.py:  Address generation/display routines for the MMGen suite
"""

from hashlib import sha256,sha512
from .common import *
from .obj import *
from .baseconv import *

pnm = g.proj_name

def dmsg_sc(desc,data):
	if g.debug_addrlist: Msg('sc_debug_{}: {}'.format(desc,data))

class AddrGenerator(MMGenObject):
	def __new__(cls,addr_type):
		if type(addr_type) == str: # allow override w/o check
			gen_method = addr_type
		elif type(addr_type) == MMGenAddrType:
			assert addr_type in g.proto.mmtypes,'{}: invalid address type for coin {}'.format(addr_type,g.coin)
			gen_method = addr_type.gen_method
		else:
			raise TypeError('{}: incorrect argument type for {}()'.format(type(addr_type),cls.__name__))
		gen_methods = {
			'p2pkh':    AddrGeneratorP2PKH,
			'segwit':   AddrGeneratorSegwit,
			'bech32':   AddrGeneratorBech32,
			'ethereum': AddrGeneratorEthereum,
			'zcash_z':  AddrGeneratorZcashZ,
			'monero':   AddrGeneratorMonero}
		assert gen_method in gen_methods
		me = super(cls,cls).__new__(gen_methods[gen_method])
		me.desc = gen_methods
		return me

class AddrGeneratorP2PKH(AddrGenerator):
	def to_addr(self,pubhex):
		from .protocol import hash160
		assert type(pubhex) == PubKey
		return CoinAddr(g.proto.pubhash2addr(hash160(pubhex),p2sh=False))

	def to_segwit_redeem_script(self,pubhex):
		raise NotImplementedError('Segwit redeem script not supported by this address type')

class AddrGeneratorSegwit(AddrGenerator):
	def to_addr(self,pubhex):
		assert pubhex.compressed,'Uncompressed public keys incompatible with Segwit'
		return CoinAddr(g.proto.pubhex2segwitaddr(pubhex))

	def to_segwit_redeem_script(self,pubhex):
		assert pubhex.compressed,'Uncompressed public keys incompatible with Segwit'
		return HexStr(g.proto.pubhex2redeem_script(pubhex))

class AddrGeneratorBech32(AddrGenerator):
	def to_addr(self,pubhex):
		assert pubhex.compressed,'Uncompressed public keys incompatible with Segwit'
		from .protocol import hash160
		return CoinAddr(g.proto.pubhash2bech32addr(hash160(pubhex)))

	def to_segwit_redeem_script(self,pubhex):
		raise NotImplementedError('Segwit redeem script not supported by this address type')

class AddrGeneratorEthereum(AddrGenerator):

	def __init__(self,addr_type):

		try:
			assert not g.use_internal_keccak_module
			from sha3 import keccak_256
		except:
			from .keccak import keccak_256
		self.keccak_256 = keccak_256

		from .protocol import hash256
		self.hash256 = hash256

		return AddrGenerator.__init__(addr_type)

	def to_addr(self,pubhex):
		assert type(pubhex) == PubKey
		return CoinAddr(self.keccak_256(bytes.fromhex(pubhex[2:])).hexdigest()[24:])

	def to_wallet_passwd(self,sk_hex):
		return WalletPassword(self.hash256(sk_hex)[:32])

	def to_segwit_redeem_script(self,pubhex):
		raise NotImplementedError('Segwit redeem script not supported by this address type')

# github.com/FiloSottile/zcash-mini/zcash/address.go
class AddrGeneratorZcashZ(AddrGenerator):

	def zhash256(self,s,t):
		s = bytearray(s + bytes(32))
		s[0] |= 0xc0
		s[32] = t
		from .sha2 import Sha256
		return Sha256(s,preprocess=False).digest()

	def to_addr(self,pubhex): # pubhex is really privhex
		key = bytes.fromhex(pubhex)
		assert len(key) == 32,'{}: incorrect privkey length'.format(len(key))
		from nacl.bindings import crypto_scalarmult_base
		p2 = crypto_scalarmult_base(self.zhash256(key,1))
		from .protocol import _b58chk_encode
		ver_bytes = g.proto.addr_fmt_to_ver_bytes('zcash_z')
		ret = _b58chk_encode(ver_bytes + self.zhash256(key,0) + p2)
		return CoinAddr(ret)

	def to_viewkey(self,pubhex): # pubhex is really privhex
		key = bytes.fromhex(pubhex)
		assert len(key) == 32,'{}: incorrect privkey length'.format(len(key))
		vk = bytearray(self.zhash256(key,0)+self.zhash256(key,1))
		vk[32] &= 0xf8
		vk[63] &= 0x7f
		vk[63] |= 0x40
		from .protocol import _b58chk_encode
		ver_bytes = g.proto.addr_fmt_to_ver_bytes('viewkey')
		ret = _b58chk_encode(ver_bytes + vk)
		return ZcashViewKey(ret)

	def to_segwit_redeem_script(self,pubhex):
		raise NotImplementedError('Zcash z-addresses incompatible with Segwit')

class AddrGeneratorMonero(AddrGenerator):

	def __init__(self,addr_type):

		try:
			assert not g.use_internal_keccak_module
			from sha3 import keccak_256
		except:
			from .keccak import keccak_256
		self.keccak_256 = keccak_256

		from .protocol import hash256
		self.hash256 = hash256

		if opt.use_old_ed25519:
			from .ed25519 import edwards,encodepoint,B,scalarmult
		else:
			from .ed25519ll_djbec import scalarmult
			from .ed25519 import edwards,encodepoint,B

		self.edwards     = edwards
		self.encodepoint = encodepoint
		self.scalarmult  = scalarmult
		self.B           = B

		return AddrGenerator.__init__(addr_type)

	def b58enc(self,addr_bytes):
		enc = baseconv.frombytes
		l = len(addr_bytes)
		a = ''.join([enc(addr_bytes[i*8:i*8+8],'b58',pad=11,tostr=True) for i in range(l//8)])
		b = enc(addr_bytes[l-l%8:],'b58',pad=7,tostr=True)
		return a + b

	def to_addr(self,sk_hex): # sk_hex instead of pubhex

		# Source and license for scalarmultbase function:
		#   https://github.com/bigreddmachine/MoneroPy/blob/master/moneropy/crypto/ed25519.py
		# Copyright (c) 2014-2016, The Monero Project
		# All rights reserved.
		def scalarmultbase(e):
			if e == 0: return [0, 1]
			Q = self.scalarmult(self.B, e//2)
			Q = self.edwards(Q, Q)
			if e & 1: Q = self.edwards(Q, self.B)
			return Q

		def hex2int_le(hexstr):
			return int((bytes.fromhex(hexstr)[::-1]).hex(),16)

		vk_hex = self.to_viewkey(sk_hex)
		pk_str  = self.encodepoint(scalarmultbase(hex2int_le(sk_hex)))
		pvk_str = self.encodepoint(scalarmultbase(hex2int_le(vk_hex)))
		addr_p1 = g.proto.addr_fmt_to_ver_bytes('monero') + pk_str + pvk_str

		return CoinAddr(self.b58enc(addr_p1 + self.keccak_256(addr_p1).digest()[:4]))

	def to_wallet_passwd(self,sk_hex):
		return WalletPassword(self.hash256(sk_hex)[:32])

	def to_viewkey(self,sk_hex):
		assert len(sk_hex) == 64,'{}: incorrect privkey length'.format(len(sk_hex))
		return MoneroViewKey(g.proto.preprocess_key(self.keccak_256(bytes.fromhex(sk_hex)).digest(),None).hex())

	def to_segwit_redeem_script(self,sk_hex):
		raise NotImplementedError('Monero addresses incompatible with Segwit')

class KeyGenerator(MMGenObject):

	def __new__(cls,addr_type,generator=None,silent=False):
		if type(addr_type) == str: # allow override w/o check
			pubkey_type = addr_type
		elif type(addr_type) == MMGenAddrType:
			assert addr_type in g.proto.mmtypes,'{}: invalid address type for coin {}'.format(addr_type,g.coin)
			pubkey_type = addr_type.pubkey_type
		else:
			raise TypeError('{}: incorrect argument type for {}()'.format(type(addr_type),cls.__name__))
		if pubkey_type == 'std':
			if cls.test_for_secp256k1(silent=silent) and generator != 1:
				if not opt.key_generator or opt.key_generator == 2 or generator == 2:
					return super(cls,cls).__new__(KeyGeneratorSecp256k1)
			else:
				qmsg('Using (slow) native Python ECDSA library for address generation')
				return super(cls,cls).__new__(KeyGeneratorPython)
		elif pubkey_type in ('zcash_z','monero'):
			me = super(cls,cls).__new__(KeyGeneratorDummy)
			me.desc = 'mmgen-'+pubkey_type
			return me
		else:
			raise ValueError('{}: invalid pubkey_type argument'.format(pubkey_type))

	@classmethod
	def test_for_secp256k1(self,silent=False):
		try:
			from .secp256k1 import priv2pub
			m = 'Unable to execute priv2pub() from secp256k1 extension module'
			assert priv2pub(bytes.fromhex('deadbeef'*8),1),m
			return True
		except:
			return False

import ecdsa
class KeyGeneratorPython(KeyGenerator):

	desc = 'mmgen-python-ecdsa'

	def __init__(self,*args,**kwargs):
		# secp256k1: http://www.oid-info.com/get/1.3.132.0.10
		p = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f
		r = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141
		b = 0x0000000000000000000000000000000000000000000000000000000000000007
		a = 0x0000000000000000000000000000000000000000000000000000000000000000
		Gx = 0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798
		Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8
		curve_fp = ecdsa.ellipticcurve.CurveFp(p,a,b)
		G = ecdsa.ellipticcurve.Point(curve_fp,Gx,Gy,r)
		oid = (1,3,132,0,10)
		self.secp256k1 = ecdsa.curves.Curve('secp256k1',curve_fp,G,oid)

	# devdoc/guide_wallets.md:
	# Uncompressed public keys start with 0x04; compressed public keys begin with 0x03 or
	# 0x02 depending on whether they're greater or less than the midpoint of the curve.
	def privnum2pubhex(self,numpriv,compressed=False):
		pko = ecdsa.SigningKey.from_secret_exponent(numpriv,self.secp256k1)
		# pubkey = x (32 bytes) + y (32 bytes) (unsigned big-endian)
		pubkey = (pko.get_verifying_key().to_string()).hex()
		if compressed: # discard Y coord, replace with appropriate version byte
			# even y: <0, odd y: >0 -- https://bitcointalk.org/index.php?topic=129652.0
			return ('03','02')[pubkey[-1] in '02468ace'] + pubkey[:64]
		else:
			return '04' + pubkey

	def to_pubhex(self,privhex):
		assert type(privhex) == PrivKey
		return PubKey(self.privnum2pubhex(
			int(privhex,16),compressed=privhex.compressed),compressed=privhex.compressed)

class KeyGeneratorSecp256k1(KeyGenerator):
	desc = 'mmgen-secp256k1'
	def to_pubhex(self,privhex):
		assert type(privhex) == PrivKey
		from .secp256k1 import priv2pub
		return PubKey(priv2pub(bytes.fromhex(privhex),int(privhex.compressed)).hex(),compressed=privhex.compressed)

class KeyGeneratorDummy(KeyGenerator):
	desc = 'mmgen-dummy'
	def to_pubhex(self,privhex):
		assert type(privhex) == PrivKey
		return PubKey(privhex,compressed=privhex.compressed)

class AddrListEntry(MMGenListItem):
	addr          = ListItemAttr('CoinAddr')
	idx           = ListItemAttr('AddrIdx') # not present in flat addrlists
	label         = ListItemAttr('TwComment',reassign_ok=True)
	sec           = ListItemAttr(PrivKey,typeconv=False)
	viewkey       = ListItemAttr('ViewKey')
	wallet_passwd = ListItemAttr('WalletPassword')

class PasswordListEntry(MMGenListItem):
	passwd = ListItemAttr(str,typeconv=False) # TODO: create Password type
	idx    = ImmutableAttr('AddrIdx')
	label  = ListItemAttr('TwComment',reassign_ok=True)
	sec    = ListItemAttr(PrivKey,typeconv=False)

class AddrListChksum(str,Hilite):
	color = 'pink'
	trunc_ok = False

	def __new__(cls,addrlist):
		ea = addrlist.al_id.mmtype.extra_attrs # add viewkey and passwd to the mix, if present
		if ea == None: ea = ()
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
				if i == idxs[-1]: ret += '-', i
			else:
				if prev != ret[-1]: ret += '-', prev
				ret += ',', i
			prev = i
		s = ''.join(map(str,ret))

		if fmt_str:
			ret = fmt_str.format(s)
		else:
			bc = (g.proto.base_coin,g.coin)[g.proto.base_coin=='ETH']
			mt = addrlist.al_id.mmtype
			ret = '{}{}{}[{}]'.format(addrlist.al_id.sid,('-'+bc,'')[bc=='BTC'],('-'+mt,'')[mt in ('L','E')],s)

		dmsg_sc('id_str',ret[8:].split('[')[0])

		return str.__new__(cls,ret)

class AddrList(MMGenObject): # Address info for a single seed ID
	msgs = {
	'file_header': """
# {pnm} address file
#
# This file is editable.
# Everything following a hash symbol '#' is a comment and ignored by {pnm}.
# A text label of {n} screen cells or less may be added to the right of each
# address, and it will be appended to the tracking wallet label upon import.
# The label may contain any printable ASCII symbol.
""".strip().format(n=TwComment.max_screen_width,pnm=pnm),
	'record_chksum': """
Record this checksum: it will be used to verify the address file in the future
""".strip(),
	'check_chksum': 'Check this value against your records',
	'removed_dup_keys': """
Removed {{}} duplicate WIF key{{}} from keylist (also in {pnm} key-address file
""".strip().format(pnm=pnm)
	}
	entry_type = AddrListEntry
	main_attr = 'addr'
	data_desc = 'address'
	file_desc = 'addresses'
	gen_desc  = 'address'
	gen_desc_pl = 'es'
	gen_addrs = True
	gen_passwds = False
	gen_keys = False
	has_keys = False
	ext      = 'addrs'
	chksum_rec_f = lambda foo,e: (str(e.idx), e.addr)
	line_ctr = 0

	def __init__(self,addrfile='',al_id='',adata=[],seed='',addr_idxs='',src='',
					addrlist='',keylist='',mmtype=None):

		do_chksum = True
		self.update_msgs()
		mmtype = mmtype or g.proto.dfl_mmtype
		assert mmtype in MMGenAddrType.mmtypes,'{}: mmtype not in {}'.format(mmtype,repr(MMGenAddrType.mmtypes))

		if seed and addr_idxs:   # data from seed + idxs
			self.al_id,src = AddrListID(seed.sid,mmtype),'gen'
			adata = self.generate(seed,addr_idxs)
		elif addrfile:           # data from MMGen address file
			self.infile = addrfile
			adata = self.parse_file(addrfile) # sets self.al_id
		elif al_id and adata:    # data from tracking wallet
			self.al_id = al_id
			do_chksum = False
		elif addrlist:           # data from flat address list
			self.al_id = None
			adata = AddrListList([AddrListEntry(addr=a) for a in set(addrlist)])
		elif keylist:            # data from flat key list
			self.al_id = None
			adata = AddrListList([AddrListEntry(sec=PrivKey(wif=k)) for k in set(keylist)])
		elif seed or addr_idxs:
			die(3,'Must specify both seed and addr indexes')
		elif al_id or adata:
			die(3,'Must specify both al_id and adata')
		else:
			die(3,'Incorrect arguments for {}'.format(type(self).__name__))

		# al_id,adata now set
		self.data = adata
		self.num_addrs = len(adata)
		self.fmt_data = ''
		self.chksum = None

		if self.al_id == None: return

		self.id_str = AddrListIDStr(self)
		if type(self) == KeyList: return

		if do_chksum:
			self.chksum = AddrListChksum(self)
			qmsg('Checksum for {} data {}: {}'.format(
					self.data_desc,self.id_str.hl(),self.chksum.hl()))
			qmsg(self.msgs[('check_chksum','record_chksum')[src=='gen']])

	def update_msgs(self):
		self.msgs = AddrList.msgs
		self.msgs.update(type(self).msgs)

	def generate(self,seed,addrnums):
		assert type(addrnums) is AddrIdxList

		seed = self.scramble_seed(seed.data)
		dmsg_sc('seed',seed[:8].hex())

		compressed = self.al_id.mmtype.compressed
		pubkey_type = self.al_id.mmtype.pubkey_type

		gen_wallet_passwd = type(self) == KeyAddrList and 'wallet_passwd' in self.al_id.mmtype.extra_attrs
		gen_viewkey       = type(self) == KeyAddrList and 'viewkey' in self.al_id.mmtype.extra_attrs

		if self.gen_addrs:
			kg = KeyGenerator(self.al_id.mmtype)
			ag = AddrGenerator(self.al_id.mmtype)

		t_addrs,num,pos,out = len(addrnums),0,0,AddrListList()
		le = self.entry_type

		while pos != t_addrs:
			seed = sha512(seed).digest()
			num += 1 # round

			if num != addrnums[pos]: continue

			pos += 1

			if not g.debug:
				qmsg_r('\rGenerating {} #{} ({} of {})'.format(self.gen_desc,num,pos,t_addrs))

			e = le(idx=num)

			# Secret key is double sha256 of seed hash round /num/
			e.sec = PrivKey(sha256(sha256(seed).digest()).digest(),compressed=compressed,pubkey_type=pubkey_type)

			if self.gen_addrs:
				pubhex = kg.to_pubhex(e.sec)
				e.addr = ag.to_addr(pubhex)
				if gen_viewkey:
					e.viewkey = ag.to_viewkey(pubhex)
				if gen_wallet_passwd:
					e.wallet_passwd = ag.to_wallet_passwd(e.sec)

			if type(self) == PasswordList:
				e.passwd = str(self.make_passwd(e.sec)) # TODO - own type
				dmsg('Key {:>03}: {}'.format(pos,e.passwd))

			out.append(e)
			if g.debug_addrlist:
				Msg('generate():\n{}'.format(e.pfmt()))

		qmsg('\r{}: {} {}{} generated{}'.format(
				self.al_id.hl(),t_addrs,self.gen_desc,suf(t_addrs,self.gen_desc_pl),' '*15))
		return out

	def check_format(self,addr):
		return True # format is checked when added to list entry object

	def scramble_seed(self,seed):
		is_btcfork = g.proto.base_coin == 'BTC'
		if is_btcfork and self.al_id.mmtype == 'L' and not g.proto.is_testnet():
			dmsg_sc('str','(none)')
			return seed
		if g.proto.base_coin == 'ETH':
			scramble_key = g.coin.lower()
		else:
			scramble_key = (g.coin.lower()+':','')[is_btcfork] + self.al_id.mmtype.name
		from .crypto import scramble_seed
		if g.proto.is_testnet():
			scramble_key += ':testnet'
		dmsg_sc('str',scramble_key)
		return scramble_seed(seed,scramble_key.encode())

	def encrypt(self,desc='new key list'):
		from .crypto import mmgen_encrypt
		self.fmt_data = mmgen_encrypt(self.fmt_data.encode(),desc,'')
		self.ext += '.'+g.mmenc_ext

	def write_to_file(self,ask_tty=True,ask_write_default_yes=False,binary=False,desc=None):
		tn = ('','.testnet')[g.proto.is_testnet()]
		fn = '{}{x}{}.{}'.format(self.id_str,tn,self.ext,x='-α' if g.debug_utf8 else '')
		ask_tty = self.has_keys and not opt.quiet
		write_data_to_file(fn,self.fmt_data,desc or self.file_desc,ask_tty=ask_tty,binary=binary)

	def idxs(self):
		return [e.idx for e in self.data]

	def addrs(self):
		return ['{}:{}'.format(self.al_id.sid,e.idx) for e in self.data]

	def addrpairs(self):
		return [(e.idx,e.addr) for e in self.data]

	def coinaddrs(self):
		return [e.addr for e in self.data]

	def comments(self):
		return [e.label for e in self.data]

	def entry(self,idx):
		for e in self.data:
			if idx == e.idx: return e

	def coinaddr(self,idx):
		for e in self.data:
			if idx == e.idx: return e.addr

	def comment(self,idx):
		for e in self.data:
			if idx == e.idx: return e.label

	def set_comment(self,idx,comment):
		for e in self.data:
			if idx == e.idx:
				e.label = comment

	def make_reverse_dict(self,coinaddrs):
		d,b = MMGenDict(),coinaddrs
		for e in self.data:
			try:
				d[b[b.index(e.addr)]] = MMGenID('{}:{}'.format(self.al_id,e.idx)),e.label
			except: pass
		return d

	def remove_dup_keys(self,cmplist):
		assert self.has_keys
		pop_list = []
		for n,d in enumerate(self.data):
			for e in cmplist.data:
				if e.sec.wif == d.sec.wif:
					pop_list.append(n)
		for n in reversed(pop_list): self.data.pop(n)
		if pop_list:
			vmsg(self.msgs['removed_dup_keys'].format(len(pop_list),suf(removed)))

	def add_wifs(self,key_list):
		if not key_list: return
		for d in self.data:
			for e in key_list.data:
				if e.addr and e.sec and e.addr == d.addr:
					d.sec = e.sec

	def list_missing(self,key):
		return [d.addr for d in self.data if not getattr(d,key)]

	def generate_addrs_from_keys(self):
		# assume that the first listed mmtype is valid for flat key list
		t = MMGenAddrType(g.proto.mmtypes[0])
		kg = KeyGenerator(t.pubkey_type)
		ag = AddrGenerator(t.gen_method)
		d = self.data
		for n,e in enumerate(d,1):
			qmsg_r('\rGenerating addresses from keylist: {}/{}'.format(n,len(d)))
			e.addr = ag.to_addr(kg.to_pubhex(e.sec))
			if g.debug_addrlist:
				Msg('generate_addrs_from_keys():\n{}'.format(e.pfmt()))
		qmsg('\rGenerated addresses from keylist: {}/{} '.format(n,len(d)))

	def make_label(self):
		bc,mt = g.proto.base_coin,self.al_id.mmtype
		l_coin = [] if bc == 'BTC' else [g.coin] if bc == 'ETH' else [bc]
		l_type = [] if mt == 'E' or (mt == 'L' and not g.proto.is_testnet()) else [mt.name.upper()]
		l_tn   = [] if not g.proto.is_testnet() else ['TESTNET']
		lbl_p2 = ':'.join(l_coin+l_type+l_tn)
		return self.al_id.sid + ('',' ')[bool(lbl_p2)] + lbl_p2

	def format(self,add_comments=False):

		out = [self.msgs['file_header']+'\n']
		if self.chksum:
			out.append('# {} data checksum for {}: {}'.format(
						capfirst(self.data_desc),self.id_str,self.chksum))
			out.append('# Record this value to a secure location.\n')

		lbl = self.make_label()
		dmsg_sc('lbl',lbl[9:])
		out.append('{} {{'.format(lbl))

		fs = '  {:<%s}  {:<34}{}' % len(str(self.data[-1].idx))
		for e in self.data:
			c = ' '+e.label if add_comments and e.label else ''
			if type(self) == KeyList:
				out.append(fs.format(e.idx,'{}: {}'.format(self.al_id.mmtype.wif_label,e.sec.wif),c))
			elif type(self) == PasswordList:
				out.append(fs.format(e.idx,e.passwd,c))
			else: # First line with idx
				out.append(fs.format(e.idx,e.addr,c))
				if self.has_keys:
					if opt.b16:
						out.append(fs.format('', 'orig_hex: '+e.sec.orig_hex,c))
					out.append(fs.format('','{}: {}'.format(self.al_id.mmtype.wif_label,e.sec.wif),c))
					for k in ('viewkey','wallet_passwd'):
						v = getattr(e,k)
						if v: out.append(fs.format('','{}: {}'.format(k,v),c))

		out.append('}')
		self.fmt_data = '\n'.join([l.rstrip() for l in out]) + '\n'

	def get_line(self,lines):
		ret = lines.pop(0).split(None,2)
		self.line_ctr += 1
		if ret[0] == 'orig_hex:': # hacky
			ret = lines.pop(0).split(None,2)
			self.line_ctr += 1
		return ret if len(ret) == 3 else ret + ['']

	def parse_file_body(self,lines):

		ret = AddrListList()
		le = self.entry_type
		iifs = "{!r}: invalid identifier [expected '{}:']"

		while lines:
			idx,addr,lbl = self.get_line(lines)

			assert is_mmgen_idx(idx),'invalid address index {!r}'.format(idx)
			self.check_format(addr)

			a = le(**{ 'idx':int(idx), self.main_attr:addr, 'label':lbl })

			if self.has_keys: # order: wif,(orig_hex),viewkey,wallet_passwd
				d = self.get_line(lines)
				assert d[0] == self.al_id.mmtype.wif_label+':',iifs.format(d[0],self.al_id.mmtype.wif_label)
				a.sec = PrivKey(wif=d[1])
				for k,dtype in (('viewkey',ViewKey),('wallet_passwd',WalletPassword)):
					if k in self.al_id.mmtype.extra_attrs:
						d = self.get_line(lines)
						assert d[0] == k+':',iifs.format(d[0],k)
						setattr(a,k,dtype(d[1]))

			ret.append(a)

		if self.has_keys:
			if (hasattr(opt,'yes') and opt.yes) or keypress_confirm('Check key-to-address validity?'):
				kg = KeyGenerator(self.al_id.mmtype)
				ag = AddrGenerator(self.al_id.mmtype)
				llen = len(ret)
				for n,e in enumerate(ret):
					qmsg_r('\rVerifying keys {}/{}'.format(n+1,llen))
					assert e.addr == ag.to_addr(kg.to_pubhex(e.sec)),(
						"Key doesn't match address!\n  {}\n  {}".format(e.sec.wif,e.addr))
				qmsg(' - done')

		return ret

	def parse_file(self,fn,buf=[],exit_on_error=True):

		def parse_addrfile_label(lbl): # we must maintain backwards compat, so parse is tricky
			al_coin,al_mmtype = None,None
			tn = lbl[-8:] == ':TESTNET'
			if tn:
				assert g.proto.is_testnet(),'{} file is testnet but protocol is mainnet!'.format(self.data_desc)
				lbl = lbl[:-8]
			else:
				assert not g.proto.is_testnet(),'{} file is mainnet but protocol is testnet!'.format(self.data_desc)
			lbl = lbl.split(':',1)
			if len(lbl) == 2:
				al_coin,al_mmtype = lbl[0],lbl[1].lower()
			else:
				if lbl[0].lower() in MMGenAddrType.get_names():
					al_mmtype = lbl[0].lower()
				else:
					al_coin = lbl[0]

			# this block fails if al_mmtype is invalid for g.coin
			if not al_mmtype:
				mmtype = MMGenAddrType('E' if al_coin in ('ETH','ETC') else 'L',on_fail='raise')
			else:
				mmtype = MMGenAddrType(al_mmtype,on_fail='raise')

			from .protocol import init_proto
			base_coin = init_proto(al_coin or 'BTC',testnet=False).base_coin
			return base_coin,mmtype,tn

		def check_coin_mismatch(base_coin): # die if addrfile coin doesn't match g.coin
			m = '{} address file format, but base coin is {}!'
			assert base_coin == g.proto.base_coin, m.format(base_coin,g.proto.base_coin)

		lines = get_lines_from_file(fn,self.data_desc+' data',trim_comments=True)

		try:
			assert len(lines) >= 3,  'Too few lines in address file ({})'.format(len(lines))
			ls = lines[0].split()
			assert 1 < len(ls) < 5,  "Invalid first line for {} file: '{}'".format(self.gen_desc,lines[0])
			assert ls.pop() == '{',  "'{}': invalid first line".format(ls)
			assert lines[-1] == '}', "'{}': invalid last line".format(lines[-1])
			sid = ls.pop(0)
			assert is_mmgen_seed_id(sid),"'{}': invalid Seed ID".format(ls[0])

			if type(self) == PasswordList and len(ls) == 2:
				ss = ls.pop().split(':')
				assert len(ss) == 2,"'{}': invalid password length specifier (must contain colon)".format(ls[2])
				self.set_pw_fmt(ss[0])
				self.set_pw_len(ss[1])
				self.pw_id_str = MMGenPWIDString(ls.pop())
				base_coin,mmtype = None,MMGenPasswordType('P')
				testnet = False
			elif len(ls) == 1:
				base_coin,mmtype,testnet = parse_addrfile_label(ls[0])
				check_coin_mismatch(base_coin)
			elif len(ls) == 0:
				base_coin,mmtype = 'BTC',MMGenAddrType('L')
				testnet = False
				check_coin_mismatch(base_coin)
			else:
				raise ValueError("'{}': Invalid first line for {} file '{}'".format(lines[0],self.gen_desc,fn))

			self.base_coin = base_coin
			self.is_testnet = testnet
			self.al_id = AddrListID(SeedID(sid=sid),mmtype)

			data = self.parse_file_body(lines[1:-1])
			assert isinstance(data,list),'Invalid file body data'
		except Exception as e:
			lcs = ', content line {}'.format(self.line_ctr) if self.line_ctr else ''
			m = 'Invalid data in {} list file {!r}{} ({})'.format(self.data_desc,self.infile,lcs,e.args[0])
			if exit_on_error: die(3,m)
			msg(msg)
			return False

		return data

class KeyAddrList(AddrList):
	data_desc = 'key-address'
	file_desc = 'secret keys'
	gen_desc = 'key/address pair'
	gen_desc_pl = 's'
	gen_addrs = True
	gen_keys = True
	has_keys = True
	ext      = 'akeys'
	chksum_rec_f = lambda foo,e: (str(e.idx), e.addr, e.sec.wif)

class KeyList(AddrList):
	msgs = {
	'file_header': """
# {pnm} key file
#
# This file is editable.
# Everything following a hash symbol '#' is a comment and ignored by {pnm}.
""".strip().format(pnm=pnm)
	}
	data_desc = 'key'
	file_desc = 'secret keys'
	gen_desc = 'key'
	gen_desc_pl = 's'
	gen_addrs = False
	gen_keys = True
	has_keys = True
	ext      = 'keys'
	chksum_rec_f = lambda foo,e: (str(e.idx), e.addr, e.sec.wif)

def is_bip39_str(s):
	from .bip39 import bip39
	return bool(bip39.tohex(s.split(),wl_id='bip39'))

def is_xmrseed(s):
	return bool(baseconv.tobytes(s.split(),wl_id='xmrseed'))

from collections import namedtuple
class PasswordList(AddrList):
	msgs = {
	'file_header': """
# {pnm} password file
#
# This file is editable.
# Everything following a hash symbol '#' is a comment and ignored by {pnm}.
# A text label of {n} screen cells or less may be added to the right of each
# password.  The label may contain any printable ASCII symbol.
#
""".strip().format(n=TwComment.max_screen_width,pnm=pnm),
	'file_header_mn': """
# {pnm} {{}} password file
#
# This file is editable.
# Everything following a hash symbol '#' is a comment and ignored by {pnm}.
#
""".strip().format(pnm=pnm),
	'record_chksum': """
Record this checksum: it will be used to verify the password file in the future
""".strip()
	}
	entry_type  = PasswordListEntry
	main_attr   = 'passwd'
	data_desc   = 'password'
	file_desc   = 'passwords'
	gen_desc    = 'password'
	gen_desc_pl = 's'
	gen_addrs   = False
	gen_keys    = False
	gen_passwds = True
	has_keys    = False
	ext         = 'pws'
	pw_len      = None
	dfl_pw_fmt  = 'b58'
	pwinfo      = namedtuple('passwd_info',['min_len','max_len','dfl_len','valid_lens','desc','chk_func'])
	pw_info     = {
		'b32':   pwinfo(10, 42 ,24, None,       'base32 password',       is_b32_str),   # 32**24 < 2**128
		'b58':   pwinfo(8,  36 ,20, None,       'base58 password',       is_b58_str),   # 58**20 < 2**128
		'bip39': pwinfo(12, 24 ,24, [12,18,24], 'BIP39 mnemonic',        is_bip39_str),
		'xmrseed': pwinfo(25, 25, 25, [25],     'Monero new-style mnemonic', is_xmrseed),
		'hex':   pwinfo(32, 64 ,64, [32,48,64], 'hexadecimal password',  is_hex_str),
	}
	chksum_rec_f = lambda foo,e: (str(e.idx), e.passwd)

	feature_warn_fs = 'WARNING: {!r} is a potentially dangerous feature.  Use at your own risk!'
	hex2bip39 = False

	def __init__(   self,infile=None,seed=None,
					pw_idxs=None,pw_id_str=None,pw_len=None,pw_fmt=None,
					chk_params_only=False):

		self.update_msgs()

		if infile:
			self.infile = infile
			self.data = self.parse_file(infile) # sets self.pw_id_str,self.pw_fmt,self.pw_len
		else:
			if not chk_params_only:
				for k in (seed,pw_idxs):
					assert k
			self.pw_id_str = MMGenPWIDString(pw_id_str)
			self.set_pw_fmt(pw_fmt)
			self.set_pw_len(pw_len)
			if chk_params_only:
				return
			if self.hex2bip39:
				ymsg(self.feature_warn_fs.format(pw_fmt))
			self.set_pw_len_vs_seed_len(pw_len,seed)
			self.al_id = AddrListID(seed.sid,MMGenPasswordType('P'))
			self.data = self.generate(seed,pw_idxs)

		if self.pw_fmt in ('bip39','xmrseed'):
			self.msgs['file_header'] = self.msgs['file_header_mn'].format(self.pw_fmt.upper())

		self.num_addrs = len(self.data)
		self.fmt_data = ''
		self.chksum = AddrListChksum(self)

		fs = '{}-{}-{}-{}[{{}}]'.format(self.al_id.sid,self.pw_id_str,self.pw_fmt_disp,self.pw_len)
		self.id_str = AddrListIDStr(self,fs)
		qmsg('Checksum for {} data {}: {}'.format(self.data_desc,self.id_str.hl(),self.chksum.hl()))
		qmsg(self.msgs[('record_chksum','check_chksum')[bool(infile)]])

	def set_pw_fmt(self,pw_fmt):
		if pw_fmt == 'hex2bip39':
			self.hex2bip39 = True
			self.pw_fmt = 'bip39'
			self.pw_fmt_disp = 'hex2bip39'
		else:
			self.pw_fmt = pw_fmt
			self.pw_fmt_disp = pw_fmt
		if self.pw_fmt not in self.pw_info:
			m = '{!r}: invalid password format.  Valid formats: {}'
			raise InvalidPasswdFormat(m.format(self.pw_fmt,', '.join(sorted(self.pw_info))))

	def chk_pw_len(self,passwd=None):
		if passwd is None:
			assert self.pw_len,'either passwd or pw_len must be set'
			pw_len = self.pw_len
			fs = '{l}: invalid user-requested length for {b} ({c}{m})'
		else:
			pw_len = len(passwd)
			fs = '{pw}: {b} has invalid length {l} ({c}{m} characters)'
		d = self.pw_info[self.pw_fmt]
		if d.valid_lens:
			if pw_len not in d.valid_lens:
				die(2,fs.format(l=pw_len,b=d.desc,c='not one of ',m=d.valid_lens,pw=passwd))
		elif pw_len > d.max_len:
			die(2,fs.format(l=pw_len,b=d.desc,c='>',m=d.max_len,pw=passwd))
		elif pw_len < d.min_len:
			die(2,fs.format(l=pw_len,b=d.desc,c='<',m=d.min_len,pw=passwd))

	def set_pw_len(self,pw_len):
		d = self.pw_info[self.pw_fmt]

		if pw_len is None:
			self.pw_len = d.dfl_len
			return

		if not is_int(pw_len):
			die(2,"'{}': invalid user-requested password length (not an integer)".format(pw_len,d.desc))
		self.pw_len = int(pw_len)
		self.chk_pw_len()

	def set_pw_len_vs_seed_len(self,pw_len,seed):
		pf = self.pw_fmt
		if pf == 'hex':
			pw_bytes = self.pw_len // 2
			good_pw_len = seed.byte_len * 2
		elif pf == 'bip39':
			from .bip39 import bip39
			pw_bytes = bip39.nwords2seedlen(self.pw_len,in_bytes=True)
			good_pw_len = bip39.seedlen2nwords(seed.byte_len,in_bytes=True)
		elif pf == 'xmrseed':
			pw_bytes = baseconv.seedlen_map_rev['xmrseed'][self.pw_len]
			try:
				good_pw_len = baseconv.seedlen_map['xmrseed'][seed.byte_len]
			except:
				die(1,'{}: unsupported seed length for Monero new-style mnemonic'.format(seed.byte_len*8))
		elif pf in ('b32','b58'):
			pw_int = (32 if pf == 'b32' else 58) ** self.pw_len
			pw_bytes = pw_int.bit_length() // 8
			good_pw_len = len(baseconv.frombytes(b'\xff'*seed.byte_len,wl_id=pf))
		else:
			raise NotImplementedError('{!r}: unknown password format'.format(pf))

		if pw_bytes > seed.byte_len:
			m1 = 'Cannot generate passwords with more entropy than underlying seed! ({} bits)'
			m2  = ( 'Re-run the command with --passwd-len={}' if pf in ('bip39','hex') else
					'Re-run the command, specifying a password length of {} or less' )
			die(1,(m1+'\n'+m2).format(len(seed.data) * 8,good_pw_len))

		if pf in ('bip39','hex') and pw_bytes < seed.byte_len:
			m1 = 'WARNING: requested {} length has less entropy than underlying seed!'
			m2 = 'Is this what you want?'
			if not keypress_confirm((m1+'\n'+m2).format(self.pw_info[pf].desc),default_yes=True):
				die(1,'Exiting at user request')

	def make_passwd(self,hex_sec):
		assert self.pw_fmt in self.pw_info
		if self.pw_fmt == 'hex':
			# take most significant part
			return hex_sec[:self.pw_len]
		elif self.pw_fmt == 'bip39':
			from .bip39 import bip39
			pw_len_hex = bip39.nwords2seedlen(self.pw_len,in_hex=True)
			# take most significant part
			return ' '.join(bip39.fromhex(hex_sec[:pw_len_hex],wl_id='bip39'))
		elif self.pw_fmt == 'xmrseed':
			pw_len_hex = baseconv.seedlen_map_rev['xmrseed'][self.pw_len] * 2
			# take most significant part
			bytes_trunc = bytes.fromhex(hex_sec[:pw_len_hex])
			from .protocol import CoinProtocol
			bytes_preproc = CoinProtocol.Monero().preprocess_key(bytes_trunc,None)
			return ' '.join(baseconv.frombytes(bytes_preproc,wl_id='xmrseed'))
		else:
			# take least significant part
			return baseconv.fromhex(hex_sec,self.pw_fmt,pad=self.pw_len,tostr=True)[-self.pw_len:]

	def check_format(self,pw):
		if not self.pw_info[self.pw_fmt].chk_func(pw):
			raise ValueError('Password is not valid {} data'.format(self.pw_info[self.pw_fmt].desc))
		pwlen = len(pw.split()) if self.pw_fmt in ('bip39','xmrseed') else len(pw)
		if pwlen != self.pw_len:
			raise ValueError('Password has incorrect length ({} != {})'.format(pwlen,self.pw_len))
		return True

	def scramble_seed(self,seed):
		# Changing either pw_fmt or pw_len will cause a different, unrelated
		# set of passwords to be generated: this is what we want.
		# NB: In original implementation, pw_id_str was 'baseN', not 'bN'
		scramble_key = '{}:{}:{}'.format(self.pw_fmt,self.pw_len,self.pw_id_str)

		if self.hex2bip39:
			from .bip39 import bip39
			pwlen = bip39.nwords2seedlen(self.pw_len,in_hex=True)
			scramble_key = '{}:{}:{}'.format('hex',pwlen,self.pw_id_str)

		from .crypto import scramble_seed
		dmsg_sc('str',scramble_key)
		return scramble_seed(seed,scramble_key.encode())

	def get_line(self,lines):
		self.line_ctr += 1
		if self.pw_fmt in ('bip39','xmrseed'):
			ret = lines.pop(0).split(None,self.pw_len+1)
			if len(ret) > self.pw_len+1:
				m1 = 'extraneous text {!r} found after password'.format(ret[self.pw_len+1])
				m2 = '[bare comments not allowed in BIP39 password files]'
				m = m1+' '+m2
			elif len(ret) < self.pw_len+1:
				m = 'invalid password length {}'.format(len(ret)-1)
			else:
				return (ret[0],' '.join(ret[1:self.pw_len+1]),'')
			raise ValueError(m)
		else:
			ret = lines.pop(0).split(None,2)
			return ret if len(ret) == 3 else ret + ['']

	def make_label(self):
		return '{} {} {}:{}'.format(self.al_id.sid,self.pw_id_str,self.pw_fmt_disp,self.pw_len)

class AddrData(MMGenObject):
	msgs = {
	'too_many_acct_addresses': """
ERROR: More than one address found for account: '{{}}'.
Your 'wallet.dat' file appears to have been altered by a non-{pnm} program.
Please restore your tracking wallet from a backup or create a new one and
re-import your addresses.
""".strip().format(pnm=pnm)
	}

	def __new__(cls,*args,**kwargs):
		return MMGenObject.__new__(altcoin_subclass(cls,'tw','AddrData'))

	def __init__(self,*args,**kwargs):
		self.al_ids = {}

	def seed_ids(self):
		return list(self.al_ids.keys())

	def addrlist(self,al_id):
		# TODO: Validate al_id
		if al_id in self.al_ids:
			return self.al_ids[al_id]

	def mmaddr2coinaddr(self,mmaddr):
		al_id,idx = MMGenID(mmaddr).rsplit(':',1)
		coinaddr = ''
		if al_id in self.al_ids:
			coinaddr = self.addrlist(al_id).coinaddr(int(idx))
		return coinaddr or None

	def coinaddr2mmaddr(self,coinaddr):
		d = self.make_reverse_dict([coinaddr])
		return (list(d.values())[0][0]) if d else None

	@classmethod
	async def get_tw_data(cls,wallet=None):
		vmsg('Getting address data from tracking wallet')
		if 'label_api' in g.rpc.caps:
			accts = await g.rpc.call('listlabels')
			ll = await g.rpc.batch_call('getaddressesbylabel',[(k,) for k in accts])
			alists = [list(a.keys()) for a in ll]
		else:
			accts = await g.rpc.call('listaccounts',0,True)
			alists = await g.rpc.batch_call('getaddressesbyaccount',[(k,) for k in accts])
		return list(zip(accts,alists))

	async def add_tw_data(self,wallet):

		twd = await type(self).get_tw_data(wallet)
		out,i = {},0
		for acct,addr_array in twd:
			l = TwLabel(acct,on_fail='silent')
			if l and l.mmid.type == 'mmgen':
				obj = l.mmid.obj
				if len(addr_array) != 1:
					die(2,self.msgs['too_many_acct_addresses'].format(acct))
				al_id = AddrListID(SeedID(sid=obj.sid),MMGenAddrType(obj.mmtype))
				if al_id not in out:
					out[al_id] = []
				out[al_id].append(AddrListEntry(idx=obj.idx,addr=addr_array[0],label=l.comment))
				i += 1

		vmsg('{n} {pnm} addresses found, {m} accounts total'.format(n=i,pnm=pnm,m=len(twd)))
		for al_id in out:
			self.add(AddrList(al_id=al_id,adata=AddrListList(sorted(out[al_id],key=lambda a: a.idx))))

	def add(self,addrlist):
		if type(addrlist) == AddrList:
			self.al_ids[addrlist.al_id] = addrlist
			return True
		else:
			raise TypeError('Error: object {!r} is not of type AddrList'.format(addrlist))

	def make_reverse_dict(self,coinaddrs):
		d = MMGenDict()
		for al_id in self.al_ids:
			d.update(self.al_ids[al_id].make_reverse_dict(coinaddrs))
		return d

class TwAddrData(AddrData,metaclass=aInitMeta):

	def __new__(cls,*args,**kwargs):
		return MMGenObject.__new__(altcoin_subclass(cls,'tw','TwAddrData'))

	def __init__(self,*args,**kwargs):
		pass

	async def __ainit__(self,wallet=None):
		self.al_ids = {}
		await self.add_tw_data(wallet)
