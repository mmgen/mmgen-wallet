# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
tool.amt: coin amount-related commands for the 'mmgen-tool' utility
"""

from decimal import Decimal

from .common import tool_cmd_base

class tool_cmd(tool_cmd_base):
	"coin amount utilities"

	need_proto = True

	def memoless_amt(self, asset: str, amt: Decimal, refnum: int):
		"create a memoless swap amount from a given asset, amount and reference number"

		assert self.cfg.coin == 'BTC', '--coin arg not supported for this command'

		from ..swap.util import get_swap_proto_mod, get_coin_amt

		return str(get_swap_proto_mod(self.cfg.swap_proto).memoless_amt(
			get_coin_amt(self.cfg, asset, amt), refnum).amt)
