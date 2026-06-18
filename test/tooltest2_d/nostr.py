#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
test.tooltest2_d.nostr: NOSTR test vectors for the ‘mmgen-tool’ utility
"""

from test.modtest_d.nostr import vecs

vec1, vec2 = vecs

tests = {
	'Coin': {
		'addr2pubhex': {
			'nostr_mainnet': [
				([vec1.npub], vec1.pubhex),
				([vec2.npub], vec2.pubhex),
			],
		},
		'privhex2pair': {
			'nostr_mainnet': [
				([vec1.privhex], [vec1.nsec, vec1.npub], None, 'bech32pk'),
				([vec2.privhex], [vec2.nsec, vec2.npub], None, 'bech32pk'),
			],
		},
		'pubhex2addr': {
			'nostr_mainnet': [
				([vec1.pubhex], vec1.npub, None, 'bech32pk'),
				([vec2.pubhex], vec2.npub, None, 'bech32pk'),
			],
		},
	},
}
