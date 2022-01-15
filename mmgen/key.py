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
key.py: MMGen public and private key objects
"""

from string import ascii_letters,digits
from .objmethods import Hilite,InitErrors,MMGenObject
from .obj import ImmutableAttr,get_obj,HexStr

class WifKey(str,Hilite,InitErrors):
	"""
	Initialize a WIF key, checking its well-formedness.
	The numeric validity of the private key it encodes is not checked.
	"""
	width = 53
	color = 'blue'
	def __new__(cls,proto,wif):
		if type(wif) == cls:
			return wif
		try:
			assert set(wif) <= set(ascii_letters+digits),'not an ascii alphanumeric string'
			proto.parse_wif(wif) # raises exception on error
			return str.__new__(cls,wif)
		except Exception as e:
			return cls.init_fail(e,wif)

def is_wif(proto,s):
	return get_obj( WifKey, proto=proto, wif=s, silent=True, return_bool=True )

class PubKey(HexStr,MMGenObject): # TODO: add some real checks

	def __new__(cls,s,privkey):
		try:
			me = HexStr.__new__(cls,s,case='lower')
			me.privkey = privkey
			me.compressed = privkey.compressed
			return me
		except Exception as e:
			return cls.init_fail(e,s)

class PrivKey(str,Hilite,InitErrors,MMGenObject):
	"""
	Input:   a) raw, non-preprocessed bytes; or b) WIF key.
	Output:  preprocessed hexadecimal key, plus WIF key in 'wif' attribute
	For coins without a WIF format, 'wif' contains the preprocessed hex.
	The numeric validity of the resulting key is always checked.
	"""
	color = 'red'
	width = 64
	trunc_ok = False

	compressed = ImmutableAttr(bool,typeconv=False)
	wif        = ImmutableAttr(WifKey,typeconv=False)

	# initialize with (priv_bin,compressed), WIF or self
	def __new__(cls,proto,s=None,compressed=None,wif=None,pubkey_type=None):
		if type(s) == cls:
			return s
		if wif:
			try:
				assert s == None,"'wif' and key hex args are mutually exclusive"
				assert set(wif) <= set(ascii_letters+digits),'not an ascii alphanumeric string'
				k = proto.parse_wif(wif) # raises exception on error
				me = str.__new__(cls,k.sec.hex())
				me.compressed = k.compressed
				me.pubkey_type = k.pubkey_type
				me.wif = str.__new__(WifKey,wif) # check has been done
				me.orig_hex = None
				if k.sec != proto.preprocess_key(k.sec,k.pubkey_type):
					from .exception import PrivateKeyError
					raise PrivateKeyError(
						f'{proto.cls_name} WIF key {me.wif!r} encodes private key with invalid value {me}')
				me.proto = proto
				return me
			except Exception as e:
				return cls.init_fail(e,s,objname=f'{proto.coin} WIF key')
		else:
			try:
				assert s,'private key bytes data missing'
				assert pubkey_type is not None,"'pubkey_type' arg missing"
				assert len(s) == cls.width // 2, f'key length must be {cls.width // 2} bytes'
				if pubkey_type == 'password': # skip WIF creation and pre-processing for passwds
					me = str.__new__(cls,s.hex())
				else:
					assert compressed is not None, "'compressed' arg missing"
					assert type(compressed) == bool,(
						f"'compressed' must be of type bool, not {type(compressed).__name__}" )
					me = str.__new__(cls,proto.preprocess_key(s,pubkey_type).hex())
					me.wif = WifKey(proto,proto.hex2wif(me,pubkey_type,compressed))
					me.compressed = compressed
				me.pubkey_type = pubkey_type
				me.orig_hex = s.hex() # save the non-preprocessed key
				me.proto = proto
				return me
			except Exception as e:
				return cls.init_fail(e,s)
