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
proto.rune.tx.protobuf: transaction serialization for THORChain protocol
"""

# https://dev.thorchain.org/technical-faq.html

from decimal import Decimal
from collections import namedtuple
from dataclasses import dataclass #, field
from typing import Annotated, List, Optional
from pure_protobuf.annotations import Field
from pure_protobuf.message import BaseMessage

from ...secp256k1.util import sign_message

from ...cosmos.tx.protobuf import (
	ModeInfo,
	SignDoc,
	SignerInfo,
	SignMode,
	PublicKey,
	PublicKeyData,
	Coin,
	Fee,
	AuthInfo,
	Tx,
	TxMsg)

send_tx_parms = namedtuple(
	'rune_send_tx_parms', [
		'from_addr',
		'to_addr',
		'amt',
		'gas_limit',
		'account_number',
		'sequence',
		'pubkey',
		'wifkey',
		'signature'],
		defaults = (None, None, None))

deposit_tx_parms = namedtuple(
	'rune_deposit_tx_parms', [
		'chain',
		'symbol',
		'ticker',
		'from_addr',
		'amt',
		'gas_limit',
		'account_number',
		'sequence',
		'decimals',
		'memo',
		'synth', # begin default fields
		'trade',
		'secured',
		'pubkey',
		'wifkey',
		'signature'],
		defaults = (None, None, None, None, None, None))

# subset of deposit_tx_parms:
swap_tx_parms = namedtuple(
	'rune_swap_tx_parms', [
		'from_addr',
		'amt',
		'gas_limit',
		'account_number',
		'sequence',
		'memo',
		'pubkey', # begin default fields
		'wifkey',
		'signature'],
		defaults = (None, None, None))

@dataclass
class Asset(BaseMessage):
	chain:   Annotated[str, Field(1)]
	symbol:  Annotated[str, Field(2)]
	ticker:  Annotated[str, Field(3)]
	synth:   Annotated[Optional[bool], Field(4)] = None
	trade:   Annotated[Optional[bool], Field(5)] = None
	secured: Annotated[Optional[bool], Field(6)] = None

@dataclass
class CoinWithAsset(BaseMessage):
	asset:    Annotated[Asset, Field(1)]
	amount:   Annotated[str, Field(2)]
	decimals: Annotated[Optional[int], Field(3)] = None

class Messages:

	@dataclass
	class MsgSend(BaseMessage):

		@dataclass
		class Body(BaseMessage):
			fromAddress: Annotated[bytes, Field(1)]
			toAddress:   Annotated[bytes, Field(2)]
			amount:      Annotated[List[Coin], Field(3)]

		id:   Annotated[str, Field(1)] # '/types.MsgSend'
		body: Annotated[Body, Field(2)]

	@dataclass
	class MsgDeposit(BaseMessage):
	# To initiate a $RUNE -> $ASSET swap a MsgDeposit must be broadcasted to the THORChain blockchain.
	# The MsgDeposit does not have a destination address, and has the following properties.
	# MsgDeposit{
	#     Coins:  coins,
	#     Memo:   memo,
	#     Signer: signer,
	# }
		@dataclass
		class Body(BaseMessage):
			coins:  Annotated[List[CoinWithAsset], Field(1)]
			memo:   Annotated[str, Field(2)]
			signer: Annotated[bytes, Field(3)]

		id:   Annotated[str, Field(1)] # '/types.MsgDeposit'
		body: Annotated[Body, Field(2)]

@dataclass
class RuneTxMsg(TxMsg):
	msgs_cls = Messages
	id:        Annotated[str, Field(1)]
	bodyBytes: Annotated[bytes, Field(2)]

@dataclass
class RuneTxBody(BaseMessage):
	messages:                    Annotated[List[RuneTxMsg], Field(1)]
	memo:                        Annotated[Optional[str], Field(2)] = None
	timeoutHeight:               Annotated[Optional[int], Field(3)] = None
	extensionOptions:            Annotated[Optional[bytes], Field(4)] = None
	nonCriticalExtensionOptions: Annotated[Optional[bytes], Field(5)] = None

@dataclass
class RuneTx(Tx):
	body:       Annotated[RuneTxBody, Field(1)]
	authInfo:   Annotated[AuthInfo, Field(2)]
	signatures: Annotated[List[bytes], Field(3)]

def amt_to_base_unit(amt, *, decimals):
	return int(Decimal(amt) * (Decimal('10') ** decimals))

def base_unit_to_amt(n, *, decimals):
	return n * Decimal('10') ** -decimals

def tx_info(tx, proto):
	b = tx.body.messages[0].body
	s = tx.authInfo.signerInfos[0]
	match msg_type := tx.body.messages[0].id.removeprefix('/types.'):
		case 'MsgSend':
			from_addr = proto.encode_addr_bech32x(b.fromAddress)
			to_addr   = proto.encode_addr_bech32x(b.toAddress)
			asset     = b.amount[0].denom.upper()
			memo      = tx.body.memo
			amt       = base_unit_to_amt(int(b.amount[0].amount), decimals=8)
		case 'MsgDeposit':
			from_addr = proto.encode_addr_bech32x(b.signer)
			to_addr = 'None'
			asset     = b.coins[0].asset.symbol
			memo      = b.memo
			amt       = base_unit_to_amt(int(b.coins[0].amount), decimals=b.coins[0].decimals or 8)
	yield f'TxID:      {tx.txid}'
	yield f'Type:      {msg_type}'
	yield f'From:      {from_addr}'
	yield f'To:        {to_addr}'
	yield f'Asset:     {asset}'
	yield f'Amount:    {amt}'
	yield f'Sequence:  {int(s.sequence)}'
	yield f'Gas limit: {tx.authInfo.fee.gasLimit}'
	yield f'Memo:      {memo}'
	yield f'Pubkey:    {s.publicKey.key.data.hex()}'

def build_swap_tx(cfg, proto, parms, *, skip_body_memo=False):

	p = parms
	assert type(p) == swap_tx_parms, f'{p}: invalid ‘parms’ (not swap_tx_parms instance)'

	return build_tx(
			cfg,
			proto,
			deposit_tx_parms(
				chain = 'THOR',
				symbol = 'RUNE',
				ticker = 'RUNE',
				from_addr = p.from_addr,
				amt = p.amt,
				gas_limit = p.gas_limit,
				account_number = p.account_number,
				sequence = p.sequence,
				decimals = 8,
				memo = p.memo,
				pubkey = p.pubkey,
				wifkey = p.wifkey,
				signature = p.signature),
			skip_body_memo = skip_body_memo)

def build_tx(cfg, proto, parms, *, null_fee=False, skip_body_memo=False):

	p = parms
	assert type(p) in (send_tx_parms, deposit_tx_parms), f'{p}: invalid ‘parms’ (not *_tx_parms instance)'

	msg_type = 'MsgSend' if type(p) == send_tx_parms else 'MsgDeposit'

	if p.wifkey:
		assert p.pubkey is None and p.signature is None
		from ....key import PrivKey
		from ....keygen import KeyGenerator
		privkey = PrivKey(proto=proto, wif=p.wifkey)
		pubkey = KeyGenerator(cfg, proto, 'std').to_pubkey(privkey)
	else:
		assert p.pubkey and p.signature
		pubkey = p.pubkey

	cls = getattr(Messages, msg_type)

	if msg_type == 'MsgSend':
		message = cls(
			id   = '/types.MsgSend',
			body = cls.Body(
				fromAddress = proto.decode_addr(p.from_addr).bytes,
				toAddress = proto.decode_addr(p.to_addr).bytes,
				amount = [Coin(denom='rune', amount=str(amt_to_base_unit(p.amt, decimals=8)))]))
		fee_amt = None
	elif msg_type == 'MsgDeposit':
		coin_data = CoinWithAsset(
			asset = Asset(
				chain = p.chain,
				symbol = p.symbol,
				ticker = p.ticker,
				synth = p.synth,
				trade = p.trade,
				secured = p.secured),
			amount = str(amt_to_base_unit(p.amt, decimals=p.decimals or 8)),
			decimals = p.decimals)
		message = cls(
			id   = '/types.MsgDeposit',
			body = cls.Body(
				coins = [coin_data],
				memo = p.memo,
				signer = proto.decode_addr(p.from_addr).bytes))
		fee_amt = None if null_fee else [Coin(denom='rune', amount='0')]

	signer_info = SignerInfo(
		publicKey = PublicKey(
			id = '/cosmos.crypto.secp256k1.PubKey',
			key = PublicKeyData(data=pubkey)),
		modeInfo = ModeInfo(
			single = ModeInfo.Single(mode=SignMode.SIGN_MODE_DIRECT),
			multi = None),
		sequence = p.sequence)

	body = RuneTxBody(messages=[message], memo=None if skip_body_memo else getattr(p, 'memo', None))

	auth_info = AuthInfo(signerInfos=[signer_info], fee=Fee(gasLimit=p.gas_limit, amount=fee_amt))

	# cosmjs/packages/crypto/src/secp256k1signature.ts
	# cosmjs/packages/amino/src/signature.ts
	#   Signature must be 64 bytes long. Cosmos SDK uses a 2x32 byte fixed length
	#   encoding for the secp256k1 signature integers r and s.
	signature = sign_message(
		sign_doc = SignDoc(
			bodyBytes = bytes(body),
			authInfoBytes = bytes(auth_info),
			chainId = proto.chain_id,
			accountNumber = p.account_number),
		sec_bytes = privkey) if p.wifkey else p.signature

	return RuneTx(body=body, authInfo=auth_info, signatures=[signature])
