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
proto.eth.tx.info: Ethereum transaction info class
"""

from ....tx.info import TxInfo
from ....util import fmt, pp_fmt
from ....color import pink, yellow, blue
from ....addr import MMGenID

class TxInfo(TxInfo):
	txinfo_hdr_fs = 'TRANSACTION DATA\n\nID={i} ({a} {c}) Sig={s} Locktime={l}\n'
	txinfo_hdr_fs_short = 'TX {i} ({a} {c}) Sig={s} Locktime={l}\n'
	txinfo_ftr_fs = fmt("""
		Total in account:  {i} {d}
		Total to spend:    {o} {d}
		Remaining balance: {C} {d}
		TX fee:            {a} {c}{r}
	""")
	to_addr_key = 'to'

	def format_body(self, blockcount, nonmm_str, max_mmwid, enl, terse, sort):
		tx = self.tx
		m = {}
		for k in ('inputs', 'outputs'):
			if len(getattr(tx, k)):
				m[k] = getattr(tx, k)[0].mmid if len(getattr(tx, k)) else ''
				m[k] = ' ' + m[k].hl() if m[k] else ' ' + MMGenID.hlc(nonmm_str)
		fs = """
			From:      {f}{f_mmid}
			To:        {t}{t_mmid}
			Amount:    {a} {c}
			Gas price: {g} Gwei
			Start gas: {G} Kwei
			Nonce:     {n}
			Data:      {d}
		""".strip().replace('\t', '')
		t = tx.txobj
		td = t['data']
		to_addr = t[self.to_addr_key]
		return fs.format(
			f      = t['from'].hl(0),
			t      = to_addr.hl(0) if to_addr else blue('None'),
			a      = t['amt'].hl(),
			n      = t['nonce'].hl(),
			d      = '{}... ({} bytes)'.format(td[:40], len(td)//2) if len(td) else blue('None'),
			c      = tx.proto.dcoin if len(tx.outputs) else '',
			g      = yellow(tx.pretty_fmt_fee(t['gasPrice'].to_unit('Gwei'))),
			G      = yellow(tx.pretty_fmt_fee(t['startGas'].to_unit('Kwei'))),
			t_mmid = m['outputs'] if len(tx.outputs) else '',
			f_mmid = m['inputs']) + '\n\n'

	def format_abs_fee(self, color, iwidth):
		return self.tx.fee.fmt(color=color, iwidth=iwidth) + (' (max)' if self.tx.txobj['data'] else '')

	def format_rel_fee(self):
		return ' ({} of spend amount)'.format(
			pink('{:0.6f}%'.format(self.tx.fee / self.tx.send_amt * 100))
		)

	def format_verbose_footer(self):
		if self.tx.txobj['data']:
			from ..contract import parse_abi
			return '\nParsed contract data: ' + pp_fmt(parse_abi(self.tx.txobj['data']))
		else:
			return ''

class TokenTxInfo(TxInfo):
	to_addr_key = 'token_to'

	def format_rel_fee(self):
		return ''

	def format_body(self, *args, **kwargs):
		return 'Token:     {d} {c}\n{r}'.format(
			d = self.tx.txobj['token_addr'].hl(0),
			c = blue('(' + self.tx.proto.dcoin + ')'),
			r = super().format_body(*args, **kwargs))
