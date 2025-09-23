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
proto.cosmos.tx.protobuf: transaction serialization for Cosmos protocol
"""

# cosmjs-types/src/cosmos/bank/v1beta1/tx.ts
# cosmjs-types/src/cosmos/tx/v1beta1/tx.ts
# cosmjs-types/src/cosmos/tx/signing/v1beta1/signing.ts

from hashlib import sha256

from dataclasses import dataclass
from pure_protobuf.annotations import Field
from pure_protobuf.message import BaseMessage
from typing import Annotated, List, Optional
from enum import IntEnum

class SignMode(IntEnum):
	SIGN_MODE_UNSPECIFIED = 0
	SIGN_MODE_DIRECT = 1
	SIGN_MODE_TEXTUAL = 2
	SIGN_MODE_DIRECT_AUX = 3
	SIGN_MODE_LEGACY_AMINO_JSON = 127
	SIGN_MODE_EIP_191 = 191
	UNRECOGNIZED = -1

@dataclass
class PublicKeyData(BaseMessage):
	data: Annotated[bytes, Field(1)]

@dataclass
class PublicKey(BaseMessage):
	id:  Annotated[str, Field(1)] #  '/cosmos.crypto.secp256k1.PubKey'
	key: Annotated[PublicKeyData, Field(2)]

@dataclass
class ModeInfo(BaseMessage):

	@dataclass
	class Single(BaseMessage):
		mode: Annotated[SignMode, Field(1)]

	@dataclass
	class Multi(BaseMessage):
		bitarray:  Annotated[bytes, Field(1)]
		modeInfos: Annotated[List[bytes], Field(2)]

	single: Annotated[Optional[Single], Field(1)] = None
	multi:  Annotated[Optional[Multi], Field(2)] = None

@dataclass
class SignerInfo(BaseMessage):
	publicKey: Annotated[PublicKey, Field(1)]
	# mode_info describes the signing mode of the signer and is a nested
	# structure to support nested multisig pubkeys
	modeInfo:  Annotated[ModeInfo, Field(2)]
	# sequence is the sequence of the account, which describes the number of committed
	# transactions signed by a given address. It is used to prevent replay attacks.
	sequence:  Annotated[int, Field(3)]

@dataclass
class Coin(BaseMessage):
	denom:  Annotated[str, Field(1)]
	amount: Annotated[str, Field(2)]

@dataclass
class Fee(BaseMessage):
	amount:   Annotated[Optional[List[Coin]], Field(1)] = None # = field(default_factory=list)
	gasLimit: Annotated[Optional[int], Field(2)] = None
	payer:    Annotated[Optional[str], Field(3)] = None
	granter:  Annotated[Optional[str], Field(4)] = None

@dataclass
class AuthInfo(BaseMessage):
	signerInfos: Annotated[List[SignerInfo], Field(1)]
	fee:         Annotated[Optional[Fee], Field(2)] = None
	tip:         Annotated[Optional[int], Field(3)] = None

# TxRaw is a variant of Tx that pins the signer's exact binary representation of body
# and auth_info. This is used for signing, broadcasting and verification. The binary
# `serialize(tx: TxRaw)` is stored in Tendermint and the hash `sha256(serialize(tx:
# TxRaw))` becomes the "txhash", commonly used as the transaction ID.
@dataclass
class RawTx(BaseMessage): # TxRaw (cosmjs)
	bodyBytes:     Annotated[bytes, Field(1)]
	authInfoBytes: Annotated[bytes, Field(2)]
	signatures:    Annotated[List[bytes], Field(3)]

# SignDoc is the type used for generating sign bytes for SIGN_MODE_DIRECT
@dataclass
class SignDoc(BaseMessage):
	bodyBytes:     Annotated[bytes, Field(1)]
	authInfoBytes: Annotated[bytes, Field(2)]
	chainId:       Annotated[str, Field(3)]
	accountNumber: Annotated[int, Field(4)]

@dataclass
class TxMsg(BaseMessage):
	msgs_cls = None
	id:        Annotated[str, Field(1)]
	bodyBytes: Annotated[bytes, Field(2)]

	def __new__(cls, *, id, bodyBytes):
		msg_cls = getattr(cls.msgs_cls, id.removeprefix('/types.'))
		me = BaseMessage.__new__(msg_cls)
		me.id = id
		me.body = getattr(msg_cls, 'Body').loads(bodyBytes)
		return me

@dataclass
class Tx(BaseMessage):
	body:       Annotated[bytes, Field(1)]
	authInfo:   Annotated[bytes, Field(2)]
	signatures: Annotated[List[bytes], Field(3)]

	@property
	def raw(self):
		return RawTx(
			bodyBytes = bytes(self.body),
			authInfoBytes = bytes(self.authInfo),
			signatures = self.signatures)

	@property
	def txid(self):
		return sha256(bytes(self.raw)).hexdigest()

	# raises exception on failure:
	def verify_sig(self, proto, account_number, backend='secp256k1'):
		sign_doc = SignDoc(
			bodyBytes = bytes(self.body),
			authInfoBytes = bytes(self.authInfo),
			chainId = proto.chain_id,
			accountNumber = account_number)
		sig = self.signatures[0]
		pubkey = self.authInfo.signerInfos[0].publicKey.key.data
		msghash = sha256(bytes(sign_doc)).digest()

		match backend:
			case 'secp256k1':
				from ...secp256k1.secp256k1 import verify_sig
				if not verify_sig(sig, msghash, pubkey):
					raise ValueError('signature verification failed')
			case 'ecdsa':
				# ecdsa.keys.VerifyingKey.verify_digest():
				#   raises BadSignatureError if the signature is invalid or malformed
				import ecdsa
				ec_pubkey = ecdsa.VerifyingKey.from_string(pubkey, curve=ecdsa.curves.SECP256k1)
				ec_pubkey.verify_digest(sig, msghash)
			case _:
				raise ValueError(f'verify_sig(): {backend}: unrecognized backend')
