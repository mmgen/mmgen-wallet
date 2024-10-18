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
proto.btc.params: Bitcoin protocol
"""

from ...protocol import CoinProtocol, decoded_wif, decoded_addr, _finfo, _nw
from ...addr import CoinAddr
from .common import b58chk_decode, b58chk_encode, hash160

class mainnet(CoinProtocol.Secp256k1): # chainparams.cpp
	"""
	All Bitcoin code and chain forks inherit from this class
	"""
	mod_clsname     = 'Bitcoin'
	network_names   = _nw('mainnet', 'testnet', 'regtest')
	addr_ver_info   = {'00': 'p2pkh', '05': 'p2sh'}
	addr_len        = 20
	wif_ver_num     = {'std': '80'}
	mmtypes         = ('L', 'C', 'S', 'B')
	dfl_mmtype      = 'L'
	coin_amt        = 'BTCAmt'
	max_tx_fee      = '0.003'
	sighash_type    = 'ALL'
	block0          = '000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f'
	forks           = [
		_finfo(478559, '00000000000000000019f112ec0a9982926f1258cdcc558dd7c3b7e5dc7fa148', 'BCH', False),
	]
	caps            = ('rbf', 'segwit')
	mmcaps          = ('rpc', 'rpc_init', 'tw', 'msg')
	base_proto      = 'Bitcoin'
	base_proto_coin = 'BTC'
	base_coin       = 'BTC'
	# From BIP173: witness version 'n' is stored as 'OP_n'. OP_0 is encoded as 0x00,
	# but OP_1 through OP_16 are encoded as 0x51 though 0x60 (81 to 96 in decimal).
	witness_vernum_hex = '00'
	witness_vernum  = int(witness_vernum_hex, 16)
	bech32_hrp      = 'bc'
	sign_mode       = 'daemon'
	avg_bdi         = int(9.7 * 60) # average block discovery interval (historical)
	halving_interval = 210000
	diff_adjust_interval = 2016
	max_halvings    = 64
	start_subsidy   = 50
	ignore_daemon_version = False
	max_int         = 0xffffffff

	def encode_wif(self, privbytes, pubkey_type, compressed): # input is preprocessed hex
		assert len(privbytes) == self.privkey_len, f'{len(privbytes)} bytes: incorrect private key length!'
		assert pubkey_type in self.wif_ver_bytes, f'{pubkey_type!r}: invalid pubkey_type'
		return b58chk_encode(
			self.wif_ver_bytes[pubkey_type]
			+ privbytes
			+ (b'', b'\x01')[bool(compressed)])

	def decode_wif(self, wif):
		key_data = b58chk_decode(wif)
		vlen = self.wif_ver_bytes_len or self.get_wif_ver_bytes_len(key_data)
		key = key_data[vlen:]

		if len(key) == self.privkey_len + 1:
			assert key[-1] == 0x01, f'{key[-1]!r}: invalid compressed key suffix byte'
		elif len(key) != self.privkey_len:
			raise ValueError(f'{len(key)}: invalid key length')

		return decoded_wif(
			sec         = key[:self.privkey_len],
			pubkey_type = self.wif_ver_bytes_to_pubkey_type[key_data[:vlen]],
			compressed  = len(key) == self.privkey_len + 1)

	def decode_addr(self, addr):

		if 'B' in self.mmtypes and addr[:len(self.bech32_hrp)] == self.bech32_hrp:
			from ...contrib import bech32
			ret = bech32.decode(self.bech32_hrp, addr)

			if ret[0] != self.witness_vernum:
				from ...util import msg
				msg(f'{ret[0]}: Invalid witness version number')
				return False

			return decoded_addr(bytes(ret[1]), None, 'bech32') if ret[1] else False

		return self.decode_addr_bytes(b58chk_decode(addr))

	def pubhash2addr(self, pubhash, addr_type):
		assert len(pubhash) == self.addr_len, f'{len(pubhash)}: invalid length for pubkey hash'
		return CoinAddr(
			self,
			b58chk_encode(self.addr_fmt_to_ver_bytes[addr_type] + pubhash))

	# Segwit:
	def pubhash2redeem_script(self, pubhash):
		# https://bitcoincore.org/en/segwit_wallet_dev/
		# The P2SH redeemScript is always 22 bytes. It starts with a OP_0, followed
		# by a canonical push of the keyhash (i.e. 0x0014{20-byte keyhash})
		return bytes.fromhex(self.witness_vernum_hex + '14') + pubhash

	def pubhash2segwitaddr(self, pubhash):
		return CoinAddr(
			self,
			self.pubhash2addr(hash160(self.pubhash2redeem_script(pubhash)), 'p2sh'))

	def pubhash2bech32addr(self, pubhash):
		from ...contrib import bech32
		return CoinAddr(
			self,
			bech32.bech32_encode(
				hrp  = self.bech32_hrp,
				data = [self.witness_vernum] + bech32.convertbits(list(pubhash), 8, 5)))

class testnet(mainnet):
	addr_ver_info       = {'6f': 'p2pkh', 'c4': 'p2sh'}
	wif_ver_num         = {'std': 'ef'}
	bech32_hrp          = 'tb'

class regtest(testnet):
	bech32_hrp          = 'bcrt'
	halving_interval    = 150
