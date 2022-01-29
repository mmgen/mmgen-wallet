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
Bitcoin protocol
"""

from ..protocol import CoinProtocol,parsed_wif,parsed_addr,_finfo,_b58a,_nw
import hashlib

def hash160(in_bytes): # OP_HASH160
	return hashlib.new('ripemd160',hashlib.sha256(in_bytes).digest()).digest()

def hash256(in_bytes): # OP_HASH256
	return hashlib.sha256(hashlib.sha256(in_bytes).digest()).digest()

# From en.bitcoin.it:
#  The Base58 encoding used is home made, and has some differences.
#  Especially, leading zeroes are kept as single zeroes when conversion happens.
# Test: 5JbQQTs3cnoYN9vDYaGY6nhQ1DggVsY4FJNBUfEfpSQqrEp3srk
# The 'zero address':
# 1111111111111111111114oLvT2 (pubkeyhash = '\0'*20)

def _b58chk_encode(in_bytes):
	lzeroes = len(in_bytes) - len(in_bytes.lstrip(b'\x00'))
	def do_enc(n):
		while n:
			yield _b58a[n % 58]
			n //= 58
	return ('1' * lzeroes) + ''.join(do_enc(int.from_bytes(in_bytes+hash256(in_bytes)[:4],'big')))[::-1]

def _b58chk_decode(s):
	lzeroes = len(s) - len(s.lstrip('1'))
	res = sum(_b58a.index(ch) * 58**n for n,ch in enumerate(s[::-1]))
	bl = res.bit_length()
	out = b'\x00' * lzeroes + res.to_bytes(bl//8 + bool(bl%8),'big')
	if out[-4:] != hash256(out[:-4])[:4]:
		raise ValueError('_b58chk_decode(): incorrect checksum')
	return out[:-4]

class mainnet(CoinProtocol.Secp256k1): # chainparams.cpp
	"""
	All Bitcoin code and chain forks inherit from this class
	"""
	mod_clsname     = 'Bitcoin'
	network_names   = _nw('mainnet','testnet','regtest')
	addr_ver_bytes  = { '00': 'p2pkh', '05': 'p2sh' }
	addr_len        = 20
	wif_ver_num     = { 'std': '80' }
	mmtypes         = ('L','C','S','B')
	dfl_mmtype      = 'L'
	coin_amt        = 'BTCAmt'
	max_tx_fee      = '0.003'
	sighash_type    = 'ALL'
	block0          = '000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f'
	forks           = [
		_finfo(478559,'00000000000000000019f112ec0a9982926f1258cdcc558dd7c3b7e5dc7fa148','BCH',False),
	]
	caps            = ('rbf','segwit')
	mmcaps          = ('key','addr','rpc','tx')
	base_coin       = 'BTC'
	base_proto      = 'Bitcoin'
	# From BIP173: witness version 'n' is stored as 'OP_n'. OP_0 is encoded as 0x00,
	# but OP_1 through OP_16 are encoded as 0x51 though 0x60 (81 to 96 in decimal).
	witness_vernum_hex = '00'
	witness_vernum  = int(witness_vernum_hex,16)
	bech32_hrp      = 'bc'
	sign_mode       = 'daemon'
	avg_bdi         = int(9.7 * 60) # average block discovery interval (historical)
	halving_interval = 210000
	max_halvings    = 64
	start_subsidy   = 50
	ignore_daemon_version = False
	max_int         = 0xffffffff

	def bytes2wif(self,privbytes,pubkey_type,compressed): # input is preprocessed hex
		assert len(privbytes) == self.privkey_len, f'{len(privbytes)} bytes: incorrect private key length!'
		assert pubkey_type in self.wif_ver_num, f'{pubkey_type!r}: invalid pubkey_type'
		return _b58chk_encode(
			bytes.fromhex(self.wif_ver_num[pubkey_type])
			+ privbytes
			+ (b'',b'\x01')[bool(compressed)])

	def parse_wif(self,wif):
		key = _b58chk_decode(wif)

		for k,v in self.wif_ver_num.items():
			v = bytes.fromhex(v)
			if key[:len(v)] == v:
				pubkey_type = k
				key = key[len(v):]
				break
		else:
			raise ValueError('Invalid WIF version number')

		if len(key) == self.privkey_len + 1:
			assert key[-1] == 0x01, f'{key[-1]!r}: invalid compressed key suffix byte'
			compressed = True
		elif len(key) == self.privkey_len:
			compressed = False
		else:
			raise ValueError(f'{len(key)}: invalid key length')

		return parsed_wif(
			sec         = key[:self.privkey_len],
			pubkey_type = pubkey_type,
			compressed  = compressed )

	def parse_addr(self,addr):

		if 'B' in self.mmtypes and addr[:len(self.bech32_hrp)] == self.bech32_hrp:
			import mmgen.bech32 as bech32
			ret = bech32.decode(self.bech32_hrp,addr)

			if ret[0] != self.witness_vernum:
				from ..util import msg
				msg(f'{ret[0]}: Invalid witness version number')
				return False

			return parsed_addr( bytes(ret[1]), 'bech32' ) if ret[1] else False

		return self.parse_addr_bytes(_b58chk_decode(addr))

	def pubhash2addr(self,pubkey_hash,p2sh):
		assert len(pubkey_hash) == 20, f'{len(pubkey_hash)}: invalid length for pubkey hash'
		return _b58chk_encode(
			self.addr_fmt_to_ver_bytes(('p2pkh','p2sh')[p2sh],return_hex=False) + pubkey_hash
		)

	# Segwit:
	def pubkey2redeem_script(self,pubkey):
		# https://bitcoincore.org/en/segwit_wallet_dev/
		# The P2SH redeemScript is always 22 bytes. It starts with a OP_0, followed
		# by a canonical push of the keyhash (i.e. 0x0014{20-byte keyhash})
		return bytes.fromhex(self.witness_vernum_hex + '14') + hash160(pubkey)

	def pubkey2segwitaddr(self,pubkey):
		return self.pubhash2addr(
			hash160( self.pubkey2redeem_script(pubkey)), p2sh=True )

	def pubhash2bech32addr(self,pubhash):
		d = list(pubhash)
		import mmgen.bech32 as bech32
		return bech32.bech32_encode(self.bech32_hrp,[self.witness_vernum]+bech32.convertbits(d,8,5))

class testnet(mainnet):
	addr_ver_bytes      = { '6f': 'p2pkh', 'c4': 'p2sh' }
	wif_ver_num         = { 'std': 'ef' }
	bech32_hrp          = 'tb'

class regtest(testnet):
	bech32_hrp          = 'bcrt'
	halving_interval    = 150
