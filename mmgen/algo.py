# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
algo: algorithms for the MMGen Wallet suite
"""

def get_start(*, data, bot, top, target, bisect_key_func, match_key_func):
	"""
	Bisecting algorithm to find first entry in a sorted list a substring of which, as
	returned by match_key_func(), matches the requested target.

	Return None if no match was found.

	The target substring must sort below the desired start element but above any possible
	previous element.
	"""

	assert bot <= top,      f'get_start(): {bot=} > {top=}'
	assert top < len(data), f'get_start(): {top=} >= {len(data)=}'

	while True:
		if bot == top:
			return bot if match_key_func(data[bot]) == target else None
		n = (top + bot) >> 1
		if bisect_key_func(data[n]) < target:
			bot = n + 1
		else:
			top = n
