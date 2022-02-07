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
tx.info: transaction info class
"""

from ..globalvars import *
from ..color import red,green,orange
from ..opts import opt
from ..util import msg,msg_r

import importlib

class TxInfo:

	def __init__(self,tx):
		self.tx = tx

	def format(self,terse=False,sort='addr'):

		tx = self.tx

		if tx.proto.base_proto == 'Ethereum':
			blockcount = None
		else:
			try:
				blockcount = tx.rpc.blockcount
			except:
				blockcount = None

		def get_max_mmwid(io):
			if io == tx.inputs:
				sel_f = lambda o: len(o.mmid) + 2 # len('()')
			else:
				sel_f = lambda o: len(o.mmid) + (2,8)[bool(o.is_chg)] # + len(' (chg)')
			return  max(max([sel_f(o) for o in io if o.mmid] or [0]),len(nonmm_str))

		nonmm_str = f'(non-{g.proj_name} address)'
		max_mmwid = max(get_max_mmwid(tx.inputs),get_max_mmwid(tx.outputs))

		def gen_view():
			yield (self.txinfo_hdr_fs_short if terse else self.txinfo_hdr_fs).format(
				i = tx.txid.hl(),
				a = tx.send_amt.hl(),
				c = tx.dcoin,
				t = tx.timestamp,
				r = green('True') if tx.is_replaceable() else red('False'),
				s = green('True') if tx.signed else red('False'),
				l = (
					orange(self.strfmt_locktime(terse=True)) if tx.locktime else
					green('None') ))

			if tx.chain != 'mainnet': # if mainnet has a coin-specific name, display it
				yield green(f'Chain: {tx.chain.upper()}') + '\n'

			if tx.coin_txid:
				yield f'{tx.coin} TxID: {tx.coin_txid.hl()}\n'

			enl = ('\n','')[bool(terse)]
			yield enl

			if tx.label:
				yield f'Comment: {tx.label.hl()}\n{enl}'

			yield self.format_body(blockcount,nonmm_str,max_mmwid,enl,terse=terse,sort=sort)

			yield self.txinfo_ftr_fs.format(
				i = tx.sum_inputs().hl(),
				o = tx.sum_outputs().hl(),
				C = tx.change.hl(),
				s = tx.send_amt.hl(),
				a = self.format_abs_fee(),
				r = self.format_rel_fee(terse),
				d = tx.dcoin,
				c = tx.coin )

			if opt.verbose:
				yield self.format_verbose_footer()

		return ''.join(gen_view()) # TX label might contain non-ascii chars

	def view_with_prompt(self,prompt,pause=True):
		prompt += ' (y)es, (N)o, pager (v)iew, (t)erse view: '
		from ..term import get_char
		while True:
			reply = get_char( prompt, immed_chars='YyNnVvTt' ).strip('\n\r')
			msg('')
			if reply == '' or reply in 'Nn':
				break
			elif reply in 'YyVvTt':
				self.view(
					pager = reply in 'Vv',
					pause = pause,
					terse = reply in 'Tt' )
				break
			else:
				msg('Invalid reply')

	def view(self,pager=False,pause=True,terse=False):
		o = self.format(terse=terse)
		if pager:
			do_pager(o)
		else:
			msg_r(o)
			from ..term import get_char
			if pause:
				get_char('Press any key to continue: ')
				msg('')

def init_info(tx):
	return getattr(
		importlib.import_module(f'mmgen.base_proto.{tx.proto.base_proto.lower()}.tx.info'),
		('Token' if tx.proto.tokensym else '') + 'TxInfo' )(tx)