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
proto.rune.tx.base: THORChain base transaction class
"""

from ....tx.base import Base as TxBase

class Base(TxBase):

	dfl_fee = 2000000
	dfl_gas = 800000
	usr_contract_data = None
	disable_fee_check = False

	@property
	def nondata_outputs(self):
		return self.outputs

	@property
	def usr_fee(self):
		return self.proto.coin_amt(self.dfl_fee, from_unit='satoshi')

	def add_blockcount(self):
		pass

	def is_replaceable(self):
		return False

	def check_serialized_integrity(self):
		if self.signed:
			from .protobuf import RuneTx
			tx = RuneTx.loads(bytes.fromhex(self.serialized))

			o = self.txobj
			b = tx.body.messages[0].body

			if self.is_swap:
				from_k, amt_k = ('signer', 'coins')
				if b.memo != self.swap_memo:
					raise ValueError(f'{b.memo}: invalid swap memo in serialized data')
			else:
				from_k, amt_k = ('fromAddress', 'amount')
				if s := self.proto.encode_addr_bech32x(b.toAddress) != o['to']:
					raise ValueError(f'{s}: invalid ‘to’ address in serialized data')

			if s := self.proto.encode_addr_bech32x(getattr(b, from_k)) != o['from']:
				raise ValueError(f'{s}: invalid {from_k} in serialized data')

			if d := self.proto.coin_amt(int(getattr(b, amt_k)[0].amount), from_unit='satoshi') != o['amt']:
				raise ValueError(f'{d}: invalid send amount in serialized data')

			if n := tx.authInfo.signerInfos[0].sequence != o['sequence']:
				raise ValueError(f'{n}: invalid sequence number in serialized data')
