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
proto.btc.tw.prune: Bitcoin base protocol tracking wallet address list prune class
"""

from ....tw.prune import TwAddressesPrune
from .addresses import BitcoinTwAddresses

class BitcoinTwAddressesPrune(BitcoinTwAddresses,TwAddressesPrune):

	prompt = """
Sort options: [a]mt, [A]ge, [M]mid, [r]everse
Column options: toggle [D]ays/date/confs/block
Filters: show [E]mpty addrs, [U]sed addrs, all [L]abels
View/Print: pager [v]iew, [w]ide view
Actions: [q]uit pruning, r[e]draw,
Pruning: [p]rune, [u]nprune, [c]lear prune list:
"""
	key_mappings = {
		'a':'s_amt',
		'A':'s_age',
		'M':'s_twmmid',
		'r':'d_reverse',
		'D':'d_days',
		'e':'d_redraw',
		'E':'d_showempty',
		'U':'d_showused',
		'L':'d_all_labels',
		'q':'a_quit',
		'v':'a_view',
		'w':'a_view_detail',
		'p':'a_prune',
		'u':'a_unprune',
		'c':'a_clear_prune_list' }
