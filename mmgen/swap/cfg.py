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
swap.cfg: swap configuration class for the MMGen Wallet suite
"""

import re
from collections import namedtuple

from ..amt import UniAmt
from ..util import die

_mmd = namedtuple('swap_config_option', ['min', 'max', 'dfl'])

class SwapCfg:

	# The trade limit, i.e., set 100000000 to get a minimum of 1 full asset, else a refund
	# Optional. 1e8 or scientific notation
	trade_limit = None

	# Swap interval for streaming swap in blocks. Optional. If 0, do not stream
	si = _mmd(1, 20, 3) # stream_interval

	# Swap quantity for streaming swap.
	# The interval value determines the frequency of swaps in blocks
	# Optional. If 0, network will determine the number of swaps
	stream_quantity = 0

	def __init__(self, cfg):

		self.cfg = cfg

		if cfg.trade_limit is not None:
			self.set_trade_limit(desc='parameter for --trade-limit')

		if cfg.stream_interval is None:
			self.stream_interval = self.si.dfl
		else:
			self.set_stream_interval(desc='parameter for --stream-interval')

	def set_trade_limit(self, *, desc):
		s = self.cfg.trade_limit
		if re.match(r'-*[0-9]+(\.[0-9]+)*%*$', s):
			self.trade_limit = 1 - float(s[:-1]) / 100 if s.endswith('%') else UniAmt(s)
		else:
			die('SwapCfgValueError', f'{s}: invalid {desc}')

	def set_stream_interval(self, *, desc):
		s = self.cfg.stream_interval
		from ..util import is_int
		if not is_int(s):
			die('SwapCfgValueError', f'{s}: invalid {desc} (not an integer)')
		self.stream_interval = si = int(s)
		if si < self.si.min:
			die('SwapCfgValueError', f'{si}: invalid {desc} (< {self.si.min})')
		if si > self.si.max:
			die('SwapCfgValueError', f'{si}: invalid {desc} (> {self.si.max})')
