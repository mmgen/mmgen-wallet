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
mmgen-cli: Communicate with a coin daemon via its JSON-RPC interface
"""

import asyncio, json

from .util2 import cliargs_convert
from .cfg import gc, Config
from .rpc import rpc_init
from .rpc.util import json_encoder

opts_data = {
	'text': {
		'desc':    'Communicate with a coin daemon via its JSON-RPC interface',
		'usage':   '[opts] <command> <command args>',
		'options': """
-h, --help             Print this help message
--, --longhelp         Print help message for long (global) options
-a, --ascii-output     Ensure that output is ASCII encoded
-w, --wallet=NAME      Use tracking wallet with name NAME
""",
	'notes': """

The utility accepts all {pn} global configuration options and sources the user
config file, allowing users to preconfigure hosts, ports, passwords, datadirs,
tracking wallets and so forth, thus saving a great deal of typing at the
command line. This behavior may be overridden with the --skip-cfg-file option.

Arguments are given in JSON format, with lowercase ‘true’, ‘false’ and ‘null’
for booleans and None, and double-quoted strings in dicts and lists.


                                   EXAMPLES

  $ mmgen-cli --wallet=wallet2 listreceivedbyaddress 0 true

  $ mmgen-cli --coin=ltc --rpc-host=orion getblockcount

  $ mmgen-cli --regtest=1 --wallet=bob getbalance

  $ mmgen-cli --coin=eth eth_getBalance 0x00000000219ab540356cBB839Cbe05303d7705Fa latest

  $ mmgen-cli createrawtransaction \\
    '[{{"txid":"832f5aa9af55dc453314e26869c8f96db1f2a9acac9f23ae18d396903971e0c6","vout":0}}]' \\
    '[{{"1111111111111111111114oLvT2":0.001}}]'
"""
	},
	'code': {
		'notes': lambda cfg, s, help_notes: s.format(
			pn = gc.proj_name)
	}
}

cfg = Config(opts_data=opts_data)
cmd, *args = cfg._args

async def main():

	c = await rpc_init(cfg)
	ret = await c.call(cmd, *cliargs_convert(args), wallet=cfg.wallet)
	print(
		(ascii(ret) if cfg.ascii_output else ret) if isinstance(ret, str) else
		json.dumps(ret, cls=json_encoder, indent=4, ensure_ascii=cfg.ascii_output))

asyncio.run(main())
