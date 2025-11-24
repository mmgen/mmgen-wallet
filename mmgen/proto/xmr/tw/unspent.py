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
proto.xmr.tw.unspent: Monero protocol tracking wallet unspent outputs class
"""

from collections import namedtuple

from ....tw.unspent import TwUnspentOutputs
from ....addr import MMGenID, MoneroIdx
from ....color import red, green

from .view import MoneroTwView

class MoneroTwUnspentOutputs(MoneroTwView, TwUnspentOutputs):

	hdr_lbl = 'spendable accounts'
	desc = 'spendable accounts'
	item_desc = 'account'
	account_based = True
	include_empty = False
	total = None
	nice_addr_w = {'addr': 20}

	prompt_fs_repl = {'XMR': (
		(1, 'Display options: r[e]draw screen'),
		(3, 'Actions: [q]uit menu, add [l]abel, [R]efresh balances:'))}
	extra_key_mappings = {
		'R': 'a_sync_wallets'}

	sort_disp = {
		'addr':   'Addr',
		'age':    'Age',
		'amt':    'Amt',
		'twmmid': 'MMGenID'}

	sort_funcs = {
		'addr':   lambda i: '{}:{}'.format(i.twmmid.obj.acct_sort_key, i.addr),
		'age':    lambda i: i.twmmid.sort_key, # dummy (age sort not supported)
		'amt':    lambda i: '{}:{:050}'.format(i.twmmid.obj.acct_sort_key, i.amt.to_unit('atomic')),
		'twmmid': lambda i: i.twmmid.sort_key}

	def gen_data(self, rpc_data, lbl_id):
		return (
			self.MMGenTwUnspentOutput(
					self.proto,
					twmmid  = twmmid,
					addr    = data['addr'],
					confs   = data['confs'],
					comment = data['lbl'].comment,
					amt     = data['amt'])
				for twmmid, data in rpc_data.items())

	def get_disp_data(self):
		ad = namedtuple('accts_data', ['total', 'data'])
		bd = namedtuple('accts_data_data', ['disp_data_idx', 'data'])
		def gen_accts_data():
			acct_id_save, total, d_acc = (None, 0, {})
			for n, d in enumerate(self.data):
				m = d.twmmid.obj
				if acct_id_save != m.acct_id:
					if acct_id_save:
						yield (acct_id_save, ad(total, d_acc))
					acct_id_save = m.acct_id
					total = d.amt
					d_acc = {m.addr_idx: bd(n, d)}
				else:
					total += d.amt
					d_acc[m.addr_idx] = bd(n, d)
			if acct_id_save:
				yield (acct_id_save, ad(total, d_acc))
		self.accts_data = dict(gen_accts_data())
		return super().get_disp_data()

	class display_type(TwUnspentOutputs.display_type):

		class squeezed(TwUnspentOutputs.display_type.squeezed):
			cols = ('addr_idx', 'addr', 'comment', 'amt')
			colhdr_fmt_method = None
			fmt_method = 'gen_display'

		class detail(TwUnspentOutputs.display_type.detail):
			cols = ('addr_idx', 'addr', 'amt', 'comment')
			colhdr_fmt_method = None
			fmt_method = 'gen_display'
			line_fmt_method = 'squeezed_format_line'

	def get_column_widths(self, data, *, wide, interactive):
		return self.compute_column_widths(
			widths = { # fixed cols
				'addr_idx': MoneroIdx.max_digits,
				'amt': self.amt_widths['amt'],
				'spc': 4}, # 1 leading space plus 3 spaces between 4 cols
			maxws = { # expandable cols
				'addr': max(len(d.addr) for d in data),
				'comment': max(d.comment.screen_width for d in data)},
			minws = {
				'addr': 16,
				'comment': len('Comment')},
			maxws_nice = self.nice_addr_w,
			wide = wide,
			interactive = interactive)

	def gen_display(self, data, cw, fs, color, fmt_method):
		yes, no = (red('Yes '), green('No  ')) if color else ('Yes ', 'No  ')
		fs_acct = '{:>4} {} {:%s}  {}' % MoneroIdx.max_digits
		wallet_wid = 15
		yield '     Wallet        Account  Balance'.ljust(self.term_width)
		for n, (k, v) in enumerate(self.accts_data.items()):
			mmid, acct_idx = k.rsplit(':', 1)
			m = list(v.data.values())[0].data.twmmid.obj
			yield fs_acct.format(
				str(n + 1) + ')',
				MMGenID.hlc(mmid.ljust(wallet_wid), color=color),
				m.acct_idx.fmt(MoneroIdx.max_digits, color=color),
				v.total.hl(color=color)).ljust(self.term_width)
			for v in v.data.values():
				yield fmt_method(None, v.data, cw, fs, color, yes, no)

	def squeezed_format_line(self, n, d, cw, fs, color, yes, no):
		return fs.format(
			I = d.twmmid.obj.addr_idx.fmt(cw.addr_idx, color=color),
			a = d.addr.fmt(self.addr_view_pref, cw.addr, color=color),
			c = d.comment.fmt2(cw.comment, color=color, nullrepl='-'),
			A = d.amt.fmt(cw.iwidth, color=color, prec=self.disp_prec))
