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
examples/coin-daemon-info.py:
    Get info about multiple running coin daemons.
    Demonstrates use of the MMGen Config API.
"""

# Instructions
#
#  Testing mode:
#
#   1) From the MMGen repository root, start the mainnet test suite daemons as follows
#      (note that Geth is the default testing daemon for ETH):
#
#       test/start-coin-daemons.py btc ltc eth
#
#   2) Then run the script as follows:
#
#       PYTHONPATH=. MMGEN_TEST_SUITE=1 examples/coin-daemon-info.py btc ltc eth
#
#  Live mode:
#
#   1) Start up one or more of bitcoind, litecoind or geth with the standard mainnet ports
#      and datadirs.  For geth, the options ‘--http --http.api=eth,web3’ are required.
#
#   2) Then run the script as follows:
#
#       PYTHONPATH=. examples/coin-daemon-info.py btc ltc eth

import sys, os, asyncio

from mmgen.exception import SocketError
from mmgen.cfg import Config
from mmgen.rpc import rpc_init
from mmgen.util import make_timestr

async def get_rpc(cfg):
	try:
		return await rpc_init(cfg, ignore_wallet=True)
	except SocketError:
		return False

async def main(coins):

	rpcs = {}
	cfgs = {}
	test_suite = os.getenv('MMGEN_TEST_SUITE')
	base_cfg = Config({'pager':True})

	for coin in coins:
		cfg_in = {
			'coin': coin,
			'test_suite': test_suite,
		}
		if coin == 'eth' and not test_suite:
			cfg_in.update({'daemon_id': 'geth'})
		cfgs[coin] = Config(cfg_in)
		rpcs[coin] = await get_rpc(cfgs[coin])

	def gen_output():
		fs = '{:4} {:7} {:6} {:<5} {:<8} {:30} {:13} {:23} {}'
		yield fs.format(
			'Coin',
			'Network',
			'Status',
			'Port',
			'Chain',
			'Latest Block',
			'Daemon',
			'Version',
			'Datadir')
		for coin, rpc in rpcs.items():
			info = ('Down', '-', '-', '-', '-', '-', '-') if rpc is False else (
				'Up',
				rpc.port,
				rpc.chain,
				f'{rpc.blockcount:<8} [{make_timestr(rpc.cur_date)}]',
				rpc.daemon.coind_name,
				rpc.daemon_version_str,
				rpc.daemon.datadir
			)
			yield fs.format(coin.upper(), cfgs[coin].network, *info)

	base_cfg._util.stdout_or_pager('\n'.join(gen_output()))

all_coins = ('btc', 'ltc', 'eth')

coins = sys.argv[1:]

if coins and all(coin in all_coins for coin in coins):
	asyncio.run(main(coins))
else:
	print(f'You must supply one or more of the following coins on the command line:\n  {all_coins}')
	sys.exit(1)
