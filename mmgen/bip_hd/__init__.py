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
bip_hd: BIP-44/49/84, SLIP-44 hierarchical-deterministic key derivation library
"""

# One motivation for this implementation:
#   https://blog.unit410.com/bitcoin/bip32/bip39/kdf/2021/05/17/inconsistent-bip32-derivations.html

import hmac

from ..cfg import Config
from ..util import is_int, fmt
from ..base_obj import Lockable
from ..keygen import KeyGenerator, keygen_public_data
from ..addrgen import AddrGenerator
from ..addr import MMGenAddrType
from ..key import PrivKey
from ..protocol import CoinProtocol
from ..proto.btc.common import hash160, b58chk_encode, b58chk_decode
from ..proto.secp256k1.secp256k1 import pubkey_tweak_add, pubkey_check

from . import chainparams
chainparams_data = chainparams.parse_data()

secp256k1_order = CoinProtocol.Secp256k1.secp256k1_group_order
hardened_idx0 = 0x80000000

def get_chain_params(bipnum, chain):
	return chainparams_data[f'bip-{bipnum}'][chain.upper()]

def get_version_bytes(bip_proto, coin, public):
	return getattr(
		chainparams_data[f'bip-{bip_proto}'][coin],
		'vb_pub' if public else 'vb_prv')

def parse_version_bytes(vb_hex):
	e = chainparams_data['defaults']
	if vb_hex in (e.vb_pub, e.vb_prv):
		return (None, e)
	for bipnum in (49, 84, 86, 44): # search bip-44 last, since it has the most entries
		for e in chainparams_data[f'bip-{bipnum}'].values():
			if vb_hex in (e.vb_pub, e.vb_prv):
				return (bipnum, e)
	raise ValueError(f'0x{vb_hex}: unrecognized extended key version bytes')

def compress_pubkey(pubkey_bytes):
	# see: proto.secp256k1.keygen.pubkey_format()
	return (b'\x02', b'\x03')[pubkey_bytes[-1] & 1] + pubkey_bytes[1:33]

def decompress_pubkey(pubkey_bytes):
	import ecdsa
	return b'\x04' + ecdsa.VerifyingKey.from_string(pubkey_bytes, curve=ecdsa.curves.SECP256k1).to_string()

class Bip32ExtendedKey(Lockable):

	def __init__(self, key_b58):

		try:
			key = b58chk_decode(key_b58)
		except Exception as e:
			raise type(e)(f'invalid extended key: {e}')

		assert len(key) == 78, f'len(key) == {len(key)} (not 78)'

		# Serialization:
		#   ver_bytes | depth | par_print | idx      | chaincode  | serialized_key
		#   0:4 (4)   | 4 (1) | 5:9 (4)   | 9:13 (4) | 13:45 (32) | 45(46): 33(32)
		ver_hex = key[:4].hex()
		bipnum, cp_entry = parse_version_bytes(ver_hex)

		public = ver_hex == cp_entry.vb_pub
		idx_raw = int.from_bytes(key[9:13], byteorder='big')

		self.base58    = key_b58
		self.ver_bytes = key[:4]
		self.depth     = key[4]
		self.par_print = key[5:9]
		self.idx       = idx_raw if idx_raw < hardened_idx0 else idx_raw - hardened_idx0
		self.chaincode = key[13:45]
		self.key       = key[45 if public else 46:]
		self.hardened  = idx_raw >= hardened_idx0 or self.depth == 0
		self.bip_proto = bipnum or 44
		self.network   = cp_entry.network if bipnum else 'mainnet'
		self.public    = public
		self.coin      = cp_entry.chain if bipnum and cp_entry.chain != 'BTC' else '-'

		if self.public:
			if not key[45] in (2, 3):
				raise ValueError(f'0x{key[45]:02x}: invalid first byte for public key data (not 2 or 3)')
		elif key[45]:
			raise ValueError(f'0x{key[45]:02x}: invalid first byte for private key data (not zero)')

		if self.depth == 0:
			if self.par_print != bytes(4):
				raise ValueError(f'{self.par_print.hex()}: non-zero parent fingerprint at depth 0')
			if idx_raw:
				raise ValueError(f'{idx_raw}: non-zero index at depth 0')

	def __str__(self):
		return fmt(f"""
			base58:    {self.base58}
			ver_bytes: {self.ver_bytes.hex()}
			depth:     {self.depth} [{bip_hd_nodes[self.depth].desc}]
			par_print: {self.par_print.hex()}
			idx:       {self.idx}
			chaincode: {self.chaincode.hex()}
			key:       {self.key.hex()}
			hardened:  {self.hardened}
			bip_proto: {self.bip_proto}
			network:   {self.network}
			public:    {self.public}
			coin:      {self.coin}
		""")

def get_bip_by_addr_type(addr_type):
	return (
		84 if addr_type.name == 'bech32' else
		49 if addr_type.name == 'segwit' else
		44)

def check_privkey(key_int):
	match key_int:
		case 0:
			raise ValueError('private key is zero!')
		case n if n >= secp256k1_order:
			raise ValueError(f'{n:x}: private key >= group order!')

class BipHDConfig(Lockable):

	supported_coins = ('btc', 'eth', 'doge', 'ltc', 'bch', 'rune')

	def __init__(self, base_cfg, coin, *, network, addr_type, from_path, no_path_checks):

		if not coin.lower() in self.supported_coins:
			raise ValueError(f'bip_hd: coin {coin.upper()} not supported')

		base_cfg = Config({
			'_clone':  base_cfg,
			'coin':    coin,
			'network': network,
			'type':    addr_type or None,
			'quiet':   True})

		dfl_type = base_cfg._proto.dfl_mmtype
		addr_type = MMGenAddrType(
			proto  = base_cfg._proto,
			id_str = base_cfg.type or ('C' if dfl_type == 'L' else dfl_type))

		self.base_cfg = base_cfg
		self.addr_type = addr_type
		self.kg = KeyGenerator(base_cfg, base_cfg._proto, addr_type.pubkey_type)
		self.ag = AddrGenerator(base_cfg, base_cfg._proto, addr_type)
		self.bip_proto = get_bip_by_addr_type(addr_type)
		self.from_path = from_path
		self.no_path_checks = no_path_checks

class MasterNode(Lockable):
	desc = 'Unconfigured Bip32 Master Node'
	_use_class_attr = True

	def __init__(self, base_cfg, bytes_data):

		H = hmac.digest(b'Bitcoin seed', bytes_data, 'sha512')

		self.par_print = bytes(4)
		self.depth     = 0
		self.key       = H[:32]
		self.chaincode = H[32:]
		self.idx       = 0
		self.hardened  = True
		self.public    = False
		self.base_cfg  = base_cfg

		check_privkey(int.from_bytes(self.key, byteorder='big'))

	def init_cfg(
			self,
			coin           = None,
			*,
			network        = None,
			addr_type      = None,
			from_path      = False,
			no_path_checks = False):

		new = BipHDNodeMaster()

		new.cfg = BipHDConfig(
			self.base_cfg,
			coin,
			network = network,
			addr_type = addr_type,
			from_path = from_path,
			no_path_checks = no_path_checks)
		new.par_print = self.par_print
		new.depth     = self.depth
		new.key       = self.key
		new.chaincode = self.chaincode
		new.idx       = self.idx
		new.hardened  = self.hardened
		new.public    = self.public

		new._lock()
		return new

	def to_coin_type(self, *, coin=None, network=None, addr_type=None):
		return self.init_cfg(coin, network=network, addr_type=addr_type).to_coin_type()

	def to_chain(self, idx, *, coin=None, network=None, addr_type=None, hardened=False, public=False):
		return self.init_cfg(coin, network=network, addr_type=addr_type).to_chain(
			idx      = idx,
			hardened = hardened,
			public   = public)

class BipHDNode(Lockable):
	_autolock = False
	_generated_pubkey = None
	_set_ok = ('_generated_pubkey',)

	def check_param(self, name, val):
		cls = type(self)
		if val is None:
			if not hasattr(cls, name):
				raise ValueError(f'‘{name}’ at depth {self.depth} ({self.desc!r}) must be set')
		elif hasattr(cls, name) and val != getattr(cls, name):
			raise ValueError(
				'{}: invalid value for ‘{}’ at depth {} ({!r}) (must be {})'.format(
					val, name, self.depth, self.desc,
					'None' if getattr(cls, name) is None else f'None or {getattr(cls, name)}')
			)

	def set_params(self, cfg, idx, *, hardened):
		self.check_param('idx', idx)
		self.check_param('hardened', hardened)
		return (
			type(self).idx if idx is None else idx,
			type(self).hardened if hardened is None else hardened)

	@property
	def privkey(self):
		assert not self.public
		return PrivKey(
			self.cfg.base_cfg._proto,
			self.key,
			compressed  = self.cfg.addr_type.compressed,
			pubkey_type = self.cfg.addr_type.pubkey_type)

	@property
	def pubkey_bytes(self):
		if self.public:
			return self.key
		elif self.cfg.addr_type.compressed:
			return self.priv2pub().pubkey
		else:
			return compress_pubkey(self.priv2pub().pubkey)

	def priv2pub(self):
		if not self._generated_pubkey:
			self._generated_pubkey = self.cfg.kg.gen_data(self.privkey)
		return self._generated_pubkey

	@property
	def address(self):
		return self.cfg.ag.to_addr(
			keygen_public_data(
					pubkey        = self.key if self.cfg.addr_type.compressed else decompress_pubkey(self.key),
					viewkey_bytes = None,
					pubkey_type   = self.cfg.addr_type.pubkey_type,
					compressed    = self.cfg.addr_type.compressed)
				if self.public else
			self.priv2pub()
		)

	# Extended keys can be identified by the Hash160 (RIPEMD160 after SHA256) of the serialized ECDSA
	# public key K, ignoring the chain code. This corresponds exactly to the data used in traditional
	# Bitcoin addresses. It is not advised to represent this data in base58 format though, as it may be
	# interpreted as an address that way (and wallet software is not required to accept payment to the
	# chain key itself).
	@property
	def id(self):
		return hash160(self.pubkey_bytes)

	# The first 32 bits of the identifier are called the key fingerprint.
	@property
	def fingerprint(self):
		return self.id[:4]

	@property
	def xpub(self):
		return self.key_extended(public=True, as_str=True)

	@property
	def xprv(self):
		return self.key_extended(public=False, as_str=True)

	def key_extended(self, public, *, as_str=False):
		if self.public and not public:
			raise ValueError('cannot create extended private key for public node!')
		ret = b58chk_encode(
			bytes.fromhex(get_version_bytes(self.cfg.bip_proto, self.cfg.base_cfg.coin, public))
			+ int.to_bytes(self.depth, length=1, byteorder='big')
			+ self.par_print
			+ int.to_bytes(
				self.idx + (hardened_idx0 if self.hardened and self.depth else 0),
				length    = 4,
				byteorder = 'big')
			+ self.chaincode
			+ (self.pubkey_bytes if public else b'\x00' + self.key)
		)
		return ret if as_str else Bip32ExtendedKey(ret)

	def derive_public(self, idx=None):
		return self.derive(idx=idx, hardened=False, public=True)

	def derive_private(self, idx=None, hardened=None):
		return self.derive(idx=idx, hardened=hardened, public=False)

	def derive(self, idx, *, hardened, public):

		if self.public and not public:
			raise ValueError('cannot derive private node from public node!')

		new = bip_hd_nodes[self.depth + 1]()

		new.depth     = self.depth + 1
		new.cfg       = self.cfg
		new.par_print = self.fingerprint
		new.public    = public

		if new.cfg.no_path_checks:
			new.idx, new.hardened = (idx, hardened)
		else:
			if new.public and type(new).hardened:
				raise ValueError(
					f'‘public’ requested, but node of depth {new.depth} ({new.desc}) must be hardened!')
			new.idx, new.hardened = new.set_params(new.cfg, idx, hardened=hardened)

		key_in = b'\x00' + self.key if new.hardened else self.pubkey_bytes

		I = hmac.digest(
			self.chaincode,
			key_in + ((hardened_idx0 if new.hardened else 0) + new.idx).to_bytes(length=4, byteorder='big'),
			'sha512')

		pk_addend_bytes = I[:32]
		new.chaincode   = I[32:]

		if new.public:
			new.key = pubkey_tweak_add(key_in, pk_addend_bytes) # checks range of pk_addend
		else:
			pk_addend = int.from_bytes(pk_addend_bytes, byteorder='big')
			check_privkey(pk_addend)
			key_int = (int.from_bytes(self.key, byteorder='big') + pk_addend) % secp256k1_order
			check_privkey(key_int)
			new.key = int.to_bytes(key_int, length=32, byteorder='big')

		new._lock()
		return new

	@staticmethod
	def from_path(
			base_cfg,
			seed,
			path_str,
			*,
			coin           = None,
			addr_type      = None,
			no_path_checks = False):

		path = path_str.lower().split('/')
		if path.pop(0) != 'm':
			raise ValueError(f'{path_str}: invalid path string (first component is not "m")')

		res = MasterNode(base_cfg, seed).init_cfg(
			coin           = coin or 'btc',
			addr_type      = addr_type or 'compressed',
			no_path_checks = no_path_checks,
			from_path      = True)

		for s in path:
			for suf in ("'", 'h'):
				if s.endswith(suf):
					idx = s.removesuffix(suf)
					hardened = True
					break
			else:
				idx = s
				hardened = False

			if not is_int(idx):
				raise ValueError(f'invalid path component {s!r}')

			res = res.derive(int(idx), hardened=hardened, public=False)

		return res

	@staticmethod
	# ‘addr_type’ is required for broken coins with duplicate version bytes across BIP protocols
	# (i.e. Dogecoin)
	def from_extended_key(base_cfg, coin, xkey_b58, *, addr_type=None):
		xk = Bip32ExtendedKey(xkey_b58)

		if xk.public:
			pubkey_check(xk.key)
		else:
			check_privkey(int.from_bytes(xk.key, byteorder='big'))

		addr_types = {
			84: 'bech32',
			49: 'segwit',
			44: None}

		new = bip_hd_nodes[xk.depth]()

		new.cfg = BipHDConfig(
			base_cfg,
			coin,
			network = xk.network,
			addr_type = addr_type or addr_types[xk.bip_proto],
			from_path = False,
			no_path_checks = False)

		new.par_print  = xk.par_print
		new.depth      = xk.depth
		new.key        = xk.key
		new.chaincode  = xk.chaincode
		new.idx        = xk.idx
		new.hardened   = xk.hardened
		new.public     = xk.public

		new._lock()
		return new

class BipHDNodeMaster(BipHDNode):
	desc = 'Bip32 Master Node'
	hardened = True
	idx = None

	def to_coin_type(self):
		#           purpose          coin_type
		return self.derive_private().derive_private()

	def to_chain(self, idx, *, hardened=False, public=False):
		#           purpose          coin_type        account #0            chain
		return self.derive_private().derive_private().derive_private(idx=0).derive(
			idx      = idx,
			hardened = False if public else hardened,
			public   = public)

class BipHDNodePurpose(BipHDNode):
	desc = 'Purpose'
	hardened = True

	def set_params(self, cfg, idx, *, hardened):
		self.check_param('hardened', hardened)
		if idx not in (None, cfg.bip_proto):
			raise ValueError(
				f'index for path component {self.desc!r} with address type {cfg.addr_type!r} '
				f'must be {cfg.bip_proto}, not {idx}')
		return (cfg.bip_proto, type(self).hardened)

class BipHDNodeCoinType(BipHDNode):
	desc = 'Coin Type'
	hardened = True

	def set_params(self, cfg, idx, *, hardened):
		self.check_param('hardened', hardened)
		chain_idx = get_chain_params(
			bipnum = get_bip_by_addr_type(cfg.addr_type),
			chain  = cfg.base_cfg.coin).idx
		if idx not in (None, chain_idx):
			raise ValueError(
				f'index {idx} at depth {self.depth} ({self.desc}) does not match '
				f'chain index {chain_idx} for coin {cfg.base_cfg.coin!r}')
		return (chain_idx, type(self).hardened)

	def to_chain(self, idx, *, hardened=False, public=False):
		#           account #0            chain
		return self.derive_private(idx=0).derive(
			idx      = idx,
			hardened = False if public else hardened,
			public   = public)

class BipHDNodeAccount(BipHDNode):
	desc = 'Account'
	hardened = True

class BipHDNodeChain(BipHDNode):
	desc = 'Chain'
	hardened = False

	def set_params(self, cfg, idx, *, hardened):
		self.check_param('hardened', hardened)
		if idx not in (0, 1):
			raise ValueError(
				f'at depth {self.depth} ({self.desc}), ‘idx’ must be either 0 (external) or 1 (internal)')
		return (idx, type(self).hardened)

class BipHDNodeAddrIdx(BipHDNode):
	desc = 'Address Index'
	hardened = False

bip_hd_nodes = {
	0: BipHDNodeMaster,
	1: BipHDNodePurpose,
	2: BipHDNodeCoinType,
	3: BipHDNodeAccount,
	4: BipHDNodeChain,
	5: BipHDNodeAddrIdx
}
