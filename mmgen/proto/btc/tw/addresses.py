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
proto.btc.tw.addresses: Bitcoin base protocol tracking wallet address list class
"""

from ....tw.addresses import TwAddresses
from ....tw.shared import TwLabel
from ....obj import get_obj

from .rpc import BitcoinTwRPC
from .view import BitcoinTwView

class BitcoinTwAddresses(BitcoinTwView, TwAddresses, BitcoinTwRPC):

	has_age = True
	has_used = True

	prompt_fs_in = [
		'Sort options: [a]mt, [A]ge, [M]mgen addr, [r]everse',
		'Column options: toggle [D]ays/date/confs/block',
		'Filters: show [E]mpty addrs, [u]sed addrs, all [L]abels',
		'View/Print: pager [v]iew, [w]ide pager view, [p]rint{s}',
		'Actions: [q]uit menu, r[e]draw, add [l]abel:']
	prompt_fs_repl = {
		'BCH': (1, 'Column options: toggle [D]ays/date/confs/block, cas[h]addr')}
	extra_key_mappings = {
		'A':'s_age',
		'D':'d_days',
		'u':'d_showused'}

	async def get_rpc_data(self):

		qmsg = self.cfg._util.qmsg
		qmsg_r = self.cfg._util.qmsg_r
		qmsg_r('Getting unspent outputs...')
		addrs = await self.get_unspent_by_mmid(minconf=self.minconf)
		qmsg('done')

		coin_amt = self.proto.coin_amt
		amt0 = coin_amt('0')
		self.total = sum((v['amt'] for v in addrs.values()), start=amt0)

		qmsg_r('Getting labels and associated addresses...')
		for e in await self.get_label_addr_pairs():
			if e.label and e.label.mmid not in addrs:
				addrs[e.label.mmid] = {
					'addr':   e.coinaddr,
					'amt':    amt0,
					'recvd':  amt0,
					'is_used': False,
					'confs':  0,
					'lbl':    e.label}
		qmsg('done')

		qmsg_r('Getting received funds data...')
		for d in await self.rpc.icall('listreceivedbylabel', include_empty=True):
			label = get_obj(TwLabel, proto=self.proto, text=d['label'])
			if label:
				assert label.mmid in addrs, f'{label.mmid!r} not found in addrlist!'
				amt = coin_amt(d['amount'])
				addrs[label.mmid]['recvd'] = amt
				addrs[label.mmid]['is_used'] = bool(amt)
				addrs[label.mmid]['confs'] = d['confirmations']
		qmsg('done')

		return addrs
