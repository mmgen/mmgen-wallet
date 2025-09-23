#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.zec.params: Zcash protocol
"""

from ..btc.params import mainnet
from ...protocol import decoded_addr
from ...addr import CoinAddr

class ZcashViewKey(CoinAddr):
	hex_width = 128

class mainnet(mainnet):
	base_coin      = 'ZEC'
	addr_ver_info  = {'1cb8': 'p2pkh', '1cbd': 'p2sh', '169a': 'zcash_z', 'a8abd3': 'viewkey'}
	wif_ver_num    = {'std': '80', 'zcash_z': 'ab36'}
	pubkey_types   = ('std', 'zcash_z')
	mmtypes        = ('L', 'C', 'Z')
	mmcaps         = ()
	dfl_mmtype     = 'L'
	avg_bdi        = 75

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.coin_id = 'ZEC-Z' if self.cfg.type in ('zcash_z', 'Z') else 'ZEC-T'

	def get_wif_ver_bytes_len(self, key_data):
		"""
		vlen must be set dynamically since Zcash has variable-length version bytes
		"""
		for v in self.wif_ver_bytes.values():
			if key_data[:len(v)] == v:
				return len(v)
		raise ValueError('Invalid WIF version number')

	def get_addr_len(self, addr_fmt):
		return (20, 64)[addr_fmt in ('zcash_z', 'viewkey')]

	def decode_addr_bytes(self, addr_bytes):
		"""
		vlen must be set dynamically since Zcash has variable-length version bytes
		"""
		for ver_bytes, addr_fmt in self.addr_ver_bytes.items():
			vlen = len(ver_bytes)
			if addr_bytes[:vlen] == ver_bytes:
				if len(addr_bytes[vlen:]) == self.get_addr_len(addr_fmt):
					return decoded_addr(addr_bytes[vlen:], ver_bytes, addr_fmt)

		return False

	def preprocess_key(self, sec, pubkey_type):
		if pubkey_type == 'zcash_z': # zero the first four bits
			return bytes([sec[0] & 0x0f]) + sec[1:]
		else:
			return super().preprocess_key(sec, pubkey_type)

	def pubhash2addr(self, pubhash, addr_type):
		match len(pubhash):
			case 20:
				return super().pubhash2addr(pubhash, addr_type)
			case 64:
				raise NotImplementedError('Zcash z-addresses do not support pubhash2addr()')
			case x:
				raise ValueError(f'{x}: incorrect pubkey hash length')

	def viewkey(self, viewkey_str):
		return ZcashViewKey.__new__(ZcashViewKey, self, viewkey_str)

class testnet(mainnet):
	wif_ver_num  = {'std': 'ef', 'zcash_z': 'ac08'}
	addr_ver_info = {'1d25': 'p2pkh', '1cba': 'p2sh', '16b6': 'zcash_z', 'a8ac0c': 'viewkey'}
