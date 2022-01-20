#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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

import sys,os,hashlib
from collections import namedtuple

from .util import msg,ymsg,Msg,ydie
from .devtools import *
from .globalvars import g
from .amt import BTCAmt,LTCAmt,BCHAmt,XMRAmt
from .altcoins.eth.obj import ETHAmt
import mmgen.bech32 as bech32

parsed_wif = namedtuple('parsed_wif',['sec','pubkey_type','compressed'])
parsed_addr = namedtuple('parsed_addr',['bytes','fmt'])

def hash160(in_bytes): # OP_HASH160
	return hashlib.new('ripemd160',hashlib.sha256(in_bytes).digest()).digest()

def hash256(in_bytes): # OP_HASH256
	return hashlib.sha256(hashlib.sha256(in_bytes).digest()).digest()

_b58a='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

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

_finfo = namedtuple('fork_info',['height','hash','name','replayable'])
_nw = namedtuple('coin_networks',['mainnet','testnet','regtest'])

class CoinProtocol(MMGenObject):

	proto_info = namedtuple('proto_info',['name','trust_level']) # trust levels: see altcoin.py
	coins = {
		'btc': proto_info('Bitcoin',         5),
		'bch': proto_info('BitcoinCash',     5),
		'ltc': proto_info('Litecoin',        5),
		'eth': proto_info('Ethereum',        4),
		'etc': proto_info('EthereumClassic', 4),
		'zec': proto_info('Zcash',           2),
		'xmr': proto_info('Monero',          4)
	}
	core_coins = tuple(coins) # coins may be added by init_genonly_altcoins(), so save

	class Base(MMGenObject):
		base_proto = None
		is_fork_of = None
		networks   = ('mainnet','testnet','regtest')

		def __init__(self,coin,name,network,tokensym=None):
			self.coin       = coin.upper()
			self.coin_id    = self.coin
			self.name       = name
			self.network    = network
			self.tokensym   = tokensym
			self.cls_name   = type(self).__name__
			self.testnet    = network in ('testnet','regtest')
			self.regtest    = network == 'regtest'
			self.networks   = tuple(k for k,v in self.network_names._asdict().items() if v)
			self.network_id = coin.lower() + {
				'mainnet': '',
				'testnet': '_tn',
				'regtest': '_rt',
			}[network]

			if hasattr(self,'chain_names'):
				self.chain_name = self.chain_names[0] # first chain name is default
			else:
				self.chain_name = self.network
				self.chain_names = [self.network]

			if self.tokensym:
				assert isinstance(self,CoinProtocol.Ethereum), 'CoinProtocol.Base_chk1'

			if self.base_coin in ('ETH','XMR'):
				from .util import get_keccak
				self.keccak_256 = get_keccak()

		@property
		def dcoin(self):
			return self.coin

		@classmethod
		def chain_name_to_network(cls,coin,chain_name):
			"""
			The generic networks 'mainnet', 'testnet' and 'regtest' are required for all coins
			that support transaction operations.

			For protocols that have specific names for chains corresponding to these networks,
			the attribute 'chain_name' is used, while 'network' retains the generic name.
			For Bitcoin and Bitcoin forks, 'network' and 'chain_name' are equivalent.
			"""
			for network in ('mainnet','testnet','regtest'):
				proto = init_proto(coin,network=network)
				for proto_chain_name in proto.chain_names:
					if chain_name == proto_chain_name:
						return network
			raise ValueError(f'{chain_name}: unrecognized chain name for coin {coin}')

		@staticmethod
		def parse_network_id(network_id):
			nid = namedtuple('parsed_network_id',['coin','network'])
			if network_id.endswith('_tn'):
				return nid(network_id[:-3],'testnet')
			elif network_id.endswith('_rt'):
				return nid(network_id[:-3],'regtest')
			else:
				return nid(network_id,'mainnet')

		@staticmethod
		def create_network_id(coin,network):
			return coin.lower() + { 'mainnet':'', 'testnet':'_tn', 'regtest':'_rt' }[network]

		def cap(self,s):
			return s in self.caps

		def addr_fmt_to_ver_bytes(self,req_fmt,return_hex=False):
			for ver_hex,fmt in self.addr_ver_bytes.items():
				if req_fmt == fmt:
					return ver_hex if return_hex else bytes.fromhex(ver_hex)
			return False

		def get_addr_len(self,addr_fmt):
			return self.addr_len

		def parse_addr_bytes(self,addr_bytes):
			for ver_hex,addr_fmt in self.addr_ver_bytes.items():
				ver_bytes = bytes.fromhex(ver_hex)
				vlen = len(ver_bytes)
				if addr_bytes[:vlen] == ver_bytes:
					if len(addr_bytes[vlen:]) == self.get_addr_len(addr_fmt):
						return parsed_addr( addr_bytes[vlen:], addr_fmt )

			return False

		def coin_addr(self,addr):
			from .addr import CoinAddr
			return CoinAddr( proto=self, addr=addr )

		def addr_type(self,id_str):
			from .addr import MMGenAddrType
			return MMGenAddrType( proto=self, id_str=id_str )

	class Secp256k1(Base):
		"""
		Bitcoin and Ethereum protocols inherit from this class
		"""
		secp256k1_ge = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141
		privkey_len  = 32
		pubkey_types = ('std',)

		def preprocess_key(self,sec,pubkey_type):
			# Key must be non-zero and less than group order of secp256k1 curve
			if 0 < int.from_bytes(sec,'big') < self.secp256k1_ge:
				return sec
			else: # chance of this is less than 1 in 2^127
				pk = int.from_bytes(sec,'big')
				if pk == 0: # chance of this is 1 in 2^256
					ydie(3,'Private key is zero!')
				elif pk == self.secp256k1_ge: # ditto
					ydie(3,'Private key == secp256k1_ge!')
				else:
					if not g.test_suite:
						ymsg(f'Warning: private key is greater than secp256k1 group order!:\n  {hexpriv}')
					return (pk % self.secp256k1_ge).to_bytes(self.privkey_len,'big')

	class Bitcoin(Secp256k1): # chainparams.cpp
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
		coin_amt        = BTCAmt
		max_tx_fee      = BTCAmt('0.003')
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
				ret = bech32.decode(self.bech32_hrp,addr)

				if ret[0] != self.witness_vernum:
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
			return bech32.bech32_encode(self.bech32_hrp,[self.witness_vernum]+bech32.convertbits(d,8,5))

	class BitcoinTestnet(Bitcoin):
		addr_ver_bytes      = { '6f': 'p2pkh', 'c4': 'p2sh' }
		wif_ver_num         = { 'std': 'ef' }
		bech32_hrp          = 'tb'

	class BitcoinRegtest(BitcoinTestnet):
		bech32_hrp          = 'bcrt'
		halving_interval    = 150

	class BitcoinCash(Bitcoin):
		is_fork_of      = 'Bitcoin'
		mmtypes         = ('L','C')
		sighash_type    = 'ALL|FORKID'
		forks = [
			_finfo(478559,'000000000000000000651ef99cb9fcbe0dadde1d424bd9f15ff20136191a5eec','BTC',False)
		]
		caps = ()
		coin_amt        = BCHAmt
		max_tx_fee      = BCHAmt('0.1')
		ignore_daemon_version = False

		def pubkey2redeem_script(self,pubkey): raise NotImplementedError
		def pubkey2segwitaddr(self,pubkey):    raise NotImplementedError

	class BitcoinCashTestnet(BitcoinCash):
		addr_ver_bytes = { '6f': 'p2pkh', 'c4': 'p2sh' }
		wif_ver_num    = { 'std': 'ef' }

	class BitcoinCashRegtest(BitcoinCashTestnet):
		halving_interval = 150

	class Litecoin(Bitcoin):
		block0          = '12a765e31ffd4059bada1e25190f6e98c99d9714d334efa41a195a7e7e04bfe2'
		addr_ver_bytes  = { '30': 'p2pkh', '32': 'p2sh', '05': 'p2sh' } # new p2sh ver 0x32 must come first
		wif_ver_num     = { 'std': 'b0' }
		mmtypes         = ('L','C','S','B')
		coin_amt        = LTCAmt
		max_tx_fee      = LTCAmt('0.3')
		base_coin       = 'LTC'
		forks           = []
		bech32_hrp      = 'ltc'
		avg_bdi         = 150
		halving_interval = 840000
		ignore_daemon_version = False

	class LitecoinTestnet(Litecoin):
		# addr ver nums same as Bitcoin testnet, except for 'p2sh'
		addr_ver_bytes     = { '6f':'p2pkh', '3a':'p2sh', 'c4':'p2sh' }
		wif_ver_num        = { 'std': 'ef' } # same as Bitcoin testnet
		bech32_hrp         = 'tltc'

	class LitecoinRegtest(LitecoinTestnet):
		bech32_hrp         = 'rltc'
		halving_interval   = 150

	class DummyWIF:

		def bytes2wif(self,privbytes,pubkey_type,compressed):
			assert pubkey_type == self.pubkey_type, f'{pubkey_type}: invalid pubkey_type for {self.name} protocol!'
			assert compressed == False, f'{self.name} protocol does not support compressed pubkeys!'
			return privbytes.hex()

		def parse_wif(self,wif):
			return parsed_wif(
				sec         = bytes.fromhex(wif),
				pubkey_type = self.pubkey_type,
				compressed  = False )

	class Ethereum(DummyWIF,Secp256k1):

		network_names = _nw('mainnet','testnet','devnet')
		addr_len      = 20
		mmtypes       = ('E',)
		dfl_mmtype    = 'E'
		mod_clsname   = 'Ethereum'
		base_coin     = 'ETH'
		pubkey_type   = 'std' # required by DummyWIF

		coin_amt      = ETHAmt
		max_tx_fee    = ETHAmt('0.005')
		chain_names   = ['ethereum','foundation']
		sign_mode     = 'standalone'
		caps          = ('token',)
		mmcaps        = ('key','addr','rpc','tx')
		base_proto    = 'Ethereum'
		avg_bdi       = 15
		ignore_daemon_version = False

		chain_ids = {
			1:    'ethereum',         # ethereum mainnet
			2:    'morden',           # morden testnet (deprecated)
			3:    'ropsten',          # ropsten testnet
			4:    'rinkeby',          # rinkeby testnet
			5:    'goerli',           # goerli testnet
			42:   'kovan',            # kovan testnet
			61:   'classic',          # ethereum classic mainnet
			62:   'morden',           # ethereum classic testnet
			17:   'developmentchain', # parity dev chain
			1337: 'developmentchain', # geth dev chain
		}

		@property
		def dcoin(self):
			return self.tokensym or self.coin

		def parse_addr(self,addr):
			from .util import is_hex_str_lc
			if is_hex_str_lc(addr) and len(addr) == self.addr_len * 2:
				return parsed_addr( bytes.fromhex(addr), 'ethereum' )
			if g.debug:
				Msg(f'Invalid address: {addr}')
			return False

		@classmethod
		def checksummed_addr(cls,addr):
			h = self.keccak_256(addr.encode()).digest().hex()
			return ''.join(addr[i].upper() if int(h[i],16) > 7 else addr[i] for i in range(len(addr)))

		def pubhash2addr(self,pubkey_hash,p2sh):
			assert len(pubkey_hash) == 20, f'{len(pubkey_hash)}: invalid length for {self.name} pubkey hash'
			assert not p2sh, f'{self.name} protocol has no P2SH address format'
			return pubkey_hash.hex()

	class EthereumTestnet(Ethereum):
		chain_names = ['kovan','goerli','rinkeby']

	class EthereumRegtest(EthereumTestnet):
		chain_names = ['developmentchain']

	class EthereumClassic(Ethereum):
		chain_names = ['classic','ethereum_classic']
		max_tx_fee  = ETHAmt('0.005')
		ignore_daemon_version = False

	class EthereumClassicTestnet(EthereumClassic):
		chain_names = ['morden','morden_testnet','classic-testnet']

	class EthereumClassicRegtest(EthereumClassicTestnet):
		chain_names = ['developmentchain']

	class Zcash(Bitcoin):
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
			from .opts import opt
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

	class ZcashTestnet(Zcash):
		wif_ver_num  = { 'std': 'ef', 'zcash_z': 'ac08' }
		addr_ver_bytes = { '1d25': 'p2pkh', '1cba': 'p2sh', '16b6': 'zcash_z', 'a8ac0c': 'viewkey' }

	# https://github.com/monero-project/monero/blob/master/src/cryptonote_config.h
	class Monero(DummyWIF,Base):

		network_names  = _nw('mainnet','stagenet',None)
		base_coin      = 'XMR'
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
		coin_amt       = XMRAmt

		def preprocess_key(self,sec,pubkey_type): # reduce key
			from .ed25519 import l
			return int.to_bytes(
				int.from_bytes( sec[::-1], 'big' ) % l,
				self.privkey_len,
				'big' )[::-1]

		def parse_addr(self,addr):

			from .baseconv import baseconv,is_b58_str

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

	class MoneroTestnet(Monero): # use stagenet for testnet
		addr_ver_bytes = { '18': 'monero', '24': 'monero_sub' } # testnet is ('35','3f')

