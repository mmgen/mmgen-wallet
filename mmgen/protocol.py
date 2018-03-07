#!/usr/bin/env python
#
# MMGen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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
from binascii import unhexlify
from mmgen.util import msg,pmsg,Msg,pdie
from mmgen.obj import MMGenObject,BTCAmt,LTCAmt,BCHAmt,B2XAmt
from mmgen.globalvars import g
import mmgen.bech32 as bech32

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
	if [i for i in b58num if not i in _b58a]:
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
	mmtypes         = ('L','C','S','B')
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
	caps               = ('rbf','segwit')
	mmcaps             = ('key','addr','rpc','tx')
	base_coin          = 'BTC'
	# From BIP173: witness version 'n' is stored as 'OP_n'. OP_0 is encoded as 0x00,
	# but OP_1 through OP_16 are encoded as 0x51 though 0x60 (81 to 96 in decimal).
	witness_vernum_hex = '00'
	witness_vernum     = int(witness_vernum_hex,16)
	bech32_hrp         = 'bc'

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
	def verify_addr(cls,addr,hex_width,return_dict=False):

		if 'B' in cls.mmtypes and addr[:len(cls.bech32_hrp)] == cls.bech32_hrp:
			ret = bech32.decode(cls.bech32_hrp,addr)
			if ret[0] != cls.witness_vernum:
				msg('{}: Invalid witness version number'.format(ret[0]))
			elif ret[1]:
				return {
					'hex': ''.join(map(chr,ret[1])).encode('hex'),
					'format': 'bech32'
				} if return_dict else True
			return False

		for addr_fmt in cls.addr_ver_num:
			ver_num,pfx = cls.addr_ver_num[addr_fmt]
			if type(pfx) == tuple:
				if addr[0] not in pfx: continue
			elif addr[:len(pfx)] != pfx: continue
			num = _b58tonum(addr)
			if num == False:
				if g.debug: Msg('Address cannot be converted to base 58')
				break
			addr_hex = '{:0{}x}'.format(num,len(ver_num)+hex_width+8)
#			pmsg(hex_width,len(addr_hex),addr_hex[:len(ver_num)],ver_num)
			if addr_hex[:len(ver_num)] != ver_num: continue
			if hash256(addr_hex[:-8])[:8] == addr_hex[-8:]:
				return {
					'hex': addr_hex[len(ver_num):-8],
					'format': {'p2pkh':'p2pkh','p2sh':'p2sh','p2sh2':'p2sh',
								'zcash_z':'zcash_z','viewkey':'viewkey'}[addr_fmt]
				} if return_dict else True
			else:
				if g.debug: Msg('Invalid checksum in address')
				break

		return False

	@classmethod
	def pubhash2addr(cls,pubkey_hash,p2sh):
		assert len(pubkey_hash) == 40,'{}: invalid length for pubkey hash'.format(len(pubkey_hash))
		s = cls.addr_ver_num[('p2pkh','p2sh')[p2sh]][0] + pubkey_hash
		lzeroes = (len(s) - len(s.lstrip('0'))) / 2 # non-zero only for ver num '00' (BTC p2pkh)
		return ('1' * lzeroes) + _b58chk_encode(s)

	# Segwit:
	@classmethod
	def pubhex2redeem_script(cls,pubhex):
		# https://bitcoincore.org/en/segwit_wallet_dev/
		# The P2SH redeemScript is always 22 bytes. It starts with a OP_0, followed
		# by a canonical push of the keyhash (i.e. 0x0014{20-byte keyhash})
		return cls.witness_vernum_hex + '14' + hash160(pubhex)

	@classmethod
	def pubhex2segwitaddr(cls,pubhex):
		return cls.pubhash2addr(hash160(cls.pubhex2redeem_script(pubhex)),p2sh=True)

	@classmethod
	def pubhash2bech32addr(cls,pubhash):
		d = map(ord,pubhash.decode('hex'))
		return bech32.bech32_encode(cls.bech32_hrp,[cls.witness_vernum]+bech32.convertbits(d,8,5))

