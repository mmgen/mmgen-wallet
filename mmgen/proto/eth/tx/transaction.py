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
proto.eth.tx.transaction: Ethereum serialized transaction class
"""

# Adapted from:
#   https://github.com/ethereum/pyethereum/blob/master/ethereum/transactions.py
#   Copyright (c) 2015 Vitalik Buterin, Heiko Hees (MIT License)
#
#   Modified to use libsecp256k1 instead of py_ecc for all EC operations

from enum import Enum

from ....util import cached_property
from ....util2 import get_keccak
from ....protocol import CoinProtocol

from ...secp256k1.secp256k1 import sign_msghash, pubkey_recover, pubkey_gen

from .. import rlp
from ..rlp.sedes import big_endian_int, binary, Binary

secp256k1_ge = CoinProtocol.Secp256k1.secp256k1_group_order
null_address = b'\xff' * 20

keccak_256 = get_keccak()

def sha3(bytes_data):
	return keccak_256(bytes_data).digest()

def mk_contract_addr(sender, nonce):
	return sha3(rlp.encode([sender, nonce]))[12:]

class EthereumTransactionError(Exception):
	pass

class gas_code(Enum):
	GTXCOST        = 21000 # TX BASE GAS COST
	GTXDATAZERO    = 4     # TX DATA ZERO BYTE GAS COST
	GTXDATANONZERO = 68    # TX DATA NON ZERO BYTE GAS COST

class Transaction(rlp.Serializable):

	"""
	A transaction is stored as:
	[nonce, gasprice, startgas, to, value, data, v, r, s]

	nonce is the number of transactions already sent by that account, encoded
	in binary form (eg.  0 -> '', 7 -> '\x07', 1000 -> '\x03\xd8').

	(v,r,s) is the raw Electrum-style signature of the transaction without the
	signature made with the private key corresponding to the sending account,
	with 0 <= v <= 3. From an Electrum-style signature (65 bytes) it is
	possible to extract the public key, and thereby the address, directly.

	A valid transaction is one where:
	(i) the signature is well-formed (ie. 0 <= v <= 3, 0 <= r < P, 0 <= s < N,
	    0 <= r < P - N if v >= 2), and
	(ii) the sending account has enough funds to pay the fee and the value.
	"""

	fields = [
		('nonce',    big_endian_int),
		('gasprice', big_endian_int),
		('startgas', big_endian_int),
		('to',       Binary.fixed_length(20, allow_empty=True)),
		('value',    big_endian_int),
		('data',     binary),
		('v',        big_endian_int),
		('r',        big_endian_int),
		('s',        big_endian_int)]

	def __init__(self, nonce, gasprice, startgas, to, value, data, v=0, r=0, s=0):

		super().__init__(
			nonce,
			gasprice,
			startgas,
			to,
			value,
			data,
			v,
			r,
			s)

	# https://ethereum.stackexchange.com/questions/35481/
	#    deriving-the-v-value-from-an-ecdsa-signature-without-web3j
	#
	# https://ethereum.stackexchange.com/questions/35764/r-s-v-ecdsa-packet-signatures/35770
	#
	#   Basically this code from the bitcoin core libraries define the v value
	#
	#      *recid = (overflow ? 2 : 0) | (secp256k1_fe_is_odd(&r.y) ? 1 : 0);
	#
	#   That gets added to 27 for Ethereum, while 29 and 30 are invalid according to YellowPaper.io
	#
	#   Please note that if an implementation supports EIP-155, instead of using 27 or 28,
	#   it uses CHAIN_ID * 2 + 35. So the value of "v" can also be 37 or 38
	@property
	def recid(self):
		return self.v - 27 if self.v in (27, 28) else self.v - 35 - self.network_id * 2

	@property
	def network_id(self):
		if self.r == 0 and self.s == 0:
			return self.v
		elif self.v in (27, 28):
			return None
		else:
			return ((self.v - 1) // 2) - 17

	def get_sighash(self, network_id):
		if network_id is None:
			return sha3(rlp.encode(unsigned_tx_from_tx(self), UnsignedTransaction))
		else:
			assert 1 <= network_id < 2 ** 63 - 18, f'{network_id}: invalid network ID'
			return sha3(rlp.encode(
				rlp.infer_sedes(self).serialize(self)[:-3]
				+ [network_id, b'', b'']))

	def sign(self, key, network_id=None):
		"""
		Sign transaction with a private key, overwriting any existing signature
		"""
		sig, recid = sign_msghash(self.get_sighash(network_id), bytes.fromhex(key))
		ret = self.copy(
			v = 27 + recid if network_id is None else 35 + recid + network_id * 2,
			r = int.from_bytes(sig[:32], 'big'),
			s = int.from_bytes(sig[32:], 'big'))
		ret._sender = sha3(pubkey_gen(bytes.fromhex(key), 0)[1:])[12:]
		return ret

	@cached_property
	def sender(self):
		"""
		Recover transaction sender from signature
		"""
		if self.r == 0 and self.s == 0:
			return null_address
		# In the yellow paper it is specified that s should be smaller than secp256k1_ge (eq.205)
		elif self.r >= secp256k1_ge or self.s >= secp256k1_ge or self.r == 0 or self.s == 0:
			raise EthereumTransactionError('Invalid signature (r or s) values!')
		return sha3(pubkey_recover(
			self.get_sighash(self.network_id),
			self.r.to_bytes(32, 'big') + self.s.to_bytes(32, 'big'),
			self.recid,
			False)[1:])[12:]

	@property
	def hash(self):
		return sha3(rlp.encode(self))

	def to_dict(self):
		d = {}
		for name, _ in self.__class__._meta.fields:
			d[name] = getattr(self, name)
			if name in ('to', 'data'):
				d[name] = '0x' + d[name].hex()
		d['sender'] = '0x' + self.sender.hex()
		d['hash']   = '0x' + self.hash.hex()
		return d

	@property
	def intrinsic_gas_used(self):
		num_zero_bytes = self.data.count(0)
		num_non_zero_bytes = len(self.data) - num_zero_bytes
		return (
			gas_code.GTXCOST
			# + (0 if self.to else gas_code.CREATE[3])
			+ gas_code.GTXDATAZERO * num_zero_bytes
			+ gas_code.GTXDATANONZERO * num_non_zero_bytes)

	@property
	def creates(self):
		'returns the address of the contract created by this transaction'
		if self.to in (b'', bytes(20)):
			return mk_contract_addr(self.sender, self.nonce)

	def __eq__(self, other):
		return isinstance(other, self.__class__) and self.hash == other.hash

	def __lt__(self, other):
		return isinstance(other, self.__class__) and self.hash < other.hash

	def __hash__(self):
		return int.from_bytes(self.hash, 'big')

	def __ne__(self, other):
		return not self.__eq__(other)

	def __repr__(self):
		return '<Transaction_(%s)>' % self.hash.hex()[:8]

	def __structlog__(self):
		return self.hash.hex()

class UnsignedTransaction(rlp.Serializable):
	fields = [(field, sedes) for field, sedes in Transaction._meta.fields if field not in 'vrs']

def unsigned_tx_from_tx(tx):
	return UnsignedTransaction(
		nonce    = tx.nonce,
		gasprice = tx.gasprice,
		startgas = tx.startgas,
		to       = tx.to,
		value    = tx.value,
		data     = tx.data)
