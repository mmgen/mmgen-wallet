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
tx.info: transaction info class
"""

import importlib

from ..cfg import gc
from ..color import red, green, cyan, orange, blue, yellow, magenta
from ..util import msg, msg_r, decode_timestamp, make_timestr
from ..util2 import format_elapsed_hr

class TxInfo:

	def __init__(self, cfg, tx):
		self.cfg = cfg
		self.tx = tx

	def format(self, *, terse=False, sort='addr'):

		tx = self.tx

		if tx.is_swap:
			sort = 'raw'

		if tx.proto.base_proto == 'Ethereum':
			blockcount = None
		else:
			try:
				blockcount = tx.rpc.blockcount
			except:
				blockcount = None

		def get_max_mmwid(io):
			sel_f = (
				(lambda o: len(o.mmid) + 2) if io == tx.inputs else  # 2 = len('()')
				(lambda o: len(o.mmid) + (2, 8)[bool(o.is_chg)]))    # 6 = len(' (chg)')
			return max(max([sel_f(o) for o in io if o.mmid] or [0]), len(nonmm_str))

		nonmm_str = f'(non-{gc.proj_name} address)'
		max_mmwid = max(get_max_mmwid(tx.inputs), get_max_mmwid(tx.outputs))

		def gen_view():
			yield (self.txinfo_hdr_fs_short if terse else self.txinfo_hdr_fs).format(
				hdr = cyan(('SWAP ' if tx.is_swap else '') + 'TRANSACTION DATA'),
				i = tx.txid.hl(),
				a = tx.send_amt.hl(),
				c = tx.dcoin,
				r = green('True') if tx.is_replaceable() else red('False'),
				s = green('True') if tx.signed else red('False'),
				l = (
					orange(self.strfmt_locktime(terse=True)) if tx.locktime else
					green('None')))

			for attr, label in [('timestamp', 'Created:'), ('sent_timestamp', 'Sent:')]:
				if (val := getattr(tx, attr)) is not None:
					_ = decode_timestamp(val)
					yield f'  {label:8} {make_timestr(_)} ({format_elapsed_hr(_)})\n'

			if tx.chain != 'mainnet': # if mainnet has a coin-specific name, display it
				yield green(f'  Chain: {tx.chain.upper()}') + '\n'

			if tx.coin_txid:
				yield f'  {tx.coin} TxID: {tx.coin_txid.hl()}\n'

			if tx.is_swap:
				from ..swap.proto.thorchain import Memo, name
				data = tx.swap_memo.encode() if tx.proto.is_vm else tx.data_output.data
				if Memo.is_partial_memo(data):
					recv_mmid = getattr(tx, 'swap_recv_addr_mmid', None)
					p = Memo.parse(data.decode('ascii'))
					yield '  {} {}\n'.format(magenta('DEX Protocol:'), blue(name))
					yield '    Swap: {}\n'.format(orange(f'{tx.send_asset.name} => {tx.recv_asset.name}'))
					yield '    Dest: {}{}\n'.format(
						cyan(p.address),
						orange(f' {recv_mmid}') if recv_mmid else '')
					if not recv_mmid:
						yield yellow('    Warning: swap destination address is not a wallet address!\n')

			enl = ('\n', '')[bool(terse)]
			yield enl

			if tx.comment:
				yield f'  Comment: {tx.comment.hl()}\n{enl}'

			yield self.format_body(
				blockcount,
				nonmm_str,
				max_mmwid,
				enl,
				terse = terse,
				sort  = sort)

			iwidth = len(str(int(tx.sum_inputs())))

			yield self.txinfo_ftr_fs.format(
				i = tx.sum_inputs().fmt(iwidth, color=True),
				o = tx.sum_outputs().fmt(iwidth, color=True),
				C = tx.change.fmt(iwidth, color=True),
				s = tx.send_amt.fmt(iwidth, color=True),
				a = self.format_abs_fee(iwidth, color=True),
				r = self.format_rel_fee(),
				d = tx.dcoin,
				c = tx.coin)

			if tx.cfg.verbose:
				yield self.format_verbose_footer()

		return ''.join(gen_view())

	def view_with_prompt(self, prompt, *, pause=True):
		prompt += ' (y)es, (N)o, pager (v)iew, (t)erse view: '
		from ..term import get_char
		while True:
			reply = get_char(prompt, immed_chars='YyNnVvTt').strip('\n\r')
			msg('')
			if reply == '' or reply in 'Nn':
				break
			if reply in 'YyVvTt':
				self.view(
					pager = reply in 'Vv',
					pause = pause,
					terse = reply in 'Tt')
				break
			msg('Invalid reply')

	def view(self, *, pager=False, pause=True, terse=False):
		o = self.format(terse=terse)
		if pager:
			from ..ui import do_pager
			do_pager(o)
		else:
			msg('')
			msg_r(o)
			from ..term import get_char
			if pause:
				get_char('Press any key to continue: ')
				msg('')

def init_info(cfg, tx):
	return getattr(
		importlib.import_module(f'mmgen.proto.{tx.proto.base_proto_coin.lower()}.tx.info'),
		('Token' if tx.proto.tokensym else '') + 'TxInfo')(cfg, tx)
