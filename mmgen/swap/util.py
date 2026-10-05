# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
swap.util: swap utilities for the MMGen Wallet suite
"""

def get_swap_proto_mod(swap_proto_name):
	import importlib
	return importlib.import_module(f'mmgen.swap.proto.{swap_proto_name}')

def init_swap_proto(cfg, asset):
	from ..protocol import init_proto
	return init_proto(
		cfg,
		asset.coin,
		network = cfg._proto.network,
		tokensym = asset.tokensym,
		need_amt = True)
