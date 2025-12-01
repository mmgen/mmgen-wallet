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
proto.xmr.tw.view: Monero protocol base class for tracking wallet view classes
"""

from collections import namedtuple

from ....obj import ImmutableAttr
from ....color import red, green
from ....addr import MoneroIdx
from ....amt import CoinAmtChk
from ....seed import SeedID
from ....xmrwallet import op as xmrwallet_op
from ....tw.view import TwView
from ....tw.unspent import TwUnspentOutputs

class MoneroTwView:

	is_account_based = True
	item_desc = 'account'
	nice_addr_w = {'addr': 20}
	total = None

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

	class MoneroTwViewItem(TwUnspentOutputs.MMGenTwUnspentOutput):
		valid_attrs = {'amt', 'unlocked_amt', 'comment', 'twmmid', 'addr', 'confs', 'is_used', 'skip'}
		unlocked_amt = ImmutableAttr(CoinAmtChk, include_proto=True)
		is_used = ImmutableAttr(bool)

	class rpc:
		caps = ()
		is_remote = False

	async def get_rpc_data(self):
		from mmgen.tw.shared import TwMMGenID, TwLabel

		op = xmrwallet_op('dump_data', self.cfg, None, None, compat_call=True)
		await op.restart_wallet_daemon()
		wallets_data = await op.main()

		if wallets_data:
			self.sid = SeedID(sid=wallets_data[0]['seed_id'])

		self.total = self.unlocked_total = self.proto.coin_amt('0')

		def gen_addrs():
			bd = namedtuple('address_balance_data', ['bal', 'unlocked_bal', 'blocks_to_unlock'])
			for wdata in wallets_data:
				bals_data = {i: {} for i in range(len(wdata['data'].accts_data['subaddress_accounts']))}

				for d in wdata['data'].bals_data.get('per_subaddress', []):
					bals_data[d['account_index']].update({
						d['address_index']: bd(
							d['balance'],
							d['unlocked_balance'],
							d['blocks_to_unlock'])})

				for acct_idx, acct_data in enumerate(wdata['data'].addrs_data):
					for addr_data in acct_data['addresses']:
						addr_idx = addr_data['address_index']
						addr_bals = bals_data[acct_idx].get(addr_idx)
						bal = self.proto.coin_amt(
							addr_bals.bal if addr_bals else 0,
							from_unit = 'atomic')
						unlocked_bal = self.proto.coin_amt(
							addr_bals.unlocked_bal if addr_bals else 0,
							from_unit = 'atomic')
						if bal or self.include_empty:
							self.total += bal
							self.unlocked_total += unlocked_bal
							mmid = '{}:M:{}-{}/{}'.format(
								wdata['seed_id'],
								wdata['wallet_num'],
								acct_idx,
								addr_idx)
							btu = addr_bals.blocks_to_unlock if addr_bals else 0
							if not btu and bal != unlocked_bal:
								btu = 12
							yield (TwMMGenID(self.proto, mmid), {
								'addr':    addr_data['address'],
								'amt':     bal,
								'unlocked_amt': unlocked_bal,
								'recvd':   bal,
								'is_used': addr_data['used'],
								'confs':   11 - btu,
								'lbl':     TwLabel(self.proto, mmid + ' ' + addr_data['label'])})

		return dict(gen_addrs())

	def gen_data(self, rpc_data, lbl_id):
		return (
			self.MoneroTwViewItem(
					self.proto,
					twmmid  = twmmid,
					addr    = data['addr'],
					confs   = data['confs'],
					is_used = data['is_used'],
					comment = data['lbl'].comment,
					amt     = data['amt'],
					unlocked_amt = data['unlocked_amt'])
				for twmmid, data in rpc_data.items())

	def get_disp_data(self, input_data=None):
		data = self.data if input_data is None else input_data
		chk_fail_msg = 'For account-based views, ALL sort keys MUST begin with acct_sort_key!'
		ad = namedtuple('accts_data', ['idx', 'acct_idx', 'total', 'unlocked_total', 'data'])
		bd = namedtuple('accts_data_data', ['disp_data_idx', 'data'])
		def gen_accts_data():
			idx, acct_idx = (None, None)
			total, unlocked_total, d_acc = (0, 0, {})
			chk_acc = [] # check for out-of-order accounts (developer idiot-proofing)
			for n, d in enumerate(data):
				m = d.twmmid.obj
				if idx != m.idx or acct_idx != m.acct_idx:
					if idx:
						yield ad(idx, acct_idx, total, unlocked_total, d_acc)
					idx = m.idx
					acct_idx = m.acct_idx
					total = d.amt
					unlocked_total = d.unlocked_amt
					d_acc = {m.addr_idx: bd(n, d)}
					chk_acc.append((idx, acct_idx))
				else:
					total += d.amt
					unlocked_total += d.unlocked_amt
					d_acc[m.addr_idx] = bd(n, d)
			if idx:
				assert len(set(chk_acc)) == len(chk_acc), chk_fail_msg
				yield ad(idx, acct_idx, total, unlocked_total, d_acc)
		self.accts_data = tuple(gen_accts_data())
		return data

	class display_type:

		class squeezed(TwUnspentOutputs.display_type.squeezed):
			cols = ('addr_idx', 'addr', 'comment', 'amt')
			colhdr_fmt_method = None
			fmt_method = 'gen_display'

		class detail(TwUnspentOutputs.display_type.detail):
			cols = ('addr_idx', 'addr', 'amt', 'comment')
			colhdr_fmt_method = None
			fmt_method = 'gen_display'
			line_fmt_method = 'squeezed_format_line'

	def get_column_widths(self, data, *, wide):
		return self.column_widths_data(
			widths = { # fixed cols
				'addr_idx': MoneroIdx.max_digits,
				'used': 4 if 'used' in self.display_type.squeezed.cols else 0,
				'amt': self.amt_widths['amt'],
				'spc': len(self.display_type.squeezed.cols)},
			maxws = { # expandable cols
				'addr': max(len(d.addr) for d in data),
				'comment': max(d.comment.screen_width for d in data)},
			minws = {
				'addr': 16,
				'comment': len('Comment')},
			maxws_nice = self.nice_addr_w)

	def gen_display(self, data, cw, fs, color, fmt_method):
		yes, no = (red('Used'), green('New ')) if color else ('Used', 'New ')
		fs_acct = '{:>4} {:6} {:7}  {}'
		# 30 = 4(col1) + 6(col2) + 7(col3) + 8(iwidth) + 1(len('.')) + 4(spc)
		rfill = ' ' * (self.term_width - self.proto.coin_amt.max_prec - 30)
		yield fs_acct.format('', 'Wallet', 'Account', ' Balance').ljust(self.term_width)
		for n, d in enumerate(self.accts_data):
			yield fs_acct.format(
				str(n + 1) + ')',
				d.idx.fmt(6, color=color),
				d.acct_idx.fmt(7, color=color),
				d.total.fmt2(
					8, # iwidth
					color = color,
					color_override = None if d.total == d.unlocked_total else 'orange'
				)) + rfill
			for v in d.data.values():
				yield fmt_method(None, v.data, cw, fs, color, yes, no)

	def squeezed_format_line(self, n, d, cw, fs, color, yes, no):
		return fs.format(
			I = d.twmmid.obj.addr_idx.fmt(cw.addr_idx, color=color),
			a = d.addr.fmt(self.addr_view_pref, cw.addr, color=color),
			u = yes if d.is_used else no,
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

	class action(TwView.action):

		async def a_sync_wallets(self, parent):
			from ....util import msg, msg_r, ymsg
			from ....tw.view import CUR_HOME, ERASE_ALL
			msg('')
			try:
				op = xmrwallet_op('sync', parent.cfg, None, None, compat_call=True)
			except Exception as e:
				if type(e).__name__ == 'SocketError':
					import asyncio
					ymsg(str(e))
					await asyncio.sleep(2)
					msg_r(CUR_HOME + ERASE_ALL)
					return False
				raise
			await op.restart_wallet_daemon()
			await op.main()
			await parent.get_data()
			msg_r(CUR_HOME + ERASE_ALL)
