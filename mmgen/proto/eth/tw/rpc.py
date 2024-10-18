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
proto.eth.tw.rpc: Ethereum base protocol tracking wallet RPC class
"""

from ....tw.rpc import TwRPC

class EthereumTwRPC(TwRPC):
	pass

class EthereumTokenTwRPC(EthereumTwRPC):
	pass
