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
from mmgen.util import msg,pmsg,Msg
from mmgen.obj import MMGenObject,BTCAmt,LTCAmt,BCHAmt,B2XAmt
from mmgen.globalvars import g

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
		if not i in _b58a:
			raise ValueError,'_b58tonum(): invalid b58 value'
	return sum(_b58a.index(n) * (58**i) for i,n in enumerate(list(b58num[::-1])))

def _b58chk_encode(hexstr):
	return _numtob58(int(hexstr+hash256(hexstr)[:8],16))

def _b58chk_decode(s):
	hexstr = '{:x}'.format(_b58tonum(s))
	if hexstr[-8:] == hash256(hexstr[:-8])[:8]:
		return hexstr[:-8]
	raise ValueError,'_b58chk_decode(): checksum incorrect'

# chainparams.cpp
class BitcoinProtocol(MMGenObject):
	name            = 'bitcoin'
	daemon_name     = 'bitcoind'
	addr_ver_num    = { 'p2pkh': ('00','1'), 'p2sh':  ('05','3') }
	wif_ver_num     = { 'std': '80' }
	mmtypes         = ('L','C','S')
	dfl_mmtype      = 'L'
	data_subdir     = ''
	rpc_port        = 8332
	secs_per_block  = 600
	coin_amt        = BTCAmt
	max_tx_fee      = BTCAmt('0.003')
	daemon_data_dir = os.path.join(os.getenv('APPDATA'),'Bitcoin') if g.platform == 'win' \
						else os.path.join(g.home_dir,'.bitcoin')
	daemon_data_subdir = ''
	sighash_type = 'ALL'
	block0 = '000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f'
	forks = [ # height, hash, name, replayable
		(478559,'00000000000000000019f112ec0a9982926f1258cdcc558dd7c3b7e5dc7fa148','bch',False),
		(None,'','b2x',True)
	]
	caps = ('rbf','segwit')
	mmcaps = ('key','addr','rpc')
	base_coin = 'BTC'
	addr_width = 34

	@staticmethod
	def get_protocol_by_chain(chain):
		return CoinProtocol(g.coin,{'mainnet':False,'testnet':True,'regtest':True}[chain])

	@staticmethod
	def get_rpc_coin_amt_type():
		return (float,str)[g.daemon_version>=120000]

	@classmethod
	def cap(cls,s): return s in cls.caps

	@classmethod
	def preprocess_key(cls,hexpriv,pubkey_type): return hexpriv

	@classmethod
	def hex2wif(cls,hexpriv,pubkey_type,compressed):
		return _b58chk_encode(cls.wif_ver_num[pubkey_type] + hexpriv + ('','01')[bool(compressed)])

	@classmethod
	def wif2hex(cls,wif):
		key = _b58chk_decode(wif)
		pubkey_type = None
		for k,v in cls.wif_ver_num.items():
			if key[:len(v)] == v:
				pubkey_type = k
				key = key[len(v):]
		assert pubkey_type,'invalid WIF version number'
		if len(key) == 66:
			assert key[-2:] == '01','invalid compressed key suffix'
			compressed = True
		else:
			assert len(key) == 64,'invalid key length'
			compressed = False
		return { 'hex':key[:64], 'pubkey_type':pubkey_type, 'compressed':compressed }

	@classmethod
	def wif2hex_old(cls,wif):
		num = _b58tonum(wif)
		if num == False: return False
		key = '{:x}'.format(num)
		if len(key) not in (74,76): return False
		compressed = len(key) == 76
		if compressed and key[66:68] != '01': return False
		klen = (66,68)[compressed]
		if (key[:2] == cls.wif_ver_num['std'] and key[klen:] == hash256(key[:klen])[:8]):
			return { 'hex':key[2:66], 'compressed':compressed }
		else:
			return False

	@classmethod
	def verify_addr(cls,addr,return_dict=False):
		for addr_fmt in cls.addr_ver_num:
			ver_num,pfx = cls.addr_ver_num[addr_fmt]
			if type(pfx) == tuple:
				if addr[0] not in pfx: continue
			elif addr[:len(pfx)] != pfx: continue
			num = _b58tonum(addr)
			if num == False:
				if g.debug: Msg('Address cannot be converted to base 58')
				break
			addr_hex = '{:0{}x}'.format(num,48+len(ver_num))
			if addr_hex[:len(ver_num)] != ver_num: continue
			if hash256(addr_hex[:-8])[:8] == addr_hex[-8:]:
				return {
					'hex': addr_hex[len(ver_num):-8],
					'format': {'p2pkh':'p2pkh','p2sh':'p2sh','p2sh2':'p2sh','zcash_z':'zcash_z'}[addr_fmt],
					'width': cls.addr_width
				} if return_dict else True
			else:
				if g.debug: Msg('Invalid checksum in address')
				break
		if g.debug: Msg("Invalid address '{}'".format(addr))
		return False

	@classmethod
	def pubhash2addr(cls,pubkey_hash,p2sh):
		s = cls.addr_ver_num[('p2pkh','p2sh')[p2sh]][0] + pubkey_hash
		lzeroes = (len(s) - len(s.lstrip('0'))) / 2 # non-zero only for ver num '00' (BTC p2pkh)
		return ('1' * lzeroes) + _b58chk_encode(s)

	# Segwit:
	@classmethod
	def pubhex2redeem_script(cls,pubhex):
		# https://bitcoincore.org/en/segwit_wallet_dev/
		# The P2SH redeemScript is always 22 bytes. It starts with a OP_0, followed
		# by a canonical push of the keyhash (i.e. 0x0014{20-byte keyhash})
		return '0014' + hash160(pubhex)

	@classmethod
	def pubhex2segwitaddr(cls,pubhex):
		return cls.pubhash2addr(hash160(cls.pubhex2redeem_script(pubhex)),p2sh=True)

