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
examples/whitepaper.py: extract the Bitcoin whitepaper from the blockchain
"""

import asyncio
from mmgen.cfg import Config
from mmgen.rpc import rpc_init

txid = '54e48e5f5c656b26c3bca14a8c95aa583d07ebe84dde3b7dd4a78f4e4186e713'
fn = 'bitcoin.pdf'

async def main():

	cfg = Config(process_opts=True)

	assert cfg.coin == 'BTC' and cfg.network == 'mainnet', 'This script works only on BTC mainnet!'

	c = await rpc_init(cfg, ignore_wallet=True)

	tx = await c.call('getrawtransaction', txid, True)

	chunks = [''.join(d['scriptPubKey']['asm'].split()[1:4]) for d in tx['vout']]

	with open(fn, 'wb') as f:
		f.write(bytes.fromhex(''.join(chunks)[16:368600]))

	print(f'Wrote {fn}')

asyncio.run(main())
