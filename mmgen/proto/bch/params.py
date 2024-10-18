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
proto.bch.params: Bitcoin Cash protocol
"""

from ...protocol import decoded_addr_multiview
from ...addr import CoinAddr
from ..btc.params import mainnet, _finfo
from ..btc.common import b58chk_decode, b58chk_encode
from .cashaddr import cashaddr_decode_addr, cashaddr_encode_addr, cashaddr_addr_types

class mainnet(mainnet):
	is_fork_of      = 'Bitcoin'
	mmtypes         = ('L', 'C')
	sighash_type    = 'ALL|FORKID'
	forks = [
		_finfo(478559, '000000000000000000651ef99cb9fcbe0dadde1d424bd9f15ff20136191a5eec', 'BTC', False)
	]
	caps = ()
	coin_amt        = 'BCHAmt'
	max_tx_fee      = '0.1'
	ignore_daemon_version = False
	cashaddr_pfx    = 'bitcoincash'
	cashaddr        = True

	def decode_addr(self, addr):
		if len(addr) >= 42: # cashaddr
			if addr.islower():
				pass
			elif addr.isupper():
				addr = addr.lower()
			else:
				raise ValueError(f'{addr}: address has mixed case!')
			if ':' in addr:
				assert addr.startswith(self.cashaddr_pfx), f'{addr}: address has invalid prefix!'
			else:
				addr = f'{self.cashaddr_pfx}:{addr}'
			dec = cashaddr_decode_addr(addr)
			ver_bytes = self.addr_fmt_to_ver_bytes[dec.addr_type]
			return decoded_addr_multiview(
				dec.bytes,
				ver_bytes,
				dec.addr_type,
				addr,
				[dec.payload, b58chk_encode(ver_bytes+dec.bytes)] if len(dec.bytes) == self.addr_len else
				[dec.payload],
				0)
		else:
			dec = self.decode_addr_bytes(b58chk_decode(addr))
			enc = cashaddr_encode_addr(
				cashaddr_addr_types[dec.fmt],
				len(dec.bytes),
				self.cashaddr_pfx,
				dec.bytes)
			return decoded_addr_multiview(*dec, enc.addr, [enc.payload, addr], 1)

	def pubhash2addr(self, pubhash, addr_type):
		return CoinAddr(
			self,
			cashaddr_encode_addr(
				cashaddr_addr_types[addr_type],
				len(pubhash),
				self.cashaddr_pfx,
				pubhash).addr
				if self.cfg.cashaddr else
			b58chk_encode(self.addr_fmt_to_ver_bytes[addr_type] + pubhash))

	def pubhash2redeem_script(self, pubhash):
		raise NotImplementedError

	def pubhash2segwitaddr(self, pubhash):
		raise NotImplementedError

class testnet(mainnet):
	addr_ver_info  = {'6f': 'p2pkh', 'c4': 'p2sh'}
	wif_ver_num    = {'std': 'ef'}
	cashaddr_pfx   = 'bchtest'

class regtest(testnet):
	halving_interval = 150
	cashaddr_pfx     = 'bchreg'
