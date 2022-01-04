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
addr.py:  Address generation/display routines for the MMGen suite
"""

from hashlib import sha256,sha512
from .common import *
from .obj import *
from .baseconv import *
from .protocol import init_proto,hash160

pnm = g.proj_name

def dmsg_sc(desc,data):
	if g.debug_addrlist:
		Msg(f'sc_debug_{desc}: {data}')

class AddrGenerator(MMGenObject):
	def __new__(cls,proto,addr_type):

		if type(addr_type) == str:
			addr_type = MMGenAddrType(proto=proto,id_str=addr_type)
		elif type(addr_type) == MMGenAddrType:
			assert addr_type in proto.mmtypes, f'{addr_type}: invalid address type for coin {proto.coin}'
		else:
			raise TypeError(f'{type(addr_type)}: incorrect argument type for {cls.__name__}()')

		addr_generators = {
			'p2pkh':    AddrGeneratorP2PKH,
			'segwit':   AddrGeneratorSegwit,
			'bech32':   AddrGeneratorBech32,
			'ethereum': AddrGeneratorEthereum,
			'zcash_z':  AddrGeneratorZcashZ,
			'monero':   AddrGeneratorMonero,
		}
		me = super(cls,cls).__new__(addr_generators[addr_type.gen_method])
		me.desc = type(me).__name__
		me.proto = proto
		me.addr_type = addr_type
		me.pubkey_type = addr_type.pubkey_type
		return me

class AddrGeneratorP2PKH(AddrGenerator):
	def to_addr(self,pubhex):
		assert pubhex.privkey.pubkey_type == self.pubkey_type
		return CoinAddr(self.proto,self.proto.pubhash2addr(hash160(pubhex),p2sh=False))

	def to_segwit_redeem_script(self,pubhex):
		raise NotImplementedError('Segwit redeem script not supported by this address type')

class AddrGeneratorSegwit(AddrGenerator):
	def to_addr(self,pubhex):
		assert pubhex.privkey.pubkey_type == self.pubkey_type
		assert pubhex.compressed,'Uncompressed public keys incompatible with Segwit'
		return CoinAddr(self.proto,self.proto.pubhex2segwitaddr(pubhex))

	def to_segwit_redeem_script(self,pubhex):
		assert pubhex.compressed,'Uncompressed public keys incompatible with Segwit'
		return HexStr(self.proto.pubhex2redeem_script(pubhex))

class AddrGeneratorBech32(AddrGenerator):
	def to_addr(self,pubhex):
		assert pubhex.privkey.pubkey_type == self.pubkey_type
		assert pubhex.compressed,'Uncompressed public keys incompatible with Segwit'
		return CoinAddr(self.proto,self.proto.pubhash2bech32addr(hash160(pubhex)))

	def to_segwit_redeem_script(self,pubhex):
		raise NotImplementedError('Segwit redeem script not supported by this address type')

class AddrGeneratorEthereum(AddrGenerator):

	def __init__(self,proto,addr_type):

		try:
			assert not g.use_internal_keccak_module
			from sha3 import keccak_256
		except:
			from .keccak import keccak_256
		self.keccak_256 = keccak_256

		from .protocol import hash256
		self.hash256 = hash256

	def to_addr(self,pubhex):
		assert pubhex.privkey.pubkey_type == self.pubkey_type
		return CoinAddr(self.proto,self.keccak_256(bytes.fromhex(pubhex[2:])).hexdigest()[24:])

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
		assert pubhex.privkey.pubkey_type == self.pubkey_type
		key = bytes.fromhex(pubhex)
		assert len(key) == 32, f'{len(key)}: incorrect privkey length'
		from nacl.bindings import crypto_scalarmult_base
		p2 = crypto_scalarmult_base(self.zhash256(key,1))
		from .protocol import _b58chk_encode
		ver_bytes = self.proto.addr_fmt_to_ver_bytes('zcash_z')
		ret = _b58chk_encode(ver_bytes + self.zhash256(key,0) + p2)
		return CoinAddr(self.proto,ret)

	def to_viewkey(self,pubhex): # pubhex is really privhex
		key = bytes.fromhex(pubhex)
		assert len(key) == 32, f'{len(key)}: incorrect privkey length'
		vk = bytearray(self.zhash256(key,0)+self.zhash256(key,1))
		vk[32] &= 0xf8
		vk[63] &= 0x7f
		vk[63] |= 0x40
		from .protocol import _b58chk_encode
		ver_bytes = self.proto.addr_fmt_to_ver_bytes('viewkey')
		ret = _b58chk_encode(ver_bytes + vk)
		return ZcashViewKey(self.proto,ret)

	def to_segwit_redeem_script(self,pubhex):
		raise NotImplementedError('Zcash z-addresses incompatible with Segwit')

class AddrGeneratorMonero(AddrGenerator):

	def __init__(self,proto,addr_type):

		try:
			assert not g.use_internal_keccak_module
			from sha3 import keccak_256
		except:
			from .keccak import keccak_256
		self.keccak_256 = keccak_256

		from .protocol import hash256
		self.hash256 = hash256

		if getattr(opt,'use_old_ed25519',False):
			from .ed25519 import edwards,encodepoint,B,scalarmult
		else:
			from .ed25519ll_djbec import scalarmult
			from .ed25519 import edwards,encodepoint,B

		self.edwards     = edwards
		self.encodepoint = encodepoint
		self.scalarmult  = scalarmult
		self.B           = B

	def b58enc(self,addr_bytes):
		enc = baseconv.frombytes
		l = len(addr_bytes)
		a = ''.join([enc(addr_bytes[i*8:i*8+8],'b58',pad=11,tostr=True) for i in range(l//8)])
		b = enc(addr_bytes[l-l%8:],'b58',pad=7,tostr=True)
		return a + b

	def to_addr(self,sk_hex): # sk_hex instead of pubhex
		assert sk_hex.privkey.pubkey_type == self.pubkey_type

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
		addr_p1 = self.proto.addr_fmt_to_ver_bytes('monero') + pk_str + pvk_str

		return CoinAddr(
			proto = self.proto,
			addr = self.b58enc(addr_p1 + self.keccak_256(addr_p1).digest()[:4]) )

	def to_wallet_passwd(self,sk_hex):
		return WalletPassword(self.hash256(sk_hex)[:32])

	def to_viewkey(self,sk_hex):
		assert len(sk_hex) == 64, f'{len(sk_hex)}: incorrect privkey length'
		return MoneroViewKey(
			self.proto.preprocess_key(self.keccak_256(bytes.fromhex(sk_hex)).digest(),None).hex() )

	def to_segwit_redeem_script(self,sk_hex):
		raise NotImplementedError('Monero addresses incompatible with Segwit')

class KeyGenerator(MMGenObject):

	def __new__(cls,proto,addr_type,generator=None,silent=False):
		if type(addr_type) == str: # allow override w/o check
			pubkey_type = addr_type
		elif type(addr_type) == MMGenAddrType:
			assert addr_type in proto.mmtypes, f'{address}: invalid address type for coin {proto.coin}'
			pubkey_type = addr_type.pubkey_type
		else:
			raise TypeError(f'{type(addr_type)}: incorrect argument type for {cls.__name__}()')
		if pubkey_type == 'std':
			if cls.test_for_secp256k1(silent=silent) and generator != 1:
				if not opt.key_generator or opt.key_generator == 2 or generator == 2:
					me = super(cls,cls).__new__(KeyGeneratorSecp256k1)
			else:
				qmsg('Using (slow) native Python ECDSA library for address generation')
				me = super(cls,cls).__new__(KeyGeneratorPython)
		elif pubkey_type in ('zcash_z','monero'):
			me = super(cls,cls).__new__(KeyGeneratorDummy)
			me.desc = 'mmgen-'+pubkey_type
		else:
			raise ValueError(f'{pubkey_type}: invalid pubkey_type argument')

		me.proto = proto
		return me

	@classmethod
	def test_for_secp256k1(self,silent=False):
		try:
			from .secp256k1 import priv2pub
			m = 'Unable to execute priv2pub() from secp256k1 extension module'
			assert priv2pub(bytes.fromhex('deadbeef'*8),1),m
			return True
		except Exception as e:
			if not silent:
				ymsg(str(e))
			return False

class KeyGeneratorPython(KeyGenerator):

	desc = 'mmgen-python-ecdsa'

	# devdoc/guide_wallets.md:
	# Uncompressed public keys start with 0x04; compressed public keys begin with 0x03 or
	# 0x02 depending on whether they're greater or less than the midpoint of the curve.
	def privnum2pubhex(self,numpriv,compressed=False):
		import ecdsa
		pko = ecdsa.SigningKey.from_secret_exponent(numpriv,curve=ecdsa.SECP256k1)
		# pubkey = x (32 bytes) + y (32 bytes) (unsigned big-endian)
		pubkey = pko.get_verifying_key().to_string().hex()
		if compressed: # discard Y coord, replace with appropriate version byte
			# even y: <0, odd y: >0 -- https://bitcointalk.org/index.php?topic=129652.0
			return ('03','02')[pubkey[-1] in '02468ace'] + pubkey[:64]
		else:
			return '04' + pubkey

	def to_pubhex(self,privhex):
		assert type(privhex) == PrivKey
		return PubKey(
			s       = self.privnum2pubhex(int(privhex,16),compressed=privhex.compressed),
			privkey = privhex )

class KeyGeneratorSecp256k1(KeyGenerator):
	desc = 'mmgen-secp256k1'
	def to_pubhex(self,privhex):
		assert type(privhex) == PrivKey
		from .secp256k1 import priv2pub
		return PubKey(
			s       = priv2pub(bytes.fromhex(privhex),int(privhex.compressed)).hex(),
			privkey = privhex )

class KeyGeneratorDummy(KeyGenerator):
	desc = 'mmgen-dummy'
	def to_pubhex(self,privhex):
		assert type(privhex) == PrivKey
		return PubKey(
			s       = privhex,
			privkey = privhex )

class AddrListEntryBase(MMGenListItem):
	invalid_attrs = {'proto'}
	def __init__(self,proto,**kwargs):
		self.__dict__['proto'] = proto
		MMGenListItem.__init__(self,**kwargs)

class AddrListEntry(AddrListEntryBase):
	addr          = ListItemAttr('CoinAddr',include_proto=True)
	idx           = ListItemAttr('AddrIdx') # not present in flat addrlists
	label         = ListItemAttr('TwComment',reassign_ok=True)
	sec           = ListItemAttr('PrivKey',include_proto=True)
	viewkey       = ListItemAttr('ViewKey',include_proto=True)
	wallet_passwd = ListItemAttr('WalletPassword')

class PasswordListEntry(AddrListEntryBase):
	passwd = ListItemAttr(str,typeconv=False) # TODO: create Password type
	idx    = ImmutableAttr('AddrIdx')
	label  = ListItemAttr('TwComment',reassign_ok=True)
	sec    = ListItemAttr('PrivKey',include_proto=True)

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
			bc = (addrlist.proto.base_coin,addrlist.proto.coin)[addrlist.proto.base_coin=='ETH']
			mt = addrlist.al_id.mmtype
			ret = '{}{}{}[{}]'.format(
				addrlist.al_id.sid,
				('-'+bc,'')[bc == 'BTC'],
				('-'+mt,'')[mt in ('L','E')],
				s )

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
		'removed_dup_keys': f"""
