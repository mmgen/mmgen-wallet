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

from ....obj import ImmutableAttr
from ....addr import MoneroIdx
from ....amt import CoinAmtChk
from ....tw.unspent import TwUnspentOutputs

from .view import MoneroTwView

class MoneroTwUnspentOutputs(MoneroTwView, TwUnspentOutputs):

	hdr_lbl = 'spendable accounts'
	desc = 'spendable accounts'
	item_desc = 'account'
	include_empty = False
	total = None
	nice_addr_w = {'addr': 20}

	prompt_fs_in = [
		'Sort options: [a]mount, [A]ge, a[d]dr, [M]mgen addr, [r]everse',
		'Display options: r[e]draw screen',
		'View/Print: pager [v]iew, [w]ide pager view, [p]rint to file{s}',
		'Actions: [q]uit menu, add [l]abel, [R]efresh balances:']
	extra_key_mappings = {
		'R': 'a_sync_wallets',
		'A': 's_age'}

	sort_disp = {
		'addr':   'Addr',
		'age':    'Age',
		'amt':    'Amt',
		'twmmid': 'MMGenID'}

	# NB: For account-based views, ALL sort keys MUST begin with acct_sort_key!
	sort_funcs = {
		'addr':   lambda i: '{}:{}'.format(i.twmmid.obj.acct_sort_key, i.addr),
		'age':    lambda i: '{}:{:020}'.format(i.twmmid.obj.acct_sort_key, 0 - i.confs),
		'amt':    lambda i: '{}:{:050}'.format(i.twmmid.obj.acct_sort_key, i.amt.to_unit('atomic')),
		'twmmid': lambda i: i.twmmid.sort_key} # sort_key begins with acct_sort_key

	class MoneroMMGenTwUnspentOutput(TwUnspentOutputs.MMGenTwUnspentOutput):
		valid_attrs = {'amt', 'unlocked_amt', 'comment', 'twmmid', 'addr', 'confs', 'skip'}
		unlocked_amt = ImmutableAttr(CoinAmtChk, include_proto=True)

	def gen_data(self, rpc_data, lbl_id):
		return (
			self.MoneroMMGenTwUnspentOutput(
					self.proto,
					twmmid  = twmmid,
					addr    = data['addr'],
					confs   = data['confs'],
					comment = data['lbl'].comment,
					amt     = data['amt'],
					unlocked_amt = data['unlocked_amt'])
				for twmmid, data in rpc_data.items())

	def get_disp_data(self):
		chk_fail_msg = 'For account-based views, ALL sort keys MUST begin with acct_sort_key!'
		ad = namedtuple('accts_data', ['idx', 'acct_idx', 'total', 'unlocked_total', 'data'])
		bd = namedtuple('accts_data_data', ['disp_data_idx', 'data'])
		def gen_accts_data():
			idx, acct_idx = (None, None)
			total, unlocked_total, d_acc = (0, 0, {})
			chk_acc = [] # check for out-of-order accounts (developer idiot-proofing)
			for n, d in enumerate(self.data):
				m = d.twmmid.obj
				if idx != m.idx or acct_idx != m.acct_idx:
					if idx:
						yield ad(idx, acct_idx, total, unlocked_total, d_acc)
					chk_acc.append((m.idx, m.acct_idx))
					idx = m.idx
					acct_idx = m.acct_idx
					total = d.amt
					unlocked_total = d.unlocked_amt
					d_acc = {m.addr_idx: bd(n, d)}
				else:
					total += d.amt
					unlocked_total += d.unlocked_amt
					d_acc[m.addr_idx] = bd(n, d)
			if idx:
				assert len(set(chk_acc)) == len(chk_acc), chk_fail_msg
				yield ad(idx, acct_idx, total, unlocked_total, d_acc)
		self.accts_data = tuple(gen_accts_data())
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
		fs_acct = '{:>4} {:6} {:7}  {}'
		yield fs_acct.format('', 'Wallet', 'Account', 'Balance').ljust(self.term_width)
		for n, d in enumerate(self.accts_data):
			yield fs_acct.format(
				str(n + 1) + ')',
				d.idx.fmt(6, color=color),
				d.acct_idx.fmt(7, color=color),
				d.total.hl2(
					color = color,
					color_override = None if d.total == d.unlocked_total else 'orange'
				)).ljust(self.term_width)
			for v in d.data.values():
				yield fmt_method(None, v.data, cw, fs, color, None, None)

	def squeezed_format_line(self, n, d, cw, fs, color, yes, no):
		return fs.format(
			I = d.twmmid.obj.addr_idx.fmt(cw.addr_idx, color=color),
			a = d.addr.fmt(self.addr_view_pref, cw.addr, color=color),
			c = d.comment.fmt2(cw.comment, color=color, nullrepl='-'),
			A = d.amt.fmt2(
				cw.iwidth,
				color = color,
				color_override = None if d.amt == d.unlocked_amt else 'orange',
				prec = self.disp_prec))

	async def get_idx_from_user(self):
		if res := await self.get_idx(f'{self.item_desc} number', self.accts_data):
			return await self.get_idx(
				'address index',
				self.accts_data[res.idx - 1].data,
				is_addr_idx = True)
