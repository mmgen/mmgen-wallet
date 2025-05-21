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
proto.rune.params: THORChain protocol
"""

from ...protocol import CoinProtocol, decoded_addr, _nw
from ...addr import CoinAddr
from ...contrib import bech32

from ..btc.params import mainnet as btc_mainnet

class mainnet(CoinProtocol.Secp256k1):
	mod_clsname     = 'THORChain'
	network_names   = _nw('mainnet', 'stagenet', 'testnet')
	mmtypes         = ('X',)
	preferred_mmtypes  = ('X',)
	dfl_mmtype      = 'X'
	coin_amt        = 'UniAmt'
	max_tx_fee      = 1 # TODO
	caps            = ()
	mmcaps          = ()
	base_proto      = 'THORChain'
	base_proto_coin = 'RUNE'
	base_coin       = 'RUNE'
	bech32_hrp      = 'thor'
	sign_mode       = 'standalone'
	avg_bdi         = 6 # TODO
	address_reuse_ok = False

	wif_ver_num = btc_mainnet.wif_ver_num
	coin_cfg_opts = btc_mainnet.coin_cfg_opts
	encode_wif = btc_mainnet.encode_wif
	decode_wif = btc_mainnet.decode_wif

	def decode_addr(self, addr):
		hrp, data = bech32.bech32_decode(addr)
		assert hrp == self.bech32_hrp, f'{hrp!r}: invalid bech32 hrp (should be {self.bech32_hrp!r})'
		return decoded_addr(
			bytes(bech32.convertbits(data, 5, 8)),
			None,
			'bech32') if data else False

	def encode_addr_bech32x(self, pubhash):
		return CoinAddr(
			self,
			bech32.bech32_encode(
				hrp  = self.bech32_hrp,
				data = bech32.convertbits(list(pubhash), 8, 5)))

class stagenet(mainnet):
	bech32_hrp = 'sthor'

class testnet(stagenet): # testnet is deprecated
	bech32_hrp = 'tthor'
