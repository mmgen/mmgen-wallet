#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2021 The MMGen Project <mmgen@tuta.io>
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
mmgen/main_xmrwallet: Perform various Monero wallet operations for addresses
                      in an MMGen XMR key-address file
"""

from .common import *
from .xmrwallet import xmrwallet_uarg_info,MoneroWalletOps

opts_data = {
	'text': {
		'desc': """Perform various Monero wallet operations for addresses
                   in an MMGen XMR key-address file""",
		'usage2': [
			'[opts] create   <xmr_keyaddrfile> [wallets]',
			'[opts] sync     <xmr_keyaddrfile> [wallets]',
			'[opts] transfer <xmr_keyaddrfile> <transfer_spec>',
			'[opts] sweep    <xmr_keyaddrfile> <sweep_spec>',
		],
		'options': """
-h, --help                       Print this help message
--, --longhelp                   Print help message for long options (common
                                 options)
-d, --outdir=D                   Output or operate on wallets in directory 'D'
                                 instead of working dir
-D, --daemon=H:P                 Connect to monerod at {D}
-R, --tx-relay-daemon=H:P[:H:P]  Relay transactions via monerod specified by
                                 {R}
-k, --use-internal-keccak-module Force use of the internal keccak module
-p, --hash-preset=P              Use scrypt hash preset 'P' for password
                                 hashing (default: '{g.dfl_hash_preset}')
-r, --restore-height=H           Scan from height 'H' when creating wallets
-s, --no-start-wallet-daemon     Don’t start the wallet daemon at startup
-S, --no-stop-wallet-daemon      Don’t stop the wallet daemon at exit
""",
	'notes': """

Command requires a running monerod daemon.  Unless --daemon is specified,
monerod is assumed to be listening on localhost at the default RPC port.

If --tx-relay-daemon is specified, the monerod daemon at HOST:PORT will be
used to relay any created transactions.  PROXY_HOST:PROXY_PORT, if specified,
may point to a SOCKS proxy, in which case HOST may be a Tor onion address.


                        SUPPORTED OPERATIONS

create    - create wallet for all or specified addresses in key-address file
sync      - sync wallet for all or specified addresses in key-address file
transfer  - transfer specified XMR amount to specified address from specified
            wallet:account
sweep     - sweep funds in specified wallet:account to new address in same
            account or new account in another wallet


                   CREATE AND SYNC OPERATION NOTES

These operations take an optional `wallets` argument: a comma-separated list,
hyphenated range, or combination of both, of address indexes in the specified
key-address file, each corresponding to a Monero wallet to be created or
synced.  If omitted, all wallets are operated upon.


                       TRANSFER OPERATION NOTES

The transfer operation takes a `transfer specifier` arg with the following
format:

    SOURCE:ACCOUNT:ADDRESS,AMOUNT

where SOURCE is a wallet index; ACCOUNT the source account index; and ADDRESS
and AMOUNT the destination Monero address and XMR amount, respectively.


                        SWEEP OPERATION NOTES

The sweep operation takes a `sweep specifier` arg with the following format:

    SOURCE:ACCOUNT[,DEST]

where SOURCE and DEST are wallet indexes and ACCOUNT an account index.

If DEST is omitted, a new address will be created in ACCOUNT of SOURCE and
all funds from ACCOUNT of SOURCE will be swept into it.

If DEST is included, a new account will be created in DEST and all funds
from ACCOUNT of SOURCE will be swept into the new account.

The user is prompted before addresses are created or funds are transferred.


                              WARNING

Note that the use of this command requires private data to be exposed on a
network-connected machine in order to unlock the Monero wallets.  This is a
violation of good security practice.
"""
	},
	'code': {
		'options': lambda s: s.format(
			D=xmrwallet_uarg_info['daemon'].annot,
			R=xmrwallet_uarg_info['tx_relay_daemon'].annot,
			g=g,
		),
	}
}

cmd_args = opts.init(opts_data)

if len(cmd_args) < 2:
	opts.usage()

op     = cmd_args.pop(0)
infile = cmd_args.pop(0)

if op not in MoneroWalletOps.ops:
	die(1,f'{op!r}: unrecognized operation')

wallets = spec = ''

if op in ('create','sync'):
	if len(cmd_args) not in (0,1):
		opts.usage()
	if cmd_args:
		wallets = cmd_args[0]
elif op in ('transfer','sweep'):
	if len(cmd_args) != 1:
		opts.usage()
	spec = cmd_args[0]

ua = namedtuple('uargs',[ 'op', 'infile', 'wallets', 'spec' ])
uo = namedtuple('uopts',[
	'daemon',
	'tx_relay_daemon',
	'restore_height',
	'no_start_wallet_daemon',
	'no_stop_wallet_daemon',
])

uargs = ua( op, infile, wallets, spec )
uopts = uo(
	opt.daemon or '',
	opt.tx_relay_daemon or '',
	opt.restore_height or 0,
	opt.no_start_wallet_daemon,
	opt.no_stop_wallet_daemon,
)

m = getattr(MoneroWalletOps,op)(uargs,uopts)

try:
	if run_session(m.main()):
		m.post_main()
except KeyboardInterrupt:
	ymsg('\nUser interrupt')
finally:
	m.stop_daemons()