class BitcoinTestnetProtocol(BitcoinProtocol):
	addr_ver_num         = { 'p2pkh': ('6f',('m','n')), 'p2sh':  ('c4','2') }
	wif_ver_num          = { 'std': 'ef' }
	data_subdir          = 'testnet'
	daemon_data_subdir   = 'testnet3'
	rpc_port             = 18332
	bech32_hrp           = 'tb'
	bech32_hrp_rt        = 'bcrt'

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

class B2XProtocol(BitcoinProtocol):
	daemon_name     = 'bitcoind-2x'
	daemon_data_dir = os.path.join(os.getenv('APPDATA'),'Bitcoin_2X') if g.platform == 'win' \
						else os.path.join(g.home_dir,'.bitcoin-2x')
	rpc_port        = 8338
	coin_amt        = B2XAmt
	max_tx_fee      = B2XAmt('0.1')
	forks = [
		(None,'','btc',True) # activation: 494784
	]

class B2XTestnetProtocol(B2XProtocol):
	addr_ver_num       = { 'p2pkh': ('6f',('m','n')), 'p2sh':  ('c4','2') }
	wif_ver_num        = { 'std': 'ef' }
	data_subdir        = 'testnet'
	daemon_data_subdir = 'testnet5'
	rpc_port           = 18338

class LitecoinProtocol(BitcoinProtocol):
	block0         = '12a765e31ffd4059bada1e25190f6e98c99d9714d334efa41a195a7e7e04bfe2'
	name           = 'litecoin'
	daemon_name    = 'litecoind'
	daemon_data_dir = os.path.join(os.getenv('APPDATA'),'Litecoin') if g.platform == 'win' \
						else os.path.join(g.home_dir,'.litecoin')
	addr_ver_num   = { 'p2pkh': ('30','L'), 'p2sh':  ('32','M'), 'p2sh2':  ('05','3') } # 'p2sh' is new fmt
	wif_ver_num    = { 'std': 'b0' }
	mmtypes         = ('L','C','S')
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

class BitcoinProtocolAddrgen(BitcoinProtocol): mmcaps = ('key','addr')
class BitcoinTestnetProtocolAddrgen(BitcoinTestnetProtocol): mmcaps = ('key','addr')

class DummyWIF(object):

	@classmethod
	def hex2wif(cls,hexpriv,pubkey_type,compressed):
		n = cls.name.capitalize()
		assert pubkey_type == cls.pubkey_type,'{}: invalid pubkey_type for {}!'.format(pubkey_type,n)
		assert compressed == False,'{} does not support compressed pubkeys!'.format(n)
		return str(hexpriv)

	@classmethod
	def wif2hex(cls,wif):
		return { 'hex':str(wif), 'pubkey_type':cls.pubkey_type, 'compressed':False }

class EthereumProtocol(DummyWIF,BitcoinProtocolAddrgen):

	addr_width = 40
	mmtypes    = ('E',)
	dfl_mmtype = 'E'
	name = 'ethereum'
	base_coin = 'ETH'
	pubkey_type = 'std' # required by DummyWIF

	@classmethod
	def verify_addr(cls,addr,hex_width,return_dict=False):
		from mmgen.util import is_hex_str_lc
		if is_hex_str_lc(addr) and len(addr) == cls.addr_width:
			return { 'hex': addr, 'format': 'ethereum' } if return_dict else True
		if g.debug: Msg("Invalid address '{}'".format(addr))
		return False

	@classmethod
	def pubhash2addr(cls,pubkey_hash,p2sh):
		assert len(pubkey_hash) == 40,'{}: invalid length for pubkey hash'.format(len(pubkey_hash))
		assert not p2sh,'Ethereum has no P2SH address format'
		return pubkey_hash

class EthereumTestnetProtocol(EthereumProtocol): pass
class EthereumClassicProtocol(EthereumProtocol):
	name = 'ethereum_classic'
class EthereumClassicTestnetProtocol(EthereumClassicProtocol): pass

