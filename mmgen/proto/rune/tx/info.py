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
proto.rune.tx.info: THORChain transaction info class
"""

from ....tx.info import TxInfo
from ....color import pink
from ....obj import NonNegativeInt

from ...vm.tx.info import VmTxInfo, mmid_disp

class TxInfo(VmTxInfo, TxInfo):

	def format_body(self, blockcount, nonmm_str, max_mmwid, enl, *, terse, sort):
		tx = self.tx
		t = tx.txobj
		fs = """
			From:      {f}{f_mmid}
			Amount:    {a} {c}
			Gas limit: {G}
			Sequence:  {N}
			Memo:      {m}
		""" if tx.is_swap else """
			From:      {f}{f_mmid}
			To:        {t}{t_mmid}
			Amount:    {a} {c}
			Gas limit: {G}
			Sequence:  {N}
		"""
		return fs.strip().replace('\t', '').format(
			f      = t['from'].hl(0),
			t      = None if tx.is_swap else t['to'].hl(0),
			a      = t['amt'].hl(),
			N      = NonNegativeInt(t['sequence']).hl(),
			m      = pink(tx.swap_memo) if tx.is_swap else None,
			c      = tx.proto.dcoin if tx.outputs else '',
			G      = NonNegativeInt(tx.total_gas).hl(),
			f_mmid = mmid_disp(tx.inputs[0], nonmm_str),
			t_mmid = None if tx.is_swap else mmid_disp(tx.outputs[0], nonmm_str)) + '\n\n'

	def format_abs_fee(self, iwidth, /, *, color=None):
		return self.tx.fee.fmt(iwidth, color=color)

	def format_rel_fee(self):
		return ''

	def format_verbose_footer(self):
		return ''
