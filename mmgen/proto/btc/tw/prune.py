#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2024 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.btc.tw.prune: Bitcoin base protocol tracking wallet address list prune class
"""

from ....tw.prune import TwAddressesPrune
from .addresses import BitcoinTwAddresses

class BitcoinTwAddressesPrune(BitcoinTwAddresses, TwAddressesPrune):

	prompt_fs_in = [
		'Sort options: [a]mt, [A]ge, [M]mgen addr, [r]everse',
		'Column options: toggle [D]ays/date/confs/block',
		'Filters: show [E]mpty addrs, [U]sed addrs, all [L]abels',
		'View/Actions: pager [v]iew, [w]ide view, r[e]draw{s}',
		'Pruning: [q]uit pruning, [p]rune, [u]nprune, [c]lear prune list:']
	prompt_fs_repl = {
		'BCH': (1, 'Column options: toggle [D]ays/date/confs/block, cas[h]addr')
	}
	key_mappings = {
		'a':'s_amt',
		'A':'s_age',
		'M':'s_twmmid',
		'r':'s_reverse',
		'D':'d_days',
		'e':'d_redraw',
		'E':'d_showempty',
		'U':'d_showused',
		'L':'d_all_labels',
		'v':'a_view',
		'w':'a_view_detail',
		'p':'a_prune',
		'u':'a_unprune',
		'c':'a_clear_prune_list'}
