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
addr.py: MMGen address-related types
"""

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

	pkh_fmts = ('p2pkh','bech32','ethereum')
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
			assert addr.isascii() and addr.isalnum(), 'not an ASCII alphanumeric string'
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

def KeyGenerator(proto,pubkey_type,backend=None,silent=False):
	"""
	factory function returning a key generator backend for the specified pubkey type
	"""
	assert pubkey_type in proto.pubkey_types, f'{pubkey_type!r}: invalid pubkey type for coin {proto.coin}'

	from .keygen import keygen_backend,_check_backend

	pubkey_type_cls = getattr(keygen_backend,pubkey_type)

	from .opts import opt
	backend = backend or opt.keygen_backend

	if backend:
		_check_backend(backend,pubkey_type)

	backend_id = pubkey_type_cls.backends[int(backend) - 1 if backend else 0]

	if backend_id == 'libsecp256k1':
		if not pubkey_type_cls.libsecp256k1.test_avail(silent=silent):
			backend_id = 'python-ecdsa'
			if not backend:
				qmsg('Using (slow) native Python ECDSA library for public key generation')

	return getattr(pubkey_type_cls,backend_id.replace('-','_'))()

def AddrGenerator(proto,addr_type):
	"""
	factory function returning an address generator for the specified address type
	"""
	if type(addr_type) == str:
		addr_type = MMGenAddrType(proto=proto,id_str=addr_type)
	elif type(addr_type) == MMGenAddrType:
		assert addr_type in proto.mmtypes, f'{addr_type}: invalid address type for coin {proto.coin}'
	else:
		raise TypeError(f'{type(addr_type)}: incorrect argument type for {cls.__name__}()')

	from .addrgen import addr_generator

	return getattr(addr_generator,addr_type.name)(proto,addr_type)