class BitcoinTestnetProtocol(BitcoinProtocol):
	addr_ver_num         = { 'p2pkh': ('6f',('m','n')), 'p2sh':  ('c4','2') }
	wif_ver_num          = { 'std': 'ef' }
	data_subdir          = 'testnet'
	daemon_data_subdir   = 'testnet3'
	rpc_port             = 18332
	addr_width           = 35

class BitcoinCashProtocol(BitcoinProtocol):
	# TODO: assumes MSWin user installs in custom dir 'Bitcoin_ABC'
	daemon_name    = 'bitcoind-abc'
	daemon_data_dir = os.path.join(os.getenv('APPDATA'),'Bitcoin_ABC') if g.platform == 'win' \
						else os.path.join(g.home_dir,'.bitcoin-abc')
	rpc_port       = 8442
	mmtypes        = ('L','C')
	sighash_type   = 'ALL|FORKID'
	forks = [
		(478559,'000000000000000000651ef99cb9fcbe0dadde1d424bd9f15ff20136191a5eec','btc',False)
	]
	caps = ()
	coin_amt        = BCHAmt
	max_tx_fee      = BCHAmt('0.1')

	@classmethod
	def pubhex2redeem_script(cls,pubhex): raise NotImplementedError
	@classmethod
	def pubhex2segwitaddr(cls,pubhex):    raise NotImplementedError

class BitcoinCashTestnetProtocol(BitcoinCashProtocol):
	rpc_port      = 18442
	addr_ver_num  = { 'p2pkh': ('6f',('m','n')), 'p2sh':  ('c4','2') }
	wif_ver_num   = { 'std': 'ef' }
	data_subdir   = 'testnet'
	daemon_data_subdir = 'testnet3'
	addr_width     = 35

class B2XProtocol(BitcoinProtocol):
	daemon_name    = 'bitcoind-2x'
	daemon_data_dir = os.path.join(os.getenv('APPDATA'),'Bitcoin_2X') if g.platform == 'win' \
						else os.path.join(g.home_dir,'.bitcoin-2x')
	rpc_port        = 8338
	coin_amt        = B2XAmt
	max_tx_fee      = B2XAmt('0.1')
	forks = [
		(None,'','btc',True) # activation: 494784
	]

class B2XTestnetProtocol(B2XProtocol):
	addr_ver_num         = { 'p2pkh': ('6f',('m','n')), 'p2sh':  ('c4','2') }
	wif_ver_num          = { 'std': 'ef' }
	data_subdir          = 'testnet'
	daemon_data_subdir   = 'testnet5'
	rpc_port             = 18338
	addr_width     = 35

class LitecoinProtocol(BitcoinProtocol):
	block0         = '12a765e31ffd4059bada1e25190f6e98c99d9714d334efa41a195a7e7e04bfe2'
	name           = 'litecoin'
	daemon_name    = 'litecoind'
	daemon_data_dir = os.path.join(os.getenv('APPDATA'),'Litecoin') if g.platform == 'win' \
						else os.path.join(g.home_dir,'.litecoin')
	addr_ver_num   = { 'p2pkh': ('30','L'), 'p2sh':  ('32','M'), 'p2sh2':  ('05','3') } # 'p2sh' is new fmt
	wif_ver_num    = { 'std': 'b0' }
	secs_per_block = 150
	rpc_port       = 9332
	coin_amt       = LTCAmt
	max_tx_fee     = LTCAmt('0.3')
	base_coin      = 'LTC'
	forks          = []

