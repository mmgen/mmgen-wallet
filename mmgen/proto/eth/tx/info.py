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
proto.eth.tx.info: Ethereum transaction info class
"""

from ....tx.info import TxInfo
from ....color import red, yellow, blue, cyan, pink
from ....obj import NonNegativeInt

from ...vm.tx.info import VmTxInfo, mmid_disp

class TxInfo(VmTxInfo, TxInfo):

	to_addr_key = 'to'

	def format_body(self, blockcount, nonmm_str, max_mmwid, enl, *, terse, sort):
		tx = self.tx
		t = tx.txobj
		td = t['data']
		to_addr = t[self.to_addr_key]
		tokenswap = tx.is_swap and tx.is_token
		fs = """
			From:      {f}{f_mmid}
			{toaddr}   {t}{t_mmid}{tvault}
			Amount:    {a} {c}
			Gas price: {g} Gwei
			Gas limit: {G}{G_dec}
			Nonce:     {n}
			Data:      {d}
		""".strip().replace('\t', '') + ('\nMemo:      {m}' if tx.is_swap else '')
		return fs.format(
			f      = t['from'].hl(0),
			t      = to_addr.hl(0) if to_addr else blue('None'),
			a      = t['amt'].hl(),
			toaddr = ('Router:' if tokenswap else 'Vault:' if tx.is_swap else 'To:').ljust(8),
			tvault = (f'\nVault:     {cyan(tx.token_vault_addr)}' if tokenswap else ''),
			n      = t['nonce'].hl(),
			d      = blue('None') if not td else '{}... ({} bytes)'.format(td[:40], len(td)//2),
			m      = pink(tx.swap_memo) if tx.is_swap else None,
			c      = tx.proto.dcoin if len(tx.outputs) else '',
			g      = yellow(tx.pretty_fmt_fee(t['gasPrice'].to_unit('Gwei'))),
			G      = NonNegativeInt(tx.total_gas).hl(),
			G_dec  = red(f" ({t['startGas']} + {t['router_gas']})") if tokenswap else '',
			f_mmid = mmid_disp(tx.inputs[0], nonmm_str),
			t_mmid = mmid_disp(tx.outputs[0], nonmm_str) if tx.outputs and not tx.is_swap else '') + '\n\n'

	def format_abs_fee(self, iwidth, /, *, color=None):
		return self.tx.fee.fmt(iwidth, color=color) + (' (max)' if self.tx.txobj['data'] else '')

	def format_rel_fee(self):
		return ' ({} of spend amount)'.format(
			pink('{:0.6f}%'.format(self.tx.fee / self.tx.send_amt * 100))
		)

	def format_verbose_footer(self):
		if self.tx.txobj['data'] and not self.tx.is_swap:
			from ....util import pp_fmt
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
