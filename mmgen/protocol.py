#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
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
protocol: Coin protocol base classes and initializer
"""

from collections import namedtuple

from .cfg import gc
from .objmethods import MMGenObject

decoded_wif = namedtuple('decoded_wif', ['sec', 'pubkey_type', 'compressed'])
decoded_addr = namedtuple('decoded_addr', ['bytes', 'ver_bytes', 'fmt'])
decoded_addr_multiview = namedtuple('mv_decoded_addr', ['bytes', 'ver_bytes', 'fmt', 'addr', 'views', 'view_pref'])
parsed_addr = namedtuple('parsed_addr', ['ver_bytes', 'data'])

_finfo = namedtuple('fork_info', ['height', 'hash', 'name', 'replayable'])
_nw = namedtuple('coin_networks', ['mainnet', 'testnet', 'regtest'])

class CoinProtocol(MMGenObject):

	proto_info = namedtuple('proto_info', ['name', 'trust_level']) # trust levels: see altcoin/params.py

	# keys are mirrored in gc.core_coins:
	coins = {
		'btc': proto_info('Bitcoin',         5),
		'bch': proto_info('BitcoinCash',     5),
		'ltc': proto_info('Litecoin',        5),
		'eth': proto_info('Ethereum',        4),
		'etc': proto_info('EthereumClassic', 4),
		'zec': proto_info('Zcash',           2),
		'xmr': proto_info('Monero',          4)
	}

	class Base(MMGenObject):
		base_proto = None
		base_proto_coin  = None
		base_coin  = None
		is_fork_of = None
		chain_names = None
		networks   = ('mainnet', 'testnet', 'regtest')
		decimal_prec = 28

		def __init__(self, cfg, coin, name, network, tokensym=None, need_amt=False):
			self.cfg        = cfg
			self.coin       = coin.upper()
			self.coin_id    = self.coin
			self.name       = name
			self.network    = network
			self.tokensym   = tokensym
			self.cls_name   = type(self).__name__
			self.testnet    = network in ('testnet', 'regtest')
			self.regtest    = network == 'regtest'
			self.networks   = tuple(k for k, v in self.network_names._asdict().items() if v)
			self.network_id = coin.lower() + {
				'mainnet': '',
				'testnet': '_tn',
				'regtest': '_rt',
			}[network]

			if hasattr(self, 'wif_ver_num'):
				self.wif_ver_bytes = {k:bytes.fromhex(v) for k, v in self.wif_ver_num.items()}
				self.wif_ver_bytes_to_pubkey_type = {v:k for k, v in self.wif_ver_bytes.items()}
				vbs = list(self.wif_ver_bytes.values())
				self.wif_ver_bytes_len = len(vbs[0]) if len(set(len(b) for b in vbs)) == 1 else None

			if hasattr(self, 'addr_ver_info'):
				self.addr_ver_bytes = {bytes.fromhex(k):v for k, v in self.addr_ver_info.items()}
				self.addr_fmt_to_ver_bytes = {v:k for k, v in self.addr_ver_bytes.items()}
				self.addr_ver_bytes_len = len(list(self.addr_ver_bytes)[0])

			if gc.cmd_caps:
				for cap in gc.cmd_caps.caps:
					if cap not in self.mmcaps:
						from .util import die
						die(2, f'Command {gc.prog_name!r} not supported for coin {self.coin}')

			if self.chain_names:
				self.chain_name = self.chain_names[0] # first chain name is default
			else:
				self.chain_names = [self.network]
				self.chain_name = self.network

			if self.tokensym:
				assert self.name.startswith('Ethereum'), 'CoinProtocol.Base_chk1'

			if self.base_coin in ('ETH', 'XMR'):
				from .util2 import get_keccak
				self.keccak_256 = get_keccak(cfg)

			if need_amt:
				from . import amt
				from decimal import getcontext
				self.coin_amt = getattr(amt, self.coin_amt)
				self.max_tx_fee = self.coin_amt(self.max_tx_fee) if hasattr(self, 'max_tx_fee') else None
				getcontext().prec = self.decimal_prec
			else:
				self.coin_amt = None
				self.max_tx_fee = None

		@property
		def dcoin(self):
			return self.coin

		@classmethod
		def chain_name_to_network(cls, cfg, coin, chain_name):
			"""
			The generic networks 'mainnet', 'testnet' and 'regtest' are required for all coins
			that support transaction operations.

			For protocols that have specific names for chains corresponding to these networks,
			the attribute 'chain_name' is used, while 'network' retains the generic name.
			For Bitcoin and Bitcoin forks, 'network' and 'chain_name' are equivalent.
			"""
			for network in ('mainnet', 'testnet', 'regtest'):
				proto = init_proto(cfg, coin, network=network)
				for proto_chain_name in proto.chain_names:
					if chain_name == proto_chain_name:
						return network
			raise ValueError(f'{chain_name}: unrecognized chain name for coin {coin}')

		@staticmethod
		def parse_network_id(network_id):
			nid = namedtuple('parsed_network_id', ['coin', 'network'])
			if network_id.endswith('_tn'):
				return nid(network_id[:-3], 'testnet')
			elif network_id.endswith('_rt'):
				return nid(network_id[:-3], 'regtest')
			else:
				return nid(network_id, 'mainnet')

		@staticmethod
		def create_network_id(coin, network):
			return coin.lower() + {'mainnet':'', 'testnet':'_tn', 'regtest':'_rt'}[network]

		def cap(self, s):
			return s in self.caps

		def get_addr_len(self, addr_fmt):
			return self.addr_len

		def decode_addr_bytes(self, addr_bytes):
			vlen = self.addr_ver_bytes_len
			return decoded_addr(
				addr_bytes[vlen:],
				addr_bytes[:vlen],
				self.addr_ver_bytes[addr_bytes[:vlen]])

		def coin_addr(self, addr):
			from .addr import CoinAddr
			return CoinAddr(proto=self, addr=addr)

		def addr_type(self, id_str):
			from .addr import MMGenAddrType
			return MMGenAddrType(proto=self, id_str=id_str)

		def viewkey(self, viewkey_str):
			raise NotImplementedError(f'{self.name} protocol does not support view keys')

		def base_proto_subclass(self, cls, modname, sub_clsname=None):
			"""
			magic module loading and class selection
			"""
			modpath = f'mmgen.proto.{self.base_proto_coin.lower()}.{modname}'

			clsname = (
				self.mod_clsname
				+ ('Token' if self.tokensym else '')
				+ cls.__name__)

			import importlib
			if sub_clsname:
				return getattr(getattr(importlib.import_module(modpath), clsname), sub_clsname)
			else:
				return getattr(importlib.import_module(modpath), clsname)


	class Secp256k1(Base):
		"""
		Bitcoin and Ethereum protocols inherit from this class
		"""
		secp256k1_group_order = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141
		privkey_len  = 32
		pubkey_types = ('std',)

		def parse_addr(self, ver_bytes, addr_bytes, fmt):
			return parsed_addr(
				ver_bytes  = ver_bytes,
				data       = addr_bytes,
			)

		def preprocess_key(self, sec, pubkey_type):
			# Key must be non-zero and less than group order of secp256k1 curve
			if 0 < int.from_bytes(sec, 'big') < self.secp256k1_group_order:
				return sec
			else: # chance of this is less than 1 in 2^127
				from .util import die, ymsg
				pk = int.from_bytes(sec, 'big')
				if pk == 0: # chance of this is 1 in 2^256
					die(4, 'Private key is zero!')
				elif pk == self.secp256k1_group_order: # ditto
					die(4, 'Private key == secp256k1_group_order!')
				else: # return key mod group order as the key
					if not self.cfg.test_suite:
						ymsg(f'Warning: private key is greater than secp256k1 group order!:\n  {sec.hex()}')
					return (pk % self.secp256k1_group_order).to_bytes(self.privkey_len, 'big')

	class DummyWIF:
		"""
		Ethereum and Monero protocols inherit from this class
		"""
		def encode_wif(self, privbytes, pubkey_type, compressed):
			assert pubkey_type == self.pubkey_type, f'{pubkey_type}: invalid pubkey_type for {self.name} protocol!'
			assert compressed is False, f'{self.name} protocol does not support compressed pubkeys!'
			return privbytes.hex()

		def decode_wif(self, wif):
			return decoded_wif(
				sec         = bytes.fromhex(wif),
				pubkey_type = self.pubkey_type,
				compressed  = False)

def init_proto(
		cfg,
		coin       = None,
		testnet    = False,
		regtest    = False,
		network    = None,
		network_id = None,
		tokensym   = None,
		need_amt   = False,
		return_cls = False):

	assert type(testnet) is bool, 'init_proto_chk1'
	assert type(regtest) is bool, 'init_proto_chk2'
	assert coin or network_id, 'init_proto_chk3'
	assert not (coin and network_id), 'init_proto_chk4'

	if network_id:
		coin, network = CoinProtocol.Base.parse_network_id(network_id)
	elif network:
		assert network in CoinProtocol.Base.networks, f'init_proto_chk5 - {network!r}: invalid network'
		assert testnet is False, 'init_proto_chk6'
		assert regtest is False, 'init_proto_chk7'
	else:
		network = 'regtest' if regtest else 'testnet' if testnet else 'mainnet'

	coin = coin.lower()

	if coin not in CoinProtocol.coins:
		from .altcoin.params import init_genonly_altcoins
		init_genonly_altcoins(coin, testnet=testnet) # raises exception on failure

	name = CoinProtocol.coins[coin].name
	proto_name = name + ('' if network == 'mainnet' else network.capitalize())

	if not hasattr(CoinProtocol, proto_name):
		import importlib
		setattr(
			CoinProtocol,
			proto_name,
			getattr(importlib.import_module(f'mmgen.proto.{coin}.params'), network)
		)

	if return_cls:
		return getattr(CoinProtocol, proto_name)

	return getattr(CoinProtocol, proto_name)(
		cfg       = cfg,
		coin      = coin,
		name      = name,
		network   = network,
		tokensym  = tokensym,
		need_amt  = need_amt)

def init_proto_from_cfg(cfg, need_amt):
	return init_proto(
		cfg       = cfg,
		coin      = cfg.coin,
		network   = cfg.network,
		tokensym  = cfg.token,
		need_amt  = need_amt)

def warn_trustlevel(cfg):

	coinsym = cfg.coin

	if coinsym.lower() in CoinProtocol.coins:
		trust_level = CoinProtocol.coins[coinsym.lower()].trust_level
	else:
		from .altcoin.params import CoinInfo
		e = CoinInfo.get_entry(coinsym, 'mainnet')
		trust_level = e.trust_level if e else None
		if trust_level in (None, -1):
			from .util import die
			die(1, f'Coin {coinsym} is not supported by {gc.proj_name}')

	if trust_level > 3:
		return

	m = """
		Support for coin {c!r} is EXPERIMENTAL.  The {p} project
		assumes no responsibility for any loss of funds you may incur.
		This coin’s {p} testing status: {t}
		Are you sure you want to continue?
	"""

	from .util import fmt
	from .color import red, yellow, green

	warning = fmt(m).strip().format(
		c = coinsym.upper(),
		t = {
			0: red('COMPLETELY UNTESTED'),
			1: red('LOW'),
			2: yellow('MEDIUM'),
			3: green('OK'),
		}[trust_level],
		p = gc.proj_name)

	if cfg.test_suite:
		cfg._util.qmsg(warning)
		return

	from .ui import keypress_confirm
	if not keypress_confirm(cfg, warning, default_yes=True):
		import sys
		sys.exit(0)
