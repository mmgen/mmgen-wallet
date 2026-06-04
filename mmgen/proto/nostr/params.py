#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.nostr.params: Nostr protocol
"""

from ...protocol import CoinProtocol, decoded_wif, decoded_addr, _nw
from ...addr import CoinAddr
from ...contrib import bech32

class mainnet(CoinProtocol.Secp256k1):
	mod_clsname     = 'Nostr'
	network_names   = _nw('mainnet', None, None)
	mmtypes         = ('K',)
	dfl_mmtype      = 'K'
	base_proto      = 'Nostr'
	base_proto_coin = 'NOSTR'
	base_coin       = 'NOSTR'
	bech32_hrp      = 'npub'
	bech32_hrp_prv  = 'nsec'

	def encode_wif(self, privbytes, pubkey_type, *, compressed): # input is preprocessed
		return bech32.bech32_encode(
			hrp  = self.bech32_hrp_prv,
			data = bech32.convertbits(privbytes, 8, 5))

	def decode_wif(self, wif):
		hrp, data = bech32.bech32_decode(wif)
		assert hrp == self.bech32_hrp_prv, f'Bech32 HRP does not match! ({hrp} != {self.bech32_hrp_prv})'
		return decoded_wif(
			sec         = bytes(bech32.convertbits(data, 5, 8, False)),
			pubkey_type = None,
			compressed  = True) if data else False

	def decode_addr(self, addr):
		hrp, data = bech32.bech32_decode(addr)
		assert hrp == self.bech32_hrp, f'Bech32 HRP does not match! ({hrp} != {self.bech32_hrp})'
		return decoded_addr(
			bytes(bech32.convertbits(data, 5, 8, False)),
			ver_bytes = None,
			fmt = 'bech32pk') if data else False

	def encode_addr_bech32pk(self, pubkey):
		match len(pubkey):
			case 33:
				assert pubkey[0] in (2, 3), f'{pubkey[0]}: invalid first byte for {self.name} protocol public key'
			case 32:
				pass
			case x:
				raise ValueError(f'{x}: invalid public key length for {self.name} protocol')
		return CoinAddr(
			self,
			bech32.bech32_encode(
				hrp  = self.bech32_hrp,
				data = bech32.convertbits(pubkey[-32:], 8, 5)))