def init_proto(coin=None,testnet=False,regtest=False,network=None,network_id=None,tokensym=None):

	assert type(testnet) == bool, 'init_proto_chk1'
	assert type(regtest) == bool, 'init_proto_chk2'
	assert coin or network_id, 'init_proto_chk3'
	assert not (coin and network_id), 'init_proto_chk4'

	if network_id:
		coin,network = CoinProtocol.Base.parse_network_id(network_id)
	elif network:
		assert network in CoinProtocol.Base.networks, f'init_proto_chk5 - {network!r}: invalid network'
		assert testnet == False, 'init_proto_chk6'
		assert regtest == False, 'init_proto_chk7'
	else:
		network = 'regtest' if regtest else 'testnet' if testnet else 'mainnet'

	coin = coin.lower()
	if coin not in CoinProtocol.coins:
		raise ValueError(
			f'{coin.upper()}: not a valid coin for network {network.upper()}\n'
			+ 'Supported coins: '
			+ ' '.join(c.upper() for c in CoinProtocol.coins) )

	name = CoinProtocol.coins[coin].name
	proto_name = name + ('' if network == 'mainnet' else network.capitalize())

	return getattr(CoinProtocol,proto_name)(
		coin      = coin,
		name      = name,
		network   = network,
		tokensym  = tokensym )

