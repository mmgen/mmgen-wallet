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
proto.btc.tw.view: Bitcoin base protocol base class for tracking wallet view classes
"""

class BitcoinTwView:

	txid_w = 64
	txid_max_w  = {'txid': 64}
	txid_min_w  = {'txid': 7}
	txid_nice_w = {'txid': 12}
	nice_addr_w = {'addr': 16}

	age_col_params = {
		'confs':     (7,  'Confs'),
		'block':     (8,  'Block'),
		'days':      (6,  'Age(d)'),
		'date':      (8,  'Date'),
		'date_time': (16, 'Date/Time')}
