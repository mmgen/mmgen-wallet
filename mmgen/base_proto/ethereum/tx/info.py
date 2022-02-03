#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
base_proto.ethereum.tx.info: Ethereum transaction info class
"""

from ....tx.info import TxInfo
from ....util import fmt,pp_fmt
from ....color import pink,yellow,blue
from ....addr import MMGenID
from ....obj import Str

class TxInfo(TxInfo):
	txinfo_hdr_fs = 'TRANSACTION DATA\n\nID={i} ({a} {c}) UTC={t} Sig={s} Locktime={l}\n'
	txinfo_hdr_fs_short = 'TX {i} ({a} {c}) UTC={t} Sig={s} Locktime={l}\n'
	txinfo_ftr_fs = fmt("""
		Total in account:  {i} {d}
		Total to spend:    {o} {d}
		Remaining balance: {C} {d}
		TX fee:            {a} {c}{r}
	""")
	fmt_keys = ('from','to','amt','nonce')

	def format_body(self,blockcount,nonmm_str,max_mmwid,enl,terse,sort):
		tx = self.tx
		m = {}
		for k in ('inputs','outputs'):
			if len(getattr(tx,k)):
				m[k] = getattr(tx,k)[0].mmid if len(getattr(tx,k)) else ''
				m[k] = ' ' + m[k].hl() if m[k] else ' ' + MMGenID.hlc(nonmm_str)
		fs = """From:      {}{f_mmid}
				To:        {}{t_mmid}
				Amount:    {} {c}
				Gas price: {g} Gwei
				Start gas: {G} Kwei
				Nonce:     {}
				Data:      {d}
				\n""".replace('\t','')
		t = tx.txobj
		td = t['data']
		return fs.format(
			*((t[k] if t[k] != '' else Str('None')).hl() for k in self.fmt_keys),
			d      = '{}... ({} bytes)'.format(td[:40],len(td)//2) if len(td) else Str('None'),
			c      = tx.proto.dcoin if len(tx.outputs) else '',
			g      = yellow(str(t['gasPrice'].to_unit('Gwei',show_decimal=True))),
			G      = yellow(str(t['startGas'].to_unit('Kwei'))),
			t_mmid = m['outputs'] if len(tx.outputs) else '',
			f_mmid = m['inputs'] )

	def format_abs_fee(self):
		return self.tx.fee.hl() + (' (max)' if self.tx.txobj['data'] else '')

	def format_rel_fee(self,terse):
		return ' ({} of spend amount)'.format(
			pink('{:0.6f}%'.format( self.tx.fee / self.tx.send_amt * 100 ))
		)

	def format_verbose_footer(self):
		if self.tx.txobj['data']:
			from ..contract import parse_abi
			return '\nParsed contract data: ' + pp_fmt(parse_abi(self.tx.txobj['data']))
		else:
			return ''

class TokenTxInfo(TxInfo):
	fmt_keys = ('from','token_to','amt','nonce')

	def format_rel_fee(self,terse):
		return ''

	def format_body(self,*args,**kwargs):
		return 'Token:     {d} {c}\n{r}'.format(
			d = self.tx.txobj['token_addr'].hl(),
			c = blue('(' + self.tx.proto.dcoin + ')'),
			r = super().format_body(*args,**kwargs ))