def init_proto_from_opts():
	return init_proto(
		coin      = g.coin,
		testnet   = g.testnet,
		regtest   = g.regtest,
		tokensym  = g.token )

def init_genonly_altcoins(usr_coin=None,testnet=False):
	"""
	Initialize altcoin protocol class or classes for current network.
	If usr_coin is a core coin, initialization is skipped.
	If usr_coin has a trust level of -1, an exception is raised.
	If usr_coin is None, initializes all coins for current network with trust level >-1.
	Returns trust_level of usr_coin, or 0 (untrusted) if usr_coin is None.
	"""
	from .altcoin import CoinInfo as ci
	data = { 'mainnet': (), 'testnet': () }
	networks = ['mainnet'] + (['testnet'] if testnet else [])
	network = 'testnet' if testnet else 'mainnet'

	if usr_coin == None:
		for network in networks:
			data[network] = ci.get_supported_coins(network)
		trust_level = 0
	else:
		if usr_coin.lower() in CoinProtocol.core_coins: # core coin, so return immediately
			return CoinProtocol.coins[usr_coin.lower()].trust_level
		for network in networks:
			data[network] = (ci.get_entry(usr_coin,network),)

		cinfo = data[network][0]
		if not cinfo:
			raise ValueError(f'{usr_coin.upper()!r}: unrecognized coin for network {network.upper()}')
		if cinfo.trust_level == -1:
			raise ValueError(f'{usr_coin.upper()!r}: unsupported (disabled) coin for network {network.upper()}')

		trust_level = cinfo.trust_level

	exec(make_init_genonly_altcoins_str(data),globals(),globals())
	return trust_level

