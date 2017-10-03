#!/usr/bin/env python
#
# MMGen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2017 Philemon <mmgen-py@yandex.com>
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
protocol.py: Coin protocol functions, classes and methods
"""

import os,hashlib
from binascii import unhexlify
from mmgen.util import msg,pmsg

def hash160(hexnum): # take hex, return hex - OP_HASH160
	return hashlib.new('ripemd160',hashlib.sha256(unhexlify(hexnum)).digest()).hexdigest()

def hash256(hexnum): # take hex, return hex - OP_HASH256
	return hashlib.sha256(hashlib.sha256(unhexlify(hexnum)).digest()).hexdigest()

# From en.bitcoin.it:
#  The Base58 encoding used is home made, and has some differences.
#  Especially, leading zeroes are kept as single zeroes when conversion happens.
# Test: 5JbQQTs3cnoYN9vDYaGY6nhQ1DggVsY4FJNBUfEfpSQqrEp3srk
# The 'zero address':
# 1111111111111111111114oLvT2 (pubkeyhash = '\0'*20)
_b58a='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def _numtob58(num):
	ret = []
	while num:
		ret.append(_b58a[num % 58])
		num /= 58
	return ''.join(ret)[::-1]

def _b58tonum(b58num):
	b58num = b58num.strip()
	for i in b58num:
		if not i in _b58a: return False
	return sum(_b58a.index(n) * (58**i) for i,n in enumerate(list(b58num[::-1])))

def get_coin_protocol(coin,testnet):
	coin = coin.lower()
	coins = {
		'btc': (BitcoinProtocol,BitcoinTestnetProtocol),
		'bch': (BitcoinCashProtocol,BitcoinCashTestnetProtocol),
		'ltc': (LitecoinProtocol,LitecoinTestnetProtocol),
		'eth': (EthereumProtocol,EthereumTestnetProtocol),
	}
	assert type(testnet) == bool
	assert coin in coins
	return coins[coin][testnet]

from mmgen.obj import MMGenObject
from mmgen.globalvars import g

class BitcoinProtocol(MMGenObject):
	# devdoc/ref_transactions.md:
	addr_ver_num         = { 'p2pkh': ('00','1'), 'p2sh':  ('05','3') }
	addr_pfxs            = '13'
	uncompressed_wif_pfx = '5'
	privkey_pfx          = '80'
	mmtypes              = ('L','C','S')
	data_subdir          = ''
	rpc_port             = 8332
	daemon_data_dir = os.path.join(os.getenv('APPDATA'),'Bitcoin') if g.platform == 'win' \
						else os.path.join(g.home_dir,'.bitcoin')
	sighash_type = 'ALL'
	block0 = '000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f'
	forks = [
		(478559,'00000000000000000019f112ec0a9982926f1258cdcc558dd7c3b7e5dc7fa148','bch')
	]

	@classmethod
	def get_chain_protocol(cls,chain):
		chain_protos = { 'mainnet':'', 'testnet':'Testnet', 'regtest':'Testnet' }
		assert chain in chain_protos
		return globals()['Bitcoin{}Protocol'.format(chain_protos[chain])]

	@classmethod
	def hex2wif(cls,hexpriv,compressed=False):
		s = cls.privkey_pfx + hexpriv + ('','01')[bool(compressed)]
		return _numtob58(int(s+hash256(s)[:8],16))

	@classmethod
	def wif2hex(cls,wif):
		num = _b58tonum(wif)
		if num == False: return False
		key = '{:x}'.format(num)
		compressed = wif[0] != cls.uncompressed_wif_pfx
		klen = (66,68)[bool(compressed)]
		if compressed and key[66:68] != '01': return False
		if (key[:2] == cls.privkey_pfx and key[klen:] == hash256(key[:klen])[:8]):
			return { 'hex':key[2:66], 'compressed':compressed }
		else:
			return False

	@classmethod
	def verify_addr(cls,addr,verbose=False,return_dict=False):
		for addr_fmt in ('p2pkh','p2sh'):
			ver_num,ldigit = cls.addr_ver_num[addr_fmt]
			if addr[0] not in ldigit: continue
			num = _b58tonum(addr)
			if num == False: break
			addr_hex = '{:050x}'.format(num)
			if addr_hex[:2] != ver_num: continue
			if hash256(addr_hex[:42])[:8] == addr_hex[42:]:
				return { 'hex':addr_hex[2:42], 'format':addr_fmt } if return_dict else True
			else:
				if verbose: Msg("Invalid checksum in address '{}'".format(addr))
				break
		if verbose: Msg("Invalid address '{}'".format(addr))
		return False

	@classmethod
	def hexaddr2addr(cls,hexaddr,p2sh=False):
		s = cls.addr_ver_num[('p2pkh','p2sh')[p2sh]][0] + hexaddr
		lzeroes = (len(s) - len(s.lstrip('0'))) / 2
		return ('1' * lzeroes) + _numtob58(int(s+hash256(s)[:8],16))

	# Segwit:
	@classmethod
	def pubhex2redeem_script(cls,pubhex):
		# https://bitcoincore.org/en/segwit_wallet_dev/
		# The P2SH redeemScript is always 22 bytes. It starts with a OP_0, followed
		# by a canonical push of the keyhash (i.e. 0x0014{20-byte keyhash})
		return '0014' + hash160(pubhex)

	@classmethod
	def pubhex2segwitaddr(cls,pubhex):
		return cls.hexaddr2addr(hash160(cls.pubhex2redeem_script(pubhex)),p2sh=True)

class BitcoinTestnetProtocol(BitcoinProtocol):
	addr_ver_num         = { 'p2pkh': ('6f','mn'), 'p2sh':  ('c4','2') }
	addr_pfxs            = 'mn2'
	uncompressed_wif_pfx = '9'
	privkey_pfx          = 'ef'
	data_subdir          = 'testnet3'
	rpc_port             = 18332

class BitcoinCashProtocol(BitcoinProtocol):
	# TODO: assumes MSWin user installs in custom dir 'Bitcoin_ABC'
	daemon_data_dir = os.path.join(os.getenv('APPDATA'),'Bitcoin_ABC') if g.platform == 'win' \
						else os.path.join(g.home_dir,'.bitcoin-abc')
	rpc_port     = 8442
	mmtypes      = ('L','C')
	sighash_type = 'ALL|FORKID'
	block0 = '000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f'
	forks = [
		(478559,'000000000000000000651ef99cb9fcbe0dadde1d424bd9f15ff20136191a5eec','btc')
	]

	@classmethod
	def pubhex2redeem_script(cls,pubhex): raise NotImplementedError
	@classmethod
	def pubhex2segwitaddr(cls,pubhex):    raise NotImplementedError

class BitcoinCashTestnetProtocol(BitcoinTestnetProtocol):
	rpc_port = 18442
	@classmethod
	def pubhex2redeem_script(cls,pubhex): raise NotImplementedError
	@classmethod
	def pubhex2segwitaddr(cls,pubhex):    raise NotImplementedError

class LitecoinProtocol(BitcoinProtocol): pass
class LitecoinTestnetProtocol(LitecoinProtocol): pass

class EthereumProtocol(MMGenObject): pass
class EthereumTestnetProtocol(EthereumProtocol): pass