class LitecoinTestnetProtocol(LitecoinProtocol):
	# addr ver nums same as Bitcoin testnet, except for 'p2sh'
	addr_ver_num   = { 'p2pkh': ('6f',('m','n')), 'p2sh':  ('3a','Q'), 'p2sh2':  ('c4','2') }
	wif_ver_num    = { 'std': 'ef' } # same as Bitcoin testnet
	data_subdir    = 'testnet'
	daemon_data_subdir = 'testnet4'
	rpc_port       = 19332
	addr_width     = 35

class BitcoinProtocolAddrgen(BitcoinProtocol): mmcaps = ('key','addr')
class BitcoinProtocolKeygen(BitcoinProtocol):  mmcaps = ('key',)
class BitcoinTestnetProtocolAddrgen(BitcoinTestnetProtocol): mmcaps = ('key','addr')
class BitcoinTestnetProtocolKeygen(BitcoinTestnetProtocol):  mmcaps = ('key',)

class EthereumProtocol(BitcoinProtocolAddrgen):

	addr_width = 40
	mmtypes    = ('E',)
	dfl_mmtype = 'E'
	name = 'ethereum'
	base_coin = 'ETH'

	@classmethod
	def hex2wif(cls,hexpriv,pubkey_type,compressed):
		assert compressed == False,'Ethereum does not support compressed pubkeys!'
		return str(hexpriv)

	@classmethod
	def wif2hex(cls,wif):
		return { 'hex':str(wif), 'pubkey_type':'std', 'compressed':False }

	@classmethod
	def verify_addr(cls,addr,return_dict=False):
		from mmgen.util import is_hex_str_lc
		if is_hex_str_lc(addr) and len(addr) == 40:
			return { 'hex': addr, 'format': 'ethereum', 'width': cls.addr_width } if return_dict else True
		if g.debug: Msg("Invalid address '{}'".format(addr))
		return False

class EthereumTestnetProtocol(EthereumProtocol): pass
class EthereumClassicProtocol(EthereumProtocol):
	name = 'ethereum_classic'
class EthereumClassicTestnetProtocol(EthereumClassicProtocol): pass

class ZcashProtocol(BitcoinProtocolAddrgen):
	name         = 'zcash'
	base_coin    = 'ZEC'
	addr_ver_num = { 'p2pkh': ('1cb8','t1'), 'p2sh':  ('1cbd','t3'), 'zcash_z': ('169a','zc') }
	wif_ver_num  = { 'std': '80', 'zcash_z': 'ab36' }
	mmtypes      = ('C','Z')
	dfl_mmtype   = 'C'

	@classmethod
	def preprocess_key(cls,hexpriv,pubkey_type): # zero the first four bits
		if pubkey_type == 'zcash_z':
			return '{:02x}'.format(int(hexpriv[:2],16) & 0x0f) + hexpriv[2:]
		else:
			return hexpriv

class ZcashTestnetProtocol(ZcashProtocol):
	wif_ver_num  = { 'std': '??', 'zcash_z': 'ac08' }
	addr_ver_num = { 'p2pkh': ('??','t1'), 'p2sh':  ('??','t3'), 'zcash_z': ('16b6','??') }

class DashProtocol(BitcoinProtocolAddrgen):
	name         = 'dash'
	base_coin    = 'DASH'
	addr_ver_num = { 'p2pkh': ('4c','X'), 'p2sh':  ('10','7') }
	wif_ver_num  = { 'std': 'cc' }
	mmtypes      = ('C',)
	dfl_mmtype   = 'C'

class DashTestnetProtocol(DashProtocol):
	# "Dash", "testnet", "tDASH", b'\xef', b'\x8c', b'\x13'
	addr_ver_num   = { 'p2pkh': ('8c','y'), 'p2sh':  ('13','?') }
	wif_ver_num    = { 'std': 'ef' }

class CoinProtocol(MMGenObject):
	coins = {
		'btc': (BitcoinProtocol,BitcoinTestnetProtocol),
		'bch': (BitcoinCashProtocol,BitcoinCashTestnetProtocol),
		'b2x': (B2XProtocol,B2XTestnetProtocol),
		'ltc': (LitecoinProtocol,LitecoinTestnetProtocol),
		'dash': (DashProtocol,DashTestnetProtocol),
		'zec': (ZcashProtocol,ZcashTestnetProtocol),
		'eth': (EthereumProtocol,EthereumTestnetProtocol),
		'etc': (EthereumClassicProtocol,EthereumClassicTestnetProtocol),
	}
	def __new__(cls,coin,testnet):
		coin = coin.lower()
		assert type(testnet) == bool
		if coin not in cls.coins:
			from mmgen.util import die
			die(1,"'{}': not a valid coin. Valid choices are '{}'".format(coin,"','".join(cls.coins)))
		return cls.coins[coin][testnet]

	@classmethod
	def get_base_coin_from_name(cls,name):
		for proto,foo in cls.coins.values():
			if name == proto.__name__[:-8].lower():
				return proto.base_coin
		return False
