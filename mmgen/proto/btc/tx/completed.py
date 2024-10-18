#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.btc.tx.completed: Bitcoin completed transaction class
"""

from ....tx import completed as TxBase
from ....obj import HexStr
from ....util import msg, die
from .base import Base, scriptPubKey2addr

class Completed(Base, TxBase.Completed):
	fn_fee_unit = 'satoshi'

	# check signature and witness data
	def check_sigs(self): # return True if sigs found, False otherwise; raise exception on error
		txins = self.deserialized.txins
		has_ss = any(ti['scriptSig'] for ti in txins)
		has_witness = any('witness' in ti and ti['witness'] for ti in txins)
		if not (has_ss or has_witness):
			return False
		fs = "Hex TX has {} scriptSig but input is of type '{}'!"
		for n, ti in enumerate(txins):
			mmti = self.inputs[n]
			if ti['scriptSig'] == '' or (len(ti['scriptSig']) == 46 and # native P2WPKH or P2SH-P2WPKH
					ti['scriptSig'][:6] == '16' + self.proto.witness_vernum_hex + '14'):
				assert 'witness' in ti, 'missing witness'
				assert isinstance(ti['witness'], list) and len(ti['witness']) == 2, 'malformed witness'
				assert len(ti['witness'][1]) == 66, 'incorrect witness pubkey length'
				assert mmti.mmtype == ('S', 'B')[ti['scriptSig']==''], fs.format('witness-type', mmti.mmtype)
			else: # non-witness
				assert mmti.mmtype not in ('S', 'B'), fs.format('signature in', mmti.mmtype)
				assert not 'witness' in ti, 'non-witness input has witness'
				# sig_size 72 (DER format), pubkey_size 'compressed':33, 'uncompressed':65
				assert (200 < len(ti['scriptSig']) < 300), 'malformed scriptSig' # VERY rough check
		return True

	def check_pubkey_scripts(self):
		for n, i in enumerate(self.inputs, 1):
			addr, fmt = scriptPubKey2addr(self.proto, i.scriptPubKey)
			if i.addr != addr:
				if fmt != i.addr.addr_fmt:
					m = 'Address format of scriptPubKey ({}) does not match that of address ({}) in input #{}'
					msg(m.format(fmt, i.addr.addr_fmt, n))
				m = 'ERROR: Address and scriptPubKey of transaction input #{} do not match!'
				die(3, (m+'\n  {:23}{}'*3).format(
					n,
					'address:',               i.addr,
					'scriptPubKey:',          i.scriptPubKey,
					'scriptPubKey->address:', addr))

#	def is_replaceable_from_rpc(self):
#		dec_tx = await self.rpc.call('decoderawtransaction', self.serialized)
#		return None < dec_tx['vin'][0]['sequence'] <= self.proto.max_int - 2

	def is_replaceable(self):
		return self.inputs[0].sequence == self.proto.max_int - 2

	@property
	def send_amt(self):
		return self.sum_outputs(
			exclude = None if len(self.outputs) == 1 else self.chg_idx
		)

	def check_txfile_hex_data(self):
		self.serialized = HexStr(self.serialized)

	def parse_txfile_serialized_data(self):
		pass

	@property
	def fee(self):
		return self.sum_inputs() - self.sum_outputs()

	@property
	def change(self):
		return self.sum_outputs() - self.send_amt

	def get_serialized_locktime(self):
		return int(bytes.fromhex(self.serialized[-8:])[::-1].hex(), 16)
