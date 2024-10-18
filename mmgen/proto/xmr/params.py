#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.xmr.params: Monero protocol
"""

from collections import namedtuple

from ...protocol import CoinProtocol, _nw
from ...obj import HexStr

parsed_addr = namedtuple('parsed_addr', ['ver_bytes', 'data', 'payment_id'])

class MoneroViewKey(HexStr):
	color, width, hexcase = 'cyan', 64, 'lower' # FIXME - no checking performed

# https://github.com/monero-project/monero/blob/master/src/cryptonote_config.h
class mainnet(CoinProtocol.DummyWIF, CoinProtocol.Base):

	network_names  = _nw('mainnet', 'stagenet', None)
	base_proto     = 'Monero'
	base_proto_coin = 'XMR'
	base_coin      = 'XMR'
	addr_ver_info  = {'12': 'monero', '2a': 'monero_sub', '13': 'monero_integrated'}
	pubkey_types   = ('monero',)
	mmtypes        = ('M',)
	dfl_mmtype     = 'M'
	pubkey_type    = 'monero' # required by DummyWIF
	avg_bdi        = 120
	privkey_len    = 32
	mmcaps         = ('rpc',)
	ignore_daemon_version = False
	coin_amt       = 'XMRAmt'
	sign_mode      = 'standalone'

	def get_addr_len(self, addr_fmt):
		return (64, 72)[addr_fmt == 'monero_integrated']

	def preprocess_key(self, sec, pubkey_type): # reduce key
		from ...contrib.ed25519 import l
		return int.to_bytes(
			int.from_bytes(sec[::-1], 'big') % l,
			self.privkey_len,
			'big')[::-1]

	def decode_addr(self, addr):

		from ...baseconv import baseconv

		def b58dec(addr_str):
			bc = baseconv('b58')
			l = len(addr_str)
			a = b''.join([bc.tobytes(addr_str[i*11:i*11+11], pad=8) for i in range(l//11)])
			b = bc.tobytes(addr_str[-(l%11):], pad=5)
			return a + b

		ret = b58dec(addr)

		chk = self.keccak_256(ret[:-4]).digest()[:4]

		assert ret[-4:] == chk, f'{ret[-4:].hex()}: incorrect checksum.  Correct value: {chk.hex()}'

		return self.decode_addr_bytes(ret[:-4])

	def parse_addr(self, ver_bytes, addr_bytes, fmt):
		addr_len = self.get_addr_len('monero')
		return parsed_addr(
			ver_bytes  = ver_bytes,
			data       = addr_bytes[:addr_len],
			payment_id = addr_bytes[addr_len:] if fmt == 'monero_integrated' else None,
		)

	def pubhash2addr(self, *args, **kwargs):
		raise NotImplementedError('Monero addresses do not support pubhash2addr()')

	def viewkey(self, viewkey_str):
		return MoneroViewKey.__new__(MoneroViewKey, viewkey_str)

class testnet(mainnet): # use stagenet for testnet
	# testnet is {'35', '3f', '36'}
	addr_ver_info = {'18': 'monero', '24': 'monero_sub', '19': 'monero_integrated'}
