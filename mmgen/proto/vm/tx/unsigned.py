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
proto.vm.tx.unsigned: unsigned transaction methods for VM chains
"""

from ....util import msg, msg_r, die

class Unsigned:
	desc = 'unsigned transaction'

	# Return signed object or False. Don’t exit or raise exception:
	async def sign(self, keys, tx_num_str=''):

		from ....exception import TransactionChainMismatch
		try:
			self.check_correct_chain()
		except TransactionChainMismatch:
			return False

		o = self.txobj

		def do_mismatch_err(io, j, k, desc):
			m = 'A compromised online installation may have altered your serialized data!'
			fs = '\n{} mismatch!\n{}\n  orig:       {}\n  serialized: {}'
			die(3, fs.format(desc.upper(), m, getattr(io[0], k), o[j]))

		if o['from'] != self.inputs[0].addr:
			do_mismatch_err(self.inputs, 'from', 'addr', 'from-address')
		if self.outputs:
			if o['to'] != self.outputs[0].addr:
				do_mismatch_err(self.outputs, 'to', 'addr', 'to-address')
			if o['amt'] != self.outputs[0].amt:
				do_mismatch_err(self.outputs, 'amt', 'amt', 'amount')

		msg_r(f'Signing transaction{tx_num_str}...')

		try:
			await self.do_sign(o, keys[0].sec.wif)
			msg('OK')
			from ....tx import SignedTX
			tx = SignedTX(cfg=self.cfg, data=self.__dict__, automount=self.automount)
			tx.check_serialized_integrity()
			return tx
		except Exception as e:
			msg(f'{e}: transaction signing failed!')
			return False
