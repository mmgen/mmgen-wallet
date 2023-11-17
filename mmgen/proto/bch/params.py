#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
proto.bch.params: Bitcoin Cash protocol
"""

from ..btc.params import mainnet,_finfo

class mainnet(mainnet):
	is_fork_of      = 'Bitcoin'
	mmtypes         = ('L','C')
	sighash_type    = 'ALL|FORKID'
	forks = [
		_finfo(478559,'000000000000000000651ef99cb9fcbe0dadde1d424bd9f15ff20136191a5eec','BTC',False)
	]
	caps = ()
	coin_amt        = 'BCHAmt'
	max_tx_fee      = '0.1'
	ignore_daemon_version = False

	def pubhash2redeem_script(self,pubhash):
		raise NotImplementedError

	def pubhash2segwitaddr(self,pubhash):
		raise NotImplementedError

class testnet(mainnet):
	addr_ver_info  = { '6f': 'p2pkh', 'c4': 'p2sh' }
	wif_ver_num    = { 'std': 'ef' }

class regtest(testnet):
	halving_interval = 150
