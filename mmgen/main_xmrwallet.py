#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
mmgen-xmrwallet: Perform various Monero wallet and transacting operations for
                 addresses in an MMGen XMR key-address file
"""

from collections import namedtuple

import mmgen.opts as opts
from .cfg import gc,Config
from .util import ymsg,die,async_run
from .xmrwallet import (
	MoneroWalletOps,
	xmrwallet_uarg_info,
	xmrwallet_uargs,
)

opts_data = {
	'text': {
		'desc': """Perform various Monero wallet and transacting operations for
                   addresses in an MMGen XMR key-address file""",
		'usage2': [
			'[opts] create | sync | list <xmr_keyaddrfile> [wallets]',
			'[opts] label    <xmr_keyaddrfile> LABEL_SPEC',
			'[opts] new      <xmr_keyaddrfile> NEW_ADDRESS_SPEC',
			'[opts] transfer <xmr_keyaddrfile> TRANSFER_SPEC',
			'[opts] sweep    <xmr_keyaddrfile> SWEEP_SPEC',
			'[opts] relay    <TX_file>',
			'[opts] txview   <TX_file> ...',
		],
		'options': """
-h, --help                       Print this help message
--, --longhelp                   Print help message for long options (common
                                 options)
-b, --rescan-blockchain          Rescan the blockchain if wallet fails to sync
-d, --outdir=D                   Save transaction files to directory 'D'
                                 instead of the working directory
-D, --daemon=H:P                 Connect to the monerod at {D}
-R, --tx-relay-daemon=H:P[:H:P]  Relay transactions via a monerod specified by
                                 {R}
-k, --use-internal-keccak-module Force use of the internal keccak module
-p, --hash-preset=P              Use scrypt hash preset 'P' for password
                                 hashing (default: '{gc.dfl_hash_preset}')
-r, --restore-height=H           Scan from height 'H' when creating wallets.
                                 Use special value ‘current’ to create empty
                                 wallet at current blockchain height.
-R, --no-relay                   Save transaction to file instead of relaying
-s, --no-start-wallet-daemon     Don’t start the wallet daemon at startup
-S, --no-stop-wallet-daemon      Don’t stop the wallet daemon at exit
-w, --wallet-dir=D               Output or operate on wallets in directory 'D'
                                 instead of the working directory
-H, --wallet-rpc-host=host       Wallet RPC hostname (currently: {cfg.monero_wallet_rpc_host!r})
-U, --wallet-rpc-user=user       Wallet RPC username (currently: {cfg.monero_wallet_rpc_user!r})
-P, --wallet-rpc-password=pass   Wallet RPC password (currently: [scrubbed])
""",
	'notes': """

{xmrwallet_help}
"""
	},
	'code': {
		'options': lambda cfg,s: s.format(
			D=xmrwallet_uarg_info['daemon'].annot,
			R=xmrwallet_uarg_info['tx_relay_daemon'].annot,
			cfg=cfg,
			gc=gc,
		),
		'notes': lambda help_mod,s: s.format(
			xmrwallet_help = help_mod('xmrwallet')
		)
	}
}

cfg = Config(opts_data=opts_data)

cmd_args = cfg._args

if len(cmd_args) < 2:
	cfg._opts.usage()

op     = cmd_args.pop(0)
infile = cmd_args.pop(0)
wallets = spec = None

if op not in MoneroWalletOps.ops:
	die(1,f'{op!r}: unrecognized operation')

if op == 'relay':
	if len(cmd_args) != 0:
		cfg._opts.usage()
elif op == 'txview':
	infile = [infile] + cmd_args
elif op in ('create','sync','list'):
	if len(cmd_args) not in (0,1):
		cfg._opts.usage()
	if cmd_args:
		wallets = cmd_args[0]
elif op in ('new','transfer','sweep','label'):
	if len(cmd_args) != 1:
		cfg._opts.usage()
	spec = cmd_args[0]

m = getattr(MoneroWalletOps,op)(
	cfg,
	xmrwallet_uargs(infile, wallets, spec))

try:
	if async_run(m.main()):
		m.post_main()
except KeyboardInterrupt:
	ymsg('\nUser interrupt')

try:
	async_run(m.stop_wallet_daemon())
except Exception as e:
	ymsg(f'Unable to stop wallet daemon: {type(e).__name__}: {e}')
