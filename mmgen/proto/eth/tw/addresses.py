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
proto.eth.tw.addresses: Ethereum base protocol tracking wallet address list class
"""

from ....tw.addresses import TwAddresses

from .view import EthereumTwView
from .rpc import EthereumTwRPC

class EthereumTwAddresses(TwAddresses, EthereumTwView, EthereumTwRPC):

	prompt_fs_in = [
		'Sort options: [a]mt, [M]mgen addr, [r]everse',
		'Filters: show [E]mpty addrs, show all [L]abels',
		'View/Print: pager [v]iew, [w]ide pager view, [p]rint{s}',
		'Actions: [q]uit menu, r[e]draw, [D]elete addr, add [l]abel:']

	async def get_rpc_data(self):

		self.total = self.proto.coin_amt('0')
		self.minconf = None
		addrs = {}

		used_addrs = self.twctl.used_addrs

		for e in await self.twctl.get_label_addr_pairs():
			bal = await self.twctl.get_balance(e.coinaddr)
			addrs[e.label.mmid] = {
				'addr':  e.coinaddr,
				'amt':   bal,
				'recvd': bal,         # current bal only, CF btc.tw.addresses.get_rpc_data()
				'is_used': bool(bal) or e.coinaddr in used_addrs,
				'confs': 0,
				'lbl':   e.label}
			self.total += bal

		return addrs

class EthereumTokenTwAddresses(EthereumTwAddresses):
	pass
