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
passwdlist.py: Password list class for the MMGen suite
"""

from collections import namedtuple

from .exception import InvalidPasswdFormat
from .util import ymsg,is_hex_str,is_int,keypress_confirm
from .obj import ImmutableAttr,ListItemAttr,MMGenPWIDString,PrivKey
from .baseconv import baseconv,is_b32_str,is_b58_str
from .addr import MMGenPasswordType,AddrIdx,AddrListID,is_xmrseed,is_bip39_str
from .addrlist import (
	AddrListChksum,
	AddrListIDStr,
	AddrListEntryBase,
	AddrList,
	dmsg_sc,
)

class PasswordListEntry(AddrListEntryBase):
	passwd = ListItemAttr(str,typeconv=False) # TODO: create Password type
	idx    = ImmutableAttr(AddrIdx)
	label  = ListItemAttr('TwComment',reassign_ok=True)
	sec    = ListItemAttr(PrivKey,include_proto=True)

class PasswordList(AddrList):
	entry_type  = PasswordListEntry
	main_attr   = 'passwd'
	desc        = 'password'
	gen_desc    = 'password'
	gen_desc_pl = 's'
	gen_addrs   = False
	gen_keys    = False
	gen_passwds = True
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
			chk_params_only = False,
		):

		self.proto = proto # proto is ignored

		if infile:
			self.infile = infile
			self.data = self.get_file().parse_file(infile) # sets self.pw_id_str,self.pw_fmt,self.pw_len
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

		self.num_addrs = len(self.data)
		self.fmt_data = ''
		self.chksum = AddrListChksum(self)

		fs = f'{self.al_id.sid}-{self.pw_id_str}-{self.pw_fmt_disp}-{self.pw_len}[{{}}]'
		self.id_str = AddrListIDStr(self,fs)
		self.do_chksum_msg(record=not infile)

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

	def gen_passwd(self,hex_sec):
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
			from .protocol import init_proto
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