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
addr: MMGen address-related types
"""

from collections import namedtuple

from .objmethods import HiliteStr, InitErrors, MMGenObject
from .obj import ImmutableAttr, MMGenIdx, get_obj
from .seed import SeedID
from . import color as color_mod

ati = namedtuple('addrtype_info',
	['name', 'pubkey_type', 'compressed', 'gen_method', 'addr_fmt', 'wif_label', 'extra_attrs', 'desc'])

class MMGenAddrType(HiliteStr, InitErrors, MMGenObject):
	width = 1
	trunc_ok = False
	color = 'blue'

	name        = ImmutableAttr(str)
	pubkey_type = ImmutableAttr(str)
	compressed  = ImmutableAttr(bool, set_none_ok=True)
	gen_method  = ImmutableAttr(str, set_none_ok=True)
	addr_fmt    = ImmutableAttr(str, set_none_ok=True)
	wif_label   = ImmutableAttr(str, set_none_ok=True)
	extra_attrs = ImmutableAttr(tuple, set_none_ok=True)
	desc        = ImmutableAttr(str)

	pkh_fmts = ('p2pkh', 'bech32', 'ethereum')
	mmtypes = {
		'L': ati('legacy',    'std', False,'p2pkh',   'p2pkh',   'wif', (), 'Legacy uncompressed address'),
		'C': ati('compressed','std', True, 'p2pkh',   'p2pkh',   'wif', (), 'Compressed P2PKH address'),
		'S': ati('segwit',    'std', True, 'segwit',  'p2sh',    'wif', (), 'Segwit P2SH-P2WPKH address'),
		'B': ati('bech32',    'std', True, 'bech32',  'bech32',  'wif', (), 'Native Segwit (Bech32) address'),
		'E': ati('ethereum',  'std', False,'ethereum','p2pkh',   'privkey', ('wallet_passwd',),'Ethereum address'),
		'Z': ati('zcash_z','zcash_z',False,'zcash_z', 'zcash_z', 'wif',     ('viewkey',),      'Zcash z-address'),
		'M': ati('monero', 'monero', False,'monero',  'monero',  'spendkey',('viewkey','wallet_passwd'),'Monero address'),
	}
	def __new__(cls, proto, id_str, errmsg=None):
		if isinstance(id_str, cls):
			return id_str
		try:
			id_str = id_str.replace('-', '_')
			for k, v in cls.mmtypes.items():
				if id_str in (k, v.name):
					if id_str == v.name:
						id_str = k
					me = str.__new__(cls, id_str)
					for k in v._fields:
						setattr(me, k, getattr(v, k))
					if me not in proto.mmtypes + ('P',):
						raise ValueError(f'{me.name!r}: invalid address type for {proto.name} protocol')
					me.proto = proto
					return me
			raise ValueError(f'{id_str}: unrecognized address type for protocol {proto.name}')
		except Exception as e:
			return cls.init_fail(
				e,
				f"{errmsg or ''}{id_str!r}: invalid value for {cls.__name__} ({e!s})",
				preformat = True)

	@classmethod
	def get_names(cls):
		return [v.name for v in cls.mmtypes.values()]

def is_mmgen_addrtype(proto, id_str):
	return get_obj(MMGenAddrType, proto=proto, id_str=id_str, silent=True, return_bool=True)

class MMGenPasswordType(MMGenAddrType):
	mmtypes = {
		'P': ati('password', 'password', None, None, None, None, None, 'Password generated from MMGen seed')
	}

class AddrIdx(MMGenIdx):
	max_digits = 7

def is_addr_idx(s):
	return get_obj(AddrIdx, n=s, silent=True, return_bool=True)

class AddrListID(HiliteStr, InitErrors, MMGenObject):
	width = 10
	trunc_ok = False
	color = 'yellow'
	def __new__(cls, sid=None, mmtype=None, proto=None, id_str=None):
		try:
			if id_str:
				a, b = id_str.split(':')
				sid = SeedID(sid=a)
				try:
					mmtype = MMGenAddrType(proto=proto, id_str=b)
				except:
					mmtype = MMGenPasswordType(proto=proto, id_str=b)
			else:
				assert isinstance(sid, SeedID), f'{sid!r} not a SeedID instance'
				if not isinstance(mmtype, (MMGenAddrType, MMGenPasswordType)):
					raise ValueError(f'{mmtype!r}: not an instance of MMGenAddrType or MMGenPasswordType')
			me = str.__new__(cls, sid+':'+mmtype)
			me.sid = sid
			me.mmtype = mmtype
			return me
		except Exception as e:
			return cls.init_fail(e, f'sid={sid}, mmtype={mmtype}')

def is_addrlist_id(proto, s):
	return get_obj(AddrListID, proto=proto, id_str=s, silent=False, return_bool=True)

class MMGenID(HiliteStr, InitErrors, MMGenObject):
	color = 'orange'
	width = 0
	trunc_ok = False
	def __new__(cls, proto, id_str):
		try:
			ss = str(id_str).split(':')
			assert len(ss) in (2, 3), 'not 2 or 3 colon-separated items'
			t = proto.addr_type((ss[1], proto.dfl_mmtype)[len(ss)==2])
			me = str.__new__(cls, f'{ss[0]}:{t}:{ss[-1]}')
			me.sid = SeedID(sid=ss[0])
			me.idx = AddrIdx(ss[-1])
			me.mmtype = t
			assert t in proto.mmtypes, f'{t}: invalid address type for {proto.cls_name}'
			me.al_id = str.__new__(AddrListID, me.sid+':'+me.mmtype) # checks already done
			me.sort_key = f'{me.sid}:{me.mmtype}:{me.idx:0{me.idx.max_digits}}'
			me.proto = proto
			return me
		except Exception as e:
			return cls.init_fail(e, id_str)

def is_mmgen_id(proto, s):
	return get_obj(MMGenID, proto=proto, id_str=s, silent=True, return_bool=True)

class CoinAddr(HiliteStr, InitErrors, MMGenObject):
	color = 'cyan'
	hex_width = 40
	width = 1
	trunc_ok = False

	def __new__(cls, proto, addr):
		if isinstance(addr, cls):
			return addr
		try:
			ap = proto.decode_addr(addr)
			assert ap, f'coin address {addr!r} could not be parsed'
			if hasattr(ap, 'addr'):
				me = str.__new__(cls, ap.addr)
				me.views = ap.views
				me.view_pref = ap.view_pref
			else:
				me = str.__new__(cls, addr)
				me.views = [addr]
				me.view_pref = 0
			me.addr_fmt = ap.fmt
			me.bytes = ap.bytes
			me.ver_bytes = ap.ver_bytes
			me.proto = proto
			return me
		except Exception as e:
			return cls.init_fail(e, addr, objname=f'{proto.cls_name} address')

	@property
	def parsed(self):
		if not hasattr(self, '_parsed'):
			self._parsed = self.proto.parse_addr(self.ver_bytes, self.bytes, self.addr_fmt)
		return self._parsed

	# reimplement some HiliteStr methods:
	@classmethod
	def fmtc(cls, s, width, color=False):
		return super().fmtc(s=s[:width-2]+'..' if len(s) > width else s, width=width, color=color)

	def fmt(self, view_pref, width, color=False):
		s = self.views[view_pref]
		return super().fmtc(f'{s[:width-2]}..' if len(s) > width else s, width=width, color=color)

	def hl(self, view_pref, color=True):
		return getattr(color_mod, self.color)(self.views[view_pref]) if color else self.views[view_pref]

def is_coin_addr(proto, s):
	return get_obj(CoinAddr, proto=proto, addr=s, silent=True, return_bool=True)

class TokenAddr(CoinAddr):
	color = 'blue'

def ViewKey(proto, viewkey_str):
	return proto.viewkey(viewkey_str)
