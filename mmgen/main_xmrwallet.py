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
mmgen-xmrwallet: Perform various Monero wallet operations for addresses
                 in an MMGen XMR key-address file
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
		'desc': """Perform various Monero wallet operations for addresses
                   in an MMGen XMR key-address file""",
		'usage2': [
			'[opts] create   <xmr_keyaddrfile> [wallets]',
			'[opts] sync     <xmr_keyaddrfile> [wallets]',
			'[opts] list     <xmr_keyaddrfile> [wallets]',
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
-r, --restore-height=H           Scan from height 'H' when creating wallets
-R, --no-relay                   Save transaction to file instead of relaying
-s, --no-start-wallet-daemon     Don’t start the wallet daemon at startup
-S, --no-stop-wallet-daemon      Don’t stop the wallet daemon at exit
-w, --wallet-dir=D               Output or operate on wallets in directory 'D'
                                 instead of the working directory
-H, --wallet-rpc-host=host       Wallet RPC hostname (default: {cfg.monero_wallet_rpc_host!r})
-U, --wallet-rpc-user=user       Wallet RPC username (default: {cfg.monero_wallet_rpc_user!r})
-P, --wallet-rpc-password=pass   Wallet RPC password (default: {cfg.monero_wallet_rpc_password!r})
""",
	'notes': """

All operations except for ‘relay’ require a running Monero daemon.  Unless
--daemon is specified, the monerod is assumed to be listening on localhost at
the default RPC port.

If --tx-relay-daemon is specified, the monerod at HOST:PORT will be used to
relay any created transactions.  PROXY_HOST:PROXY_PORT, if specified, may
point to a SOCKS proxy, in which case HOST may be a Tor onion address.

All communications use the RPC protocol via SSL (HTTPS) or Tor.  RPC over
plain HTTP is not supported.


                            SUPPORTED OPERATIONS

create    - create wallet for all or specified addresses in key-address file
sync      - sync wallet for all or specified addresses in key-address file
list      - same as 'sync', but also list detailed address info for accounts
label     - set a label for an address
new       - create a new account in a wallet, or a new address in an account
transfer  - transfer specified XMR amount from specified wallet:account to
            specified address
sweep     - sweep funds in specified wallet:account to new address in same
            account or new account in another wallet
relay     - relay a transaction from a transaction file created using 'sweep'
            or 'transfer' with the --no-relay option
txview    - view a transaction file or files created using 'sweep' or
            'transfer' with the --no-relay option


                 'CREATE', 'SYNC' AND 'LIST' OPERATION NOTES

These operations take an optional `wallets` argument: one or more address
indexes (expressed as a comma-separated list, hyphenated range, or both)
in the specified key-address file, each corresponding to a Monero wallet
to be created, synced or listed.  If omitted, all wallets are operated upon.


                          'LABEL' OPERATION NOTES

This operation takes a LABEL_SPEC arg with the following format:

    WALLET:ACCOUNT:ADDRESS,"label text"

where WALLET is a wallet number, ACCOUNT an account index, and ADDRESS an
address index.


                           'NEW' OPERATION NOTES

This operation takes a NEW_ADDRESS_SPEC arg with the following format:

    WALLET[:ACCOUNT][,"label text"]

where WALLET is a wallet number and ACCOUNT an account index.  If ACCOUNT is
omitted, a new account will be created in the wallet, otherwise a new address
will be created in the specified account.  An optional label text may be
appended to the spec following a comma.


                         'TRANSFER' OPERATION NOTES

The transfer operation takes a TRANSFER_SPEC arg with the following format:

    SOURCE:ACCOUNT:ADDRESS,AMOUNT

where SOURCE is a wallet number; ACCOUNT the source account index; and ADDRESS
and AMOUNT the destination Monero address and XMR amount, respectively.


                           'SWEEP' OPERATION NOTES

The sweep operation takes a SWEEP_SPEC arg with the following format:

    SOURCE:ACCOUNT[,DEST]

where SOURCE and DEST are wallet numbers and ACCOUNT an account index.

If DEST is omitted, a new address will be created in ACCOUNT of SOURCE and
all funds from ACCOUNT of SOURCE will be swept into it.

If DEST is included, all funds from ACCOUNT of SOURCE will be swept into a
newly created account in DEST, or the last existing account, if requested
by the user.

The user is prompted before addresses are created or funds are transferred.

Note that multiple sweep operations may be required to sweep all the funds
in an account.


                           'RELAY' OPERATION NOTES

By default, transactions are relayed to a monerod running on localhost at the
default RPC port.  To relay transactions to a remote or non-default monerod
via optional SOCKS proxy, use the --tx-relay-daemon option described above.


                                  WARNING

To avoid exposing your private keys on a network-connected machine, you’re
strongly advised to create all transactions offline using the --no-relay
option.  For this, a monerod with a fully synced blockchain must be running
on the offline machine.  The resulting transaction files are then sent using
the 'relay' operation.


                                  EXAMPLES

Generate an XMR key-address file with 5 addresses from your default wallet:
$ mmgen-keygen --coin=xmr 1-5

Create 3 Monero wallets from the key-address file:
$ mmgen-xmrwallet create *.akeys.mmenc 1-3

After updating the blockchain, sync wallets 1 and 2:
$ mmgen-xmrwallet sync *.akeys.mmenc 1,2

Sweep all funds from account #0 of wallet 1 to a new address:
$ mmgen-xmrwallet sweep *.akeys.mmenc 1:0

Same as above, but use a TX relay on the Tor network:
$ mmgen-xmrwallet --tx-relay-daemon=abcdefghijklmnop.onion:127.0.0.1:9050 sweep *.akeys.mmenc 1:0

Sweep all funds from account #0 of wallet 1 to wallet 2:
$ mmgen-xmrwallet sweep *.akeys.mmenc 1:0,2

Send 0.1 XMR from account #0 of wallet 2 to an external address:
$ mmgen-xmrwallet transfer *.akeys.mmenc 2:0:<monero address>,0.1

Sweep all funds from account #0 of wallet 2 to a new address, saving the
transaction to a file:
$ mmgen-xmrwallet --no-relay sweep *.akeys.mmenc 2:0

Relay the created sweep transaction via a host on the Tor network:
$ mmgen-xmrwallet --tx-relay-daemon=abcdefghijklmnop.onion:127.0.0.1:9050 relay *XMR*.sigtx

Create a new account in wallet 2:
$ mmgen-xmrwallet new *.akeys.mmenc 2

Create a new address in account 1 of wallet 2, with label:
$ mmgen-xmrwallet new *.akeys.mmenc 2:1,"from ABC exchange"

View all the XMR transaction files in the current directory, sending output
to pager:
$ mmgen-xmrwallet --pager txview *XMR*.sigtx
"""
	},
	'code': {
		'options': lambda cfg,s: s.format(
			D=xmrwallet_uarg_info['daemon'].annot,
			R=xmrwallet_uarg_info['tx_relay_daemon'].annot,
			cfg=cfg,
			gc=gc,
		),
	}
}

cfg = Config(opts_data=opts_data)

cmd_args = cfg._args

if len(cmd_args) < 2:
	cfg._opts.usage()

op     = cmd_args.pop(0)
infile = cmd_args.pop(0)

if op not in MoneroWalletOps.ops:
	die(1,f'{op!r}: unrecognized operation')

wallets = spec = ''

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
finally:
	async_run(m.stop_wallet_daemon())
