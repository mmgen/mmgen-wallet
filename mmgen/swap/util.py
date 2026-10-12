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

def get_swap_proto_rpc(cfg, coin):
	from ..protocol import init_proto
	from ..rpc import get_remote_rpc
	return get_remote_rpc(cfg, init_proto(cfg, coin))

def init_swap_proto(cfg, asset):
	from ..protocol import init_proto
	return init_proto(
		cfg,
		asset.coin,
		tokensym = asset.tokensym,
		need_amt = True)

def get_swap_asset(cfg, asset, *, direction='send', sanitize_input=False):
	"given an asset symbol, and optionally direction, return a swap asset instance"
	assert isinstance(asset, str), '‘asset’ must be a string'
	return get_swap_proto_mod(cfg.swap_proto).SwapAsset(asset, direction, sanitize_input=sanitize_input)

def get_coin_amt(cfg, asset, amt):
	"given an asset symbol and amount (as string), return a coin amount instance"
	from ..amt import TokenAmt
	assert isinstance(asset, str), '‘asset’ must be a string'
	assert isinstance(amt, str), '‘amt’ must be a string'
	swap_asset = get_swap_asset(cfg, asset, sanitize_input=True)
	return (
		TokenAmt(amt, decimals=swap_asset.decimals) if swap_asset.tokensym else
		init_swap_proto(cfg, swap_asset).coin_amt(amt))
