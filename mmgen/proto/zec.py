#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
Zcash protocol
"""

from .btc import mainnet

class mainnet(mainnet):
	base_coin      = 'ZEC'
	addr_ver_bytes = { '1cb8': 'p2pkh', '1cbd': 'p2sh', '169a': 'zcash_z', 'a8abd3': 'viewkey' }
	wif_ver_num    = { 'std': '80', 'zcash_z': 'ab36' }
	pubkey_types   = ('std','zcash_z')
	mmtypes        = ('L','C','Z')
	mmcaps         = ('key','addr')
	dfl_mmtype     = 'L'
	avg_bdi        = 75

	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		from ..opts import opt
		self.coin_id = 'ZEC-Z' if opt.type in ('zcash_z','Z') else 'ZEC-T'

	def get_addr_len(self,addr_fmt):
		return (20,64)[addr_fmt in ('zcash_z','viewkey')]

	def preprocess_key(self,sec,pubkey_type):
		if pubkey_type == 'zcash_z': # zero the first four bits
			return bytes([sec[0] & 0x0f]) + sec[1:]
		else:
			return super().preprocess_key(sec,pubkey_type)

	def pubhash2addr(self,pubkey_hash,p2sh):
		hash_len = len(pubkey_hash)
		if hash_len == 20:
			return super().pubhash2addr(pubkey_hash,p2sh)
		elif hash_len == 64:
			raise NotImplementedError('Zcash z-addresses do not support pubhash2addr()')
		else:
			raise ValueError(f'{hash_len}: incorrect pubkey_hash length')

class testnet(mainnet):
	wif_ver_num  = { 'std': 'ef', 'zcash_z': 'ac08' }
	addr_ver_bytes = { '1d25': 'p2pkh', '1cba': 'p2sh', '16b6': 'zcash_z', 'a8ac0c': 'viewkey' }