class ZcashProtocol(BitcoinProtocolAddrgen):
	name         = 'zcash'
	base_coin    = 'ZEC'
	addr_ver_num = {
		'p2pkh':   ('1cb8','t1'),
		'p2sh':    ('1cbd','t3'),
		'zcash_z': ('169a','zc'),
		'viewkey': ('0b1c','V') }
	wif_ver_num  = { 'std': '80', 'zcash_z': 'ab36' }
	mmtypes      = ('L','C','Z')
	dfl_mmtype   = 'L'

	@classmethod
	def preprocess_key(cls,hexpriv,pubkey_type): # zero the first four bits
		if pubkey_type == 'zcash_z':
			return '{:02x}'.format(int(hexpriv[:2],16) & 0x0f) + hexpriv[2:]
		else:
			return hexpriv

	@classmethod
	def pubhash2addr(cls,pubkey_hash,p2sh):
		hl = len(pubkey_hash)
		if hl == 40:
			return super(cls,cls).pubhash2addr(pubkey_hash,p2sh)
		elif hl == 128:
			raise NotImplementedError,'Zcash z-addresses have no pubkey hash'
		else:
			raise ValueError,'{}: incorrect pubkey_hash length'.format(hl)

class ZcashTestnetProtocol(ZcashProtocol):
	wif_ver_num  = { 'std': '??', 'zcash_z': 'ac08' }
	addr_ver_num = {
		'p2pkh': ('??','t1'),
		'p2sh':  ('??','t3'),
		'zcash_z': ('16b6','??'),
		'viewkey': ('0b2a','??') }

# https://github.com/monero-project/monero/blob/master/src/cryptonote_config.h
class MoneroProtocol(DummyWIF,BitcoinProtocolAddrgen):
	name         = 'monero'
	base_coin    = 'XMR'
	addr_ver_num = { 'monero': ('12','4'), 'monero_sub': ('2a','8') } # 18,42
	wif_ver_num  = {}
	mmtypes      = ('M',)
	dfl_mmtype   = 'M'
	addr_width   = 95
	pubkey_type = 'monero' # required by DummyWIF

	@classmethod
	def preprocess_key(cls,hexpriv,pubkey_type): # reduce key
		try:
			from ed25519ll.djbec import l
		except:
			from mmgen.ed25519 import l
		n = int(hexpriv.decode('hex')[::-1].encode('hex'),16) % l
		return '{:064x}'.format(n).decode('hex')[::-1].encode('hex')

	@classmethod
	def verify_addr(cls,addr,hex_width,return_dict=False):

		def b58dec(addr_str):
			from mmgen.util import baseconv
			dec,l = baseconv.tohex,len(addr_str)
			a = ''.join([dec(addr_str[i*11:i*11+11],'b58',pad=16) for i in range(l/11)])
			b = dec(addr_str[-(l%11):],'b58',pad=10)
			return a + b

		from mmgen.util import is_b58_str
		assert is_b58_str(addr),'Not valid base-58 string'
		assert len(addr) == cls.addr_width,'Incorrect width'

		ret = b58dec(addr)
		import sha3
		chk = sha3.keccak_256(ret.decode('hex')[:-4]).hexdigest()[:8]
		assert chk == ret[-8:],'Incorrect checksum'

		return { 'hex': ret, 'format': 'monero' } if return_dict else True

class MoneroTestnetProtocol(MoneroProtocol):
	addr_ver_num = { 'monero': ('35','4'), 'monero_sub': ('3f','8') } # 53,63