Removed {{}} duplicate WIF key{{}} from keylist (also in {pnm} key-address file
""".strip(),
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
			skip_chksum = False ):

		self.skip_ka_check = skip_key_address_validity_check
		self.update_msgs()
		mmtype = mmtype or proto.dfl_mmtype
		assert mmtype in MMGenAddrType.mmtypes, f'{mmtype}: mmtype not in {MMGenAddrType.mmtypes!r}'

		from .protocol import CoinProtocol
		self.bitcoin_addrtypes = tuple(
			MMGenAddrType(CoinProtocol.Bitcoin,key).name for key in CoinProtocol.Bitcoin.mmtypes)

		self.proto = proto

		do_chksum = False
		if seed and addr_idxs:   # data from seed + idxs
			self.al_id,src = AddrListID(seed.sid,mmtype),'gen'
			adata = self.generate(seed,addr_idxs)
			do_chksum = True
		elif addrfile:           # data from MMGen address file
			self.infile = addrfile
			adata = self.parse_file(addrfile) # sets self.al_id
			do_chksum = True
		elif al_id and adata:    # data from tracking wallet
			self.al_id = al_id
		elif addrlist:           # data from flat address list
			self.al_id = None
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

		if self.al_id == None: return

		self.id_str = AddrListIDStr(self)
		if type(self) == KeyList: return

		if do_chksum and not skip_chksum:
			self.chksum = AddrListChksum(self)
			qmsg(
				f'Checksum for {self.data_desc} data {self.id_str.hl()}: {self.chksum.hl()}\n' +
				self.msgs[('check_chksum','record_chksum')[src=='gen']] )

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
			kg = KeyGenerator(self.proto,self.al_id.mmtype)
			ag = AddrGenerator(self.proto,self.al_id.mmtype)

		t_addrs,num,pos,out = len(addrnums),0,0,AddrListData()
		le = self.entry_type

		while pos != t_addrs:
			seed = sha512(seed).digest()
			num += 1 # round

			if num != addrnums[pos]: continue

			pos += 1

			if not g.debug:
				qmsg_r(f'\rGenerating {self.gen_desc} #{num} ({pos} of {t_addrs})')

			e = le(proto=self.proto,idx=num)

			# Secret key is double sha256 of seed hash round /num/
			e.sec = PrivKey(
				self.proto,
				sha256(sha256(seed).digest()).digest(),
				compressed  = compressed,
				pubkey_type = pubkey_type )

			if self.gen_addrs:
				pubhex = kg.to_pubhex(e.sec)
				e.addr = ag.to_addr(pubhex)
				if gen_viewkey:
					e.viewkey = ag.to_viewkey(pubhex)
				if gen_wallet_passwd:
					e.wallet_passwd = ag.to_wallet_passwd(e.sec)

			if type(self) == PasswordList:
				e.passwd = str(self.make_passwd(e.sec)) # TODO - own type
				dmsg(f'Key {pos:>03}: {e.passwd}')

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

	def encrypt(self,desc='new key list'):
		from .crypto import mmgen_encrypt
		self.fmt_data = mmgen_encrypt(self.fmt_data.encode(),desc,'')
		self.ext += '.'+g.mmenc_ext

	def write_to_file(self,ask_tty=True,ask_write_default_yes=False,binary=False,desc=None):
		tn = ('.' + self.proto.network) if self.proto.testnet else ''
		fn = '{}{x}{}.{}'.format(self.id_str,tn,self.ext,x='-α' if g.debug_utf8 else '')
		ask_tty = self.has_keys and not opt.quiet
		write_data_to_file(fn,self.fmt_data,desc or self.file_desc,ask_tty=ask_tty,binary=binary)

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
			kg = KeyGenerator(self.proto,at.pubkey_type)
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

	def make_label(self):
		bc,mt = self.proto.base_coin,self.al_id.mmtype
		l_coin = [] if bc == 'BTC' else [self.proto.coin] if bc == 'ETH' else [bc]
		l_type = [] if mt == 'E' or (mt == 'L' and not self.proto.testnet) else [mt.name.upper()]
		l_tn   = [] if not self.proto.testnet else [self.proto.network.upper()]
		lbl_p2 = ':'.join(l_coin+l_type+l_tn)
		return self.al_id.sid + ('',' ')[bool(lbl_p2)] + lbl_p2

	def format(self,add_comments=False):

		out = [self.msgs['file_header']+'\n']
		if self.chksum:
			out.append(f'# {capfirst(self.data_desc)} data checksum for {self.id_str}: {self.chksum}')
			out.append('# Record this value to a secure location.\n')

		lbl = self.make_label()
		dmsg_sc('lbl',lbl[9:])
		out.append(f'{lbl} {{')

		fs = '  {:<%s}  {:<34}{}' % len(str(self.data[-1].idx))
		for e in self.data:
			c = ' '+e.label if add_comments and e.label else ''
			if type(self) == KeyList:
				out.append(fs.format( e.idx, f'{self.al_id.mmtype.wif_label}: {e.sec.wif}', c ))
			elif type(self) == PasswordList:
				out.append(fs.format(e.idx,e.passwd,c))
			else: # First line with idx
				out.append(fs.format(e.idx,e.addr,c))
				if self.has_keys:
					if opt.b16:
						out.append(fs.format( '', f'orig_hex: {e.sec.orig_hex}', c ))
					out.append(fs.format( '', f'{self.al_id.mmtype.wif_label}: {e.sec.wif}', c ))
					for k in ('viewkey','wallet_passwd'):
						v = getattr(e,k)
						if v: out.append(fs.format( '', f'{k}: {v}', c ))

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

		ret = AddrListData()
		le = self.entry_type
		iifs = "{!r}: invalid identifier [expected '{}:']"

		while lines:
			idx,addr,lbl = self.get_line(lines)

			assert is_mmgen_idx(idx), f'invalid address index {idx!r}'
			self.check_format(addr)

			a = le(**{ 'proto': self.proto, 'idx':int(idx), self.main_attr:addr, 'label':lbl })

			if self.has_keys: # order: wif,(orig_hex),viewkey,wallet_passwd
				d = self.get_line(lines)
				assert d[0] == self.al_id.mmtype.wif_label+':', iifs.format(d[0],self.al_id.mmtype.wif_label)
				a.sec = PrivKey(proto=self.proto,wif=d[1])
				for k,dtype,add_proto in (
					('viewkey',ViewKey,True),
					('wallet_passwd',WalletPassword,False) ):
					if k in self.al_id.mmtype.extra_attrs:
						d = self.get_line(lines)
						assert d[0] == k+':', iifs.format(d[0],k)
						setattr(a,k,dtype( *((self.proto,d[1]) if add_proto else (d[1],)) ) )

			ret.append(a)

		if self.has_keys and not self.skip_ka_check:
			if getattr(opt,'yes',False) or keypress_confirm('Check key-to-address validity?'):
				kg = KeyGenerator(self.proto,self.al_id.mmtype)
				ag = AddrGenerator(self.proto,self.al_id.mmtype)
				llen = len(ret)
				for n,e in enumerate(ret):
					qmsg_r(f'\rVerifying keys {n+1}/{llen}')
					assert e.addr == ag.to_addr(kg.to_pubhex(e.sec)),(
						f'Key doesn’t match address!\n  {e.sec.wif}\n  {e.addr}')
				qmsg(' - done')

		return ret

	def parse_file(self,fn,buf=[],exit_on_error=True):

		def parse_addrfile_label(lbl):
			"""
			label examples:
			- Bitcoin legacy mainnet:   no label
			- Bitcoin legacy testnet:   'LEGACY:TESTNET'
			- Bitcoin Segwit:           'SEGWIT'
			- Bitcoin Segwit testnet:   'SEGWIT:TESTNET'
			- Bitcoin Bech32 regtest:   'BECH32:REGTEST'
			- Litecoin legacy mainnet:  'LTC'
			- Litecoin Bech32 mainnet:  'LTC:BECH32'
			- Litecoin legacy testnet:  'LTC:LEGACY:TESTNET'
			- Ethereum mainnet:         'ETH'
			- Ethereum Classic mainnet: 'ETC'
			- Ethereum regtest:         'ETH:REGTEST'
			"""
			lbl = lbl.lower()

			# remove the network component:
			if lbl.endswith(':testnet'):
				network = 'testnet'
				lbl = lbl[:-8]
			elif lbl.endswith(':regtest'):
				network = 'regtest'
				lbl = lbl[:-8]
			else:
				network = 'mainnet'

			if lbl in self.bitcoin_addrtypes:
				coin,mmtype_key = ( 'BTC', lbl )
			elif ':' in lbl: # first component is coin, second is mmtype_key
				coin,mmtype_key = lbl.split(':')
			else:            # only component is coin
				coin,mmtype_key = ( lbl, None )

			proto = init_proto(coin=coin,network=network)

			if mmtype_key == None:
				mmtype_key = proto.mmtypes[0]

			return ( proto, proto.addr_type(mmtype_key) )

		lines = get_lines_from_file(fn,self.data_desc+' data',trim_comments=True)

		try:
			assert len(lines) >= 3, f'Too few lines in address file ({len(lines)})'
			ls = lines[0].split()
			assert 1 < len(ls) < 5, f'Invalid first line for {self.gen_desc} file: {lines[0]!r}'
			assert ls.pop() == '{', f'{ls!r}: invalid first line'
			assert lines[-1] == '}', f'{lines[-1]!r}: invalid last line'
			sid = ls.pop(0)
			assert is_mmgen_seed_id(sid), f'{sid!r}: invalid Seed ID'

			if type(self) == PasswordList and len(ls) == 2:
				ss = ls.pop().split(':')
				assert len(ss) == 2, f'{ss!r}: invalid password length specifier (must contain colon)'
				self.set_pw_fmt(ss[0])
				self.set_pw_len(ss[1])
				self.pw_id_str = MMGenPWIDString(ls.pop())
				proto = init_proto('btc')# FIXME: dummy protocol
				mmtype = MMGenPasswordType(proto,'P')
			elif len(ls) == 1:
				proto,mmtype = parse_addrfile_label(ls[0])
			elif len(ls) == 0:
				proto = init_proto('btc')
				mmtype = proto.addr_type('L')
			else:
				raise ValueError(f'{lines[0]}: Invalid first line for {self.gen_desc} file {fn!r}')

			if type(self) != PasswordList:
				if proto.base_coin != self.proto.base_coin or proto.network != self.proto.network:
					"""
					Having caller supply protocol and checking address file protocol against it here
					allows us to catch all mismatches in one place.  This behavior differs from that of
					transaction files, which determine the protocol independently, requiring the caller
					to check for protocol mismatches (e.g. MMGenTX.check_correct_chain())
					"""
					raise ValueError(
						f'{self.data_desc} file is '
						+ f'{proto.base_coin} {proto.network} but protocol is '
						+ f'{self.proto.base_coin} {self.proto.network}' )

			self.base_coin = proto.base_coin
			self.network = proto.network
			self.al_id = AddrListID(SeedID(sid=sid),mmtype)

			data = self.parse_file_body(lines[1:-1])
			assert isinstance(data,list),'Invalid file body data'
		except Exception as e:
			m = 'Invalid data in {} list file {!r}{} ({!s})'.format(
				self.data_desc,
				self.infile,
				(f', content line {self.line_ctr}' if self.line_ctr else ''),
				e )
			if exit_on_error:
				die(3,m)
			else:
				msg(m)
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
	'file_header': f"""
# {pnm} key file
#
# This file is editable.
# Everything following a hash symbol '#' is a comment and ignored by {pnm}.
""".strip()
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
	'file_header': f"""
# {pnm} password file
#
# This file is editable.
# Everything following a hash symbol '#' is a comment and ignored by {pnm}.
# A text label of {TwComment.max_screen_width} screen cells or less may be added to the right of each
# password.  The label may contain any printable ASCII symbol.
#
""".strip(),
	'file_header_mn': f"""
# {pnm} {{}} password file
#
# This file is editable.
# Everything following a hash symbol '#' is a comment and ignored by {pnm}.
#
""".strip(),
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
		'b32':     pwinfo(10, 42 ,24, None,      'base32 password',          is_b32_str), # 32**24 < 2**128
		'b58':     pwinfo(8,  36 ,20, None,      'base58 password',          is_b58_str), # 58**20 < 2**128
		'bip39':   pwinfo(12, 24 ,24, [12,18,24],'BIP39 mnemonic',           is_bip39_str),
		'xmrseed': pwinfo(25, 25, 25, [25],      'Monero new-style mnemonic',is_xmrseed),
		'hex':     pwinfo(32, 64 ,64, [32,48,64],'hexadecimal password',     is_hex_str),
	}
	chksum_rec_f = lambda foo,e: (str(e.idx), e.passwd)

	feature_warn_fs = 'WARNING: {!r} is a potentially dangerous feature.  Use at your own risk!'
	hex2bip39 = False

	def __init__(self,proto,
		infile          = None,
		seed            = None,
		pw_idxs         = None,
		pw_id_str       = None,
		pw_len          = None,
		pw_fmt          = None,
		chk_params_only = False
		):

		self.proto = proto # proto is ignored
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
			self.al_id = AddrListID(seed.sid,MMGenPasswordType(self.proto,'P'))
			self.data = self.generate(seed,pw_idxs)

		if self.pw_fmt in ('bip39','xmrseed'):
			self.msgs['file_header'] = self.msgs['file_header_mn'].format(self.pw_fmt.upper())

		self.num_addrs = len(self.data)
		self.fmt_data = ''
		self.chksum = AddrListChksum(self)

		fs = f'{self.al_id.sid}-{self.pw_id_str}-{self.pw_fmt_disp}-{self.pw_len}[{{}}]'
		self.id_str = AddrListIDStr(self,fs)
		qmsg(
			f'Checksum for {self.data_desc} data {self.id_str.hl()}: {self.chksum.hl()}\n' +
			self.msgs[('record_chksum','check_chksum')[bool(infile)]] )

	def set_pw_fmt(self,pw_fmt):
		if pw_fmt == 'hex2bip39':
			self.hex2bip39 = True
			self.pw_fmt = 'bip39'
			self.pw_fmt_disp = 'hex2bip39'
		else:
			self.pw_fmt = pw_fmt
			self.pw_fmt_disp = pw_fmt
		if self.pw_fmt not in self.pw_info:
			raise InvalidPasswdFormat(
				'{!r}: invalid password format.  Valid formats: {}'.format(
					self.pw_fmt,
					', '.join(self.pw_info) ))

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
				die(2, fs.format( l=pw_len, b=d.desc, c='not one of ', m=d.valid_lens, pw=passwd ))
		elif pw_len > d.max_len:
			die(2, fs.format( l=pw_len, b=d.desc, c='>', m=d.max_len, pw=passwd ))
		elif pw_len < d.min_len:
			die(2, fs.format( l=pw_len, b=d.desc, c='<', m=d.min_len, pw=passwd ))

	def set_pw_len(self,pw_len):
		d = self.pw_info[self.pw_fmt]

		if pw_len is None:
			self.pw_len = d.dfl_len
			return

		if not is_int(pw_len):
			die(2,f'{pw_len!r}: invalid user-requested password length (not an integer)')
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
				die(1,f'{seed.byte_len*8}: unsupported seed length for Monero new-style mnemonic')
		elif pf in ('b32','b58'):
			pw_int = (32 if pf == 'b32' else 58) ** self.pw_len
			pw_bytes = pw_int.bit_length() // 8
			good_pw_len = len(baseconv.frombytes(b'\xff'*seed.byte_len,wl_id=pf))
		else:
			raise NotImplementedError(f'{pf!r}: unknown password format')

		if pw_bytes > seed.byte_len:
			die(1,
				'Cannot generate passwords with more entropy than underlying seed! ({} bits)\n'.format(
					len(seed.data) * 8 ) + (
					'Re-run the command with --passwd-len={}' if pf in ('bip39','hex') else
					'Re-run the command, specifying a password length of {} or less'
				).format(good_pw_len) )

		if pf in ('bip39','hex') and pw_bytes < seed.byte_len:
			if not keypress_confirm(
					f'WARNING: requested {self.pw_info[pf].desc} length has less entropy ' +
					'than underlying seed!\nIs this what you want?',
					default_yes = True ):
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
			bytes_preproc = init_proto('xmr').preprocess_key(bytes_trunc,None)
			return ' '.join(baseconv.frombytes(bytes_preproc,wl_id='xmrseed'))
		else:
			# take least significant part
			return baseconv.fromhex(hex_sec,self.pw_fmt,pad=self.pw_len,tostr=True)[-self.pw_len:]

	def check_format(self,pw):
		if not self.pw_info[self.pw_fmt].chk_func(pw):
			raise ValueError(f'Password is not valid {self.pw_info[self.pw_fmt].desc} data')
		pwlen = len(pw.split()) if self.pw_fmt in ('bip39','xmrseed') else len(pw)
		if pwlen != self.pw_len:
			raise ValueError(f'Password has incorrect length ({pwlen} != {self.pw_len})')
		return True

	def scramble_seed(self,seed):
		# Changing either pw_fmt or pw_len will cause a different, unrelated
		# set of passwords to be generated: this is what we want.
		# NB: In original implementation, pw_id_str was 'baseN', not 'bN'
		scramble_key = f'{self.pw_fmt}:{self.pw_len}:{self.pw_id_str}'

		if self.hex2bip39:
			from .bip39 import bip39
			pwlen = bip39.nwords2seedlen(self.pw_len,in_hex=True)
			scramble_key = f'hex:{pwlen}:{self.pw_id_str}'

		from .crypto import scramble_seed
		dmsg_sc('str',scramble_key)
		return scramble_seed(seed,scramble_key.encode())

	def get_line(self,lines):
		self.line_ctr += 1
		if self.pw_fmt in ('bip39','xmrseed'):
			ret = lines.pop(0).split(None,self.pw_len+1)
			if len(ret) > self.pw_len+1:
				m1 = f'extraneous text {ret[self.pw_len+1]!r} found after password'
				m2 = '[bare comments not allowed in BIP39 password files]'
				m = m1+' '+m2
			elif len(ret) < self.pw_len+1:
				m = f'invalid password length {len(ret)-1}'
			else:
				return (ret[0],' '.join(ret[1:self.pw_len+1]),'')
			raise ValueError(m)
		else:
			ret = lines.pop(0).split(None,2)
			return ret if len(ret) == 3 else ret + ['']

	def make_label(self):
		return f'{self.al_id.sid} {self.pw_id_str} {self.pw_fmt_disp}:{self.pw_len}'

class AddrData(MMGenObject):
	msgs = {
	'too_many_acct_addresses': f"""
ERROR: More than one address found for account: '{{}}'.
Your 'wallet.dat' file appears to have been altered by a non-{pnm} program.
Please restore your tracking wallet from a backup or create a new one and
re-import your addresses.
""".strip()
	}

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(altcoin_subclass(cls,proto,'tw'))

	def __init__(self,proto,*args,**kwargs):
		self.al_ids = {}
		self.proto = proto
		self.rpc = None

	def seed_ids(self):
		return list(self.al_ids.keys())

	def addrlist(self,al_id):
		# TODO: Validate al_id
		if al_id in self.al_ids:
			return self.al_ids[al_id]

	def mmaddr2coinaddr(self,mmaddr):
		al_id,idx = MMGenID(self.proto,mmaddr).rsplit(':',1)
		coinaddr = ''
		if al_id in self.al_ids:
			coinaddr = self.addrlist(al_id).coinaddr(int(idx))
		return coinaddr or None

	def coinaddr2mmaddr(self,coinaddr):
		d = self.make_reverse_dict([coinaddr])
		return (list(d.values())[0][0]) if d else None

	def add(self,addrlist):
		if type(addrlist) == AddrList:
			self.al_ids[addrlist.al_id] = addrlist
			return True
		else:
			raise TypeError(f'Error: object {addrlist!r} is not of type AddrList')

	def make_reverse_dict(self,coinaddrs):
		d = MMGenDict()
		for al_id in self.al_ids:
			d.update(self.al_ids[al_id].make_reverse_dict_addrlist(coinaddrs))
		return d

class TwAddrData(AddrData,metaclass=AsyncInit):

	def __new__(cls,proto,*args,**kwargs):
		return MMGenObject.__new__(altcoin_subclass(cls,proto,'tw'))

	async def __init__(self,proto,wallet=None):
		self.proto = proto
		from .rpc import rpc_init
		self.rpc = await rpc_init(proto)
		self.al_ids = {}
		await self.add_tw_data(wallet)

	async def get_tw_data(self,wallet=None):
		vmsg('Getting address data from tracking wallet')
		c = self.rpc
		if 'label_api' in c.caps:
			accts = await c.call('listlabels')
			ll = await c.batch_call('getaddressesbylabel',[(k,) for k in accts])
			alists = [list(a.keys()) for a in ll]
		else:
			accts = await c.call('listaccounts',0,True)
			alists = await c.batch_call('getaddressesbyaccount',[(k,) for k in accts])
		return list(zip(accts,alists))

	async def add_tw_data(self,wallet):

		twd = await self.get_tw_data(wallet)
		out,i = {},0
		for acct,addr_array in twd:
			l = get_obj(TwLabel,proto=self.proto,text=acct,silent=True)
			if l and l.mmid.type == 'mmgen':
				obj = l.mmid.obj
				if len(addr_array) != 1:
					die(2,self.msgs['too_many_acct_addresses'].format(acct))
				al_id = AddrListID(SeedID(sid=obj.sid),self.proto.addr_type(obj.mmtype))
				if al_id not in out:
					out[al_id] = []
				out[al_id].append(AddrListEntry(self.proto,idx=obj.idx,addr=addr_array[0],label=l.comment))
				i += 1

		vmsg(f'{i} {pnm} addresses found, {len(twd)} accounts total')
		for al_id in out:
			self.add(AddrList(self.proto,al_id=al_id,adata=AddrListData(sorted(out[al_id],key=lambda a: a.idx))))
