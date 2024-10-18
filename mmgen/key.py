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
key: MMGen public and private key objects
"""

from .objmethods import HiliteStr, InitErrors, MMGenObject
from .obj import ImmutableAttr, get_obj

class WifKey(HiliteStr, InitErrors):
	"""
	Initialize a WIF key, checking its well-formedness.
	The numeric validity of the private key it encodes is not checked.
	"""
	width = 53
	color = 'blue'
	def __new__(cls, proto, wif):
		if isinstance(wif, cls):
			return wif
		try:
			assert wif.isascii() and wif.isalnum(), 'not an ASCII alphanumeric string'
			proto.decode_wif(wif) # raises exception on error
			return str.__new__(cls, wif)
		except Exception as e:
			return cls.init_fail(e, wif)

def is_wif(proto, s):
	return get_obj(WifKey, proto=proto, wif=s, silent=True, return_bool=True)

class PubKey(bytes, InitErrors, MMGenObject): # TODO: add some real checks

	def __new__(cls, s, compressed):
		try:
			assert isinstance(s, bytes)
			me = bytes.__new__(cls, s)
			me.compressed = compressed
			return me
		except Exception as e:
			return cls.init_fail(e, s)

class PrivKey(bytes, InitErrors, MMGenObject):
	"""
	Input:   a) raw, non-preprocessed bytes; or b) WIF key.
	Output:  preprocessed key bytes, plus WIF key in 'wif' attribute
	For coins without a WIF format, 'wif' contains the preprocessed hex.
	The numeric validity of the resulting key is always checked.
	"""
	color = 'red'
	width = 32
	trunc_ok = False

	compressed = ImmutableAttr(bool, typeconv=False)
	wif        = ImmutableAttr(WifKey, typeconv=False)

	# initialize with (priv_bin, compressed), WIF or self
	def __new__(cls, proto, s=None, compressed=None, wif=None, pubkey_type=None):
		if isinstance(s, cls):
			return s
		if wif:
			try:
				assert s is None, "'wif' and key hex args are mutually exclusive"
				assert wif.isascii() and wif.isalnum(), 'not an ASCII alphanumeric string'
				k = proto.decode_wif(wif) # raises exception on error
				me = bytes.__new__(cls, k.sec)
				me.compressed = k.compressed
				me.pubkey_type = k.pubkey_type
				me.wif = str.__new__(WifKey, wif) # check has been done
				me.orig_bytes = None
				if k.sec != proto.preprocess_key(k.sec, k.pubkey_type):
					from .util import die
					die('PrivateKeyError',
						f'{proto.cls_name} WIF key {me.wif!r} encodes private key with invalid value {me}')
				me.proto = proto
				return me
			except Exception as e:
				return cls.init_fail(e, s, objname=f'{proto.coin} WIF key')
		else:
			try:
				assert s, 'private key bytes data missing'
				assert isinstance(s, bytes), 'input is not bytes'
				assert pubkey_type is not None, "'pubkey_type' arg missing"
				assert len(s) == cls.width, f'key length must be {cls.width} bytes'
				if pubkey_type == 'password': # skip WIF creation and pre-processing for passwds
					me = bytes.__new__(cls, s)
				else:
					assert compressed is not None, "'compressed' arg missing"
					assert type(compressed) is bool, (
						f"'compressed' must be of type bool, not {type(compressed).__name__}")
					me = bytes.__new__(cls, proto.preprocess_key(s, pubkey_type))
					me.wif = WifKey(proto, proto.encode_wif(me, pubkey_type, compressed))
					me.compressed = compressed
				me.pubkey_type = pubkey_type
				me.orig_bytes = s # save the non-preprocessed key
				me.proto = proto
				return me
			except Exception as e:
				return cls.init_fail(e, s)