class CoinProtocol(MMGenObject):
	coins = {
		#      mainnet testnet trustlevel (None == skip)
		'btc': (BitcoinProtocol,BitcoinTestnetProtocol,None),
		'bch': (BitcoinCashProtocol,BitcoinCashTestnetProtocol,None),
		'ltc': (LitecoinProtocol,LitecoinTestnetProtocol,None),
		'eth': (EthereumProtocol,EthereumTestnetProtocol,2),
		'etc': (EthereumClassicProtocol,EthereumClassicTestnetProtocol,2),
		'zec': (ZcashProtocol,ZcashTestnetProtocol,2),
		'xmr': (MoneroProtocol,MoneroTestnetProtocol,None)
	}
	def __new__(cls,coin,testnet):
		coin = coin.lower()
		assert type(testnet) == bool
		m = "'{}': not a valid coin. Valid choices are {}"
		assert coin in cls.coins,m.format(coin,','.join(cls.get_valid_coins()))
		return cls.coins[coin][testnet]

	@classmethod
	def get_valid_coins(cls,upcase=False):
		from mmgen.altcoin import CoinInfo as ci
		ret = sorted(set(
			[e[1] for e in ci.coin_constants['mainnet'] if e[6] != -1]
			+ cls.coins.keys()))
		return [getattr(e,('lower','upper')[upcase])() for e in ret]

	@classmethod
	def get_base_coin_from_name(cls,name):
		for proto,foo in cls.coins.values():
			if name == proto.__name__[:-8].lower():
				return proto.base_coin
		return False

def init_genonly_altcoins(usr_coin,trust_level=None):
	from mmgen.altcoin import CoinInfo as ci
	if trust_level is None:
		if not usr_coin: return None # BTC
		if usr_coin.lower() in CoinProtocol.coins:
			return CoinProtocol.coins[usr_coin.lower()][2]
		usr_coin = usr_coin.upper()
		mn_coins = [e[1] for e in ci.coin_constants['mainnet'] if e[6] != -1]
		if usr_coin not in mn_coins: return None
		trust_level = ci.coin_constants['mainnet'][mn_coins.index(usr_coin)][6]
	data = {}
	for k in ('mainnet','testnet'):
		data[k] = [e for e in ci.coin_constants[k] if e[6] >= trust_level]
	exec(make_init_genonly_altcoins_str(data))
	return trust_level

def make_init_genonly_altcoins_str(data):

	def make_proto(e,testnet=False):
		tn_str = 'Testnet' if testnet else ''
		proto,coin = '{}{}Protocol'.format(e[0],tn_str),e[1]
		if proto[0] in '0123456789': proto = 'X_'+proto
		if proto in globals(): return ''
		if coin.lower() in CoinProtocol.coins: return ''
		def num2hexstr(n):
			return '{:0{}x}'.format(n,2 if n < 256 else 4)
		o  = ['class {}(Bitcoin{}ProtocolAddrgen):'.format(proto,tn_str)]
		o += ["base_coin = '{}'".format(coin)]
		o += ["name = '{}'".format(e[0].lower())]
		o += ["nameCaps = '{}'".format(e[0])]
		a = "addr_ver_num = {{ 'p2pkh': ({!r},{!r})".format(num2hexstr(e[3][0]),e[3][1])
		b = ", 'p2sh':  ({!r},{!r})".format(num2hexstr(e[4][0]),e[4][1]) if e[4] else ''
		o += [a+b+' }']
		o += ["wif_ver_num = {{ 'std': {!r} }}".format(num2hexstr(e[2]))]
		o += ["mmtypes = ('L','C'{})".format(",'S'" if e[5] else '')]
		o += ["dfl_mmtype = '{}'".format('L')]
		return '\n\t'.join(o) + '\n'

	out = ''
	for e in data['mainnet']:
		out += make_proto(e)
	for e in data['testnet']:
		out += make_proto(e,testnet=True)

	tn_coins = [e[1] for e in data['testnet']]
	fs = "CoinProtocol.coins['{}'] = ({}Protocol,{})\n"
	for e in data['mainnet']:
		proto,coin = e[0],e[1]
		if proto[0] in '0123456789': proto = 'X_'+proto
		if proto+'Protocol' in globals(): continue
		if coin.lower() in CoinProtocol.coins: continue
		out += fs.format(coin.lower(),proto,('None',proto+'TestnetProtocol')[coin in tn_coins])
#	print out
	return out

def init_coin(coin):
	coin = coin.upper()
	g.coin = coin
	g.proto = CoinProtocol(coin,g.testnet)
