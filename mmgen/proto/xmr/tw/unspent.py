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

from ....tw.unspent import TwUnspentOutputs

from .view import MoneroTwView

class MoneroTwUnspentOutputs(MoneroTwView, TwUnspentOutputs):

	hdr_lbl = 'spendable accounts'
	desc = 'spendable accounts'
	include_empty = False

	prompt_fs_in = [
		'Sort options: [a]mount, [A]ge, a[d]dr, [M]mgen addr, [r]everse',
		'Display options: r[e]draw screen',
		'View/Print: pager [v]iew, [w]ide pager view, [p]rint to file{s}',
		'Actions: [q]uit menu, add [l]abel, [R]efresh balances:']
	extra_key_mappings = {
		'R': 'a_sync_wallets',
		'A': 's_age'}
