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
Monero protocol
"""

from ..protocol import CoinProtocol,_nw

# https://github.com/monero-project/monero/blob/master/src/cryptonote_config.h
class mainnet(CoinProtocol.DummyWIF,CoinProtocol.Base):

	network_names  = _nw('mainnet','stagenet',None)
	base_coin      = 'XMR'
	base_proto     = 'Monero'
	addr_ver_bytes = { '12': 'monero', '2a': 'monero_sub' }
	addr_len       = 68
	wif_ver_num    = {}
	pubkey_types   = ('monero',)
	mmtypes        = ('M',)
	dfl_mmtype     = 'M'
	pubkey_type    = 'monero' # required by DummyWIF
	avg_bdi        = 120
	privkey_len    = 32
	mmcaps         = ('key','addr')
	ignore_daemon_version = False
	coin_amt       = 'XMRAmt'

	def preprocess_key(self,sec,pubkey_type): # reduce key
		from ..contrib.ed25519 import l
		return int.to_bytes(
			int.from_bytes( sec[::-1], 'big' ) % l,
			self.privkey_len,
			'big' )[::-1]

	def parse_addr(self,addr):

		from ..baseconv import baseconv

		def b58dec(addr_str):
			bc = baseconv('b58')
			l = len(addr_str)
			a = b''.join([bc.tobytes( addr_str[i*11:i*11+11], pad=8 ) for i in range(l//11)])
			b = bc.tobytes( addr_str[-(l%11):], pad=5 )
			return a + b

		ret = b58dec(addr)

		chk = self.keccak_256(ret[:-4]).digest()[:4]

		assert ret[-4:] == chk, f'{ret[-4:].hex()}: incorrect checksum.  Correct value: {chk.hex()}'

		return self.parse_addr_bytes(ret)

	def pubhash2addr(self,*args,**kwargs):
		raise NotImplementedError('Monero addresses do not support pubhash2addr()')

class testnet(mainnet): # use stagenet for testnet
	addr_ver_bytes = { '18': 'monero', '24': 'monero_sub' } # testnet is ('35','3f')
