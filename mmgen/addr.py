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

from string import ascii_letters,digits
from collections import namedtuple

from .objmethods import Hilite,InitErrors,MMGenObject
from .obj import ImmutableAttr,MMGenIdx,HexStr,get_obj
from .seed import SeedID

ati = namedtuple('addrtype_info',
	['name','pubkey_type','compressed','gen_method','addr_fmt','wif_label','extra_attrs','desc'])

class MMGenAddrType(str,Hilite,InitErrors,MMGenObject):
	width = 1
	trunc_ok = False
	color = 'blue'

	name        = ImmutableAttr(str)
	pubkey_type = ImmutableAttr(str)
	compressed  = ImmutableAttr(bool,set_none_ok=True)
	gen_method  = ImmutableAttr(str,set_none_ok=True)
	addr_fmt    = ImmutableAttr(str,set_none_ok=True)
	wif_label   = ImmutableAttr(str,set_none_ok=True)
	extra_attrs = ImmutableAttr(tuple,set_none_ok=True)
	desc        = ImmutableAttr(str)

	mmtypes = {
		'L': ati('legacy',    'std', False,'p2pkh',   'p2pkh',   'wif', (), 'Legacy uncompressed address'),
		'C': ati('compressed','std', True, 'p2pkh',   'p2pkh',   'wif', (), 'Compressed P2PKH address'),
		'S': ati('segwit',    'std', True, 'segwit',  'p2sh',    'wif', (), 'Segwit P2SH-P2WPKH address'),
		'B': ati('bech32',    'std', True, 'bech32',  'bech32',  'wif', (), 'Native Segwit (Bech32) address'),
		'E': ati('ethereum',  'std', False,'ethereum','ethereum','privkey', ('wallet_passwd',),'Ethereum address'),
		'Z': ati('zcash_z','zcash_z',False,'zcash_z', 'zcash_z', 'wif',     ('viewkey',),      'Zcash z-address'),
		'M': ati('monero', 'monero', False,'monero',  'monero',  'spendkey',('viewkey','wallet_passwd'),'Monero address'),
	}
	def __new__(cls,proto,id_str,errmsg=None):
		if isinstance(id_str,cls):
			return id_str
		try:
			id_str = id_str.replace('-','_')
			for k,v in cls.mmtypes.items():
				if id_str in (k,v.name):
					if id_str == v.name:
						id_str = k
					me = str.__new__(cls,id_str)
					for k in v._fields:
						setattr(me,k,getattr(v,k))
					if me not in proto.mmtypes + ('P',):
						raise ValueError(f'{me.name!r}: invalid address type for {proto.name} protocol')
					me.proto = proto
					return me
			raise ValueError(f'{id_str}: unrecognized address type for protocol {proto.name}')
		except Exception as e:
			return cls.init_fail( e,
				f"{errmsg or ''}{id_str!r}: invalid value for {cls.__name__} ({e!s})",
				preformat = True )

	@classmethod
	def get_names(cls):
		return [v.name for v in cls.mmtypes.values()]

class MMGenPasswordType(MMGenAddrType):
	mmtypes = {
		'P': ati('password', 'password', None, None, None, None, None, 'Password generated from MMGen seed')
	}

class AddrIdx(MMGenIdx):
	max_digits = 7

def is_addr_idx(s):
	return get_obj( AddrIdx, n=s, silent=True, return_bool=True )

class AddrListID(str,Hilite,InitErrors,MMGenObject):
	width = 10
	trunc_ok = False
	color = 'yellow'
	def __new__(cls,sid,mmtype):
		try:
			assert type(sid) == SeedID, f'{sid!r} not a SeedID instance'
			if not isinstance(mmtype,(MMGenAddrType,MMGenPasswordType)):
				raise ValueError(f'{mmtype!r}: not an instance of MMGenAddrType or MMGenPasswordType')
			me = str.__new__(cls,sid+':'+mmtype)
			me.sid = sid
			me.mmtype = mmtype
			return me
		except Exception as e:
			return cls.init_fail(e, f'sid={sid}, mmtype={mmtype}')

def is_addrlist_id(s):
	return get_obj( AddrListID, sid=s, silent=True, return_bool=True )

class MMGenID(str,Hilite,InitErrors,MMGenObject):
	color = 'orange'
	width = 0
	trunc_ok = False
	def __new__(cls,proto,id_str):
		try:
			ss = str(id_str).split(':')
			assert len(ss) in (2,3),'not 2 or 3 colon-separated items'
			t = proto.addr_type((ss[1],proto.dfl_mmtype)[len(ss)==2])
			me = str.__new__(cls,'{}:{}:{}'.format(ss[0],t,ss[-1]))
			me.sid = SeedID(sid=ss[0])
			me.idx = AddrIdx(ss[-1])
			me.mmtype = t
			assert t in proto.mmtypes, f'{t}: invalid address type for {proto.cls_name}'
			me.al_id = str.__new__(AddrListID,me.sid+':'+me.mmtype) # checks already done
			me.sort_key = '{}:{}:{:0{w}}'.format(me.sid,me.mmtype,me.idx,w=me.idx.max_digits)
			me.proto = proto
			return me
		except Exception as e:
			return cls.init_fail(e,id_str)

def is_mmgen_id(proto,s):
	return get_obj( MMGenID, proto=proto, id_str=s, silent=True, return_bool=True )

class CoinAddr(str,Hilite,InitErrors,MMGenObject):
	color = 'cyan'
	hex_width = 40
	width = 1
	trunc_ok = False
	def __new__(cls,proto,addr):
		if type(addr) == cls:
			return addr
		try:
			assert set(addr) <= set(ascii_letters+digits),'contains non-alphanumeric characters'
			me = str.__new__(cls,addr)
			ap = proto.parse_addr(addr)
			assert ap, f'coin address {addr!r} could not be parsed'
			me.addr_fmt = ap.fmt
			me.hex = ap.bytes.hex()
			me.proto = proto
			return me
		except Exception as e:
			return cls.init_fail(e,addr,objname=f'{proto.cls_name} address')

	@classmethod
	def fmtc(cls,addr,**kwargs):
		w = kwargs['width'] or cls.width
		return super().fmtc(addr[:w-2]+'..' if w < len(addr) else addr, **kwargs)

def is_coin_addr(proto,s):
	return get_obj( CoinAddr, proto=proto, addr=s, silent=True, return_bool=True )

class TokenAddr(CoinAddr):
	color = 'blue'

class ViewKey(object):
	def __new__(cls,proto,viewkey):
		if proto.name == 'Zcash':
			return ZcashViewKey.__new__(ZcashViewKey,proto,viewkey)
		elif proto.name == 'Monero':
			return MoneroViewKey.__new__(MoneroViewKey,viewkey)
		else:
			raise ValueError(f'{proto.name}: protocol does not support view keys')

class MoneroViewKey(HexStr):
	color,width,hexcase = 'cyan',64,'lower' # FIXME - no checking performed

class ZcashViewKey(CoinAddr):
	hex_width = 128

from .opts import opt
from .util import qmsg
from .protocol import hash160
from .key import PrivKey,PubKey
from .baseconv import baseconv

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

		from .util import get_keccak
		self.keccak_256 = get_keccak()

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

		from .util import get_keccak
		self.keccak_256 = get_keccak()

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
