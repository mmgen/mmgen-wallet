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
swap.proto.thorchain: THORChain swap protocol implementation for the MMGen Wallet suite
"""

__all__ = ['SwapCfg', 'SwapAsset', 'Memo']

name = 'THORChain'
exp_prec = 4

from ....util2 import ExpInt
class ExpInt4(ExpInt):
	def __new__(cls, spec):
		return ExpInt.__new__(cls, spec, prec=exp_prec)

def rpc_client(tx, amt):
	from .thornode import Thornode
	return Thornode(tx, amt)

from .cfg import THORChainSwapCfg as SwapCfg

from .asset import THORChainSwapAsset as SwapAsset

from .memo import THORChainMemo as Memo