def make_init_genonly_altcoins_str(data):

	def make_proto(e,testnet=False):
		tn_str = 'Testnet' if testnet else ''
		proto = e.name + tn_str
		coin = e.symbol
		if proto[0] in '0123456789':
			proto = 'X_'+proto
		if hasattr(CoinProtocol,proto) or coin.lower() in CoinProtocol.coins:
			return ''

		def num2hexstr(n):
			return "'{:0{}x}'".format(n,(4,2)[n < 256])

		p2sh_info = ", {}: 'p2sh'".format(num2hexstr(e.p2sh_info[0])) if e.p2sh_info else ''
		sw_mmtype = ",'S'" if e.has_segwit else ''

		return f"""
	class {proto}(CoinProtocol.Bitcoin{tn_str}):
		base_coin      = {coin!r}
		addr_ver_bytes = {{ {num2hexstr(e.p2pkh_info[0])}: 'p2pkh'{p2sh_info} }}
		wif_ver_num    = {{ 'std': {num2hexstr(e.wif_ver_num)} }}
		mmtypes        = ('L','C'{sw_mmtype})
		dfl_mmtype     = 'L'
		mmcaps         = ('key','addr')
		""".rstrip()

	def gen_text():
		yield "class CoinProtocol(CoinProtocol):"
		for e in data['mainnet']:
			yield make_proto(e)
		for e in data['testnet']:
			yield make_proto(e,testnet=True)

		for e in data['mainnet']:
			proto,coin = e.name,e.symbol
			if proto[0] in '0123456789':
				proto = 'X_'+proto
			if hasattr(CoinProtocol,proto) or coin.lower() in CoinProtocol.coins:
				continue
			yield 'CoinProtocol.coins[{!r}] = CoinProtocol.proto_info({!r},{})'.format(
				coin.lower(),
				proto,
				e.trust_level )

	return '\n'.join(gen_text()) + '\n'
