#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2023 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
help.xmrwallet: xmrwallet help notes for MMGen suite
"""

def help(proto,cfg):

	return f"""
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
list      - same as ‘sync’, but also list detailed address info for accounts
label     - set a label for an address
new       - create a new account in a wallet, or a new address in an account
transfer  - transfer specified XMR amount from specified wallet:account to
            specified address
sweep     - sweep funds in specified wallet:account to new address in same
            account or new account in another wallet
relay     - relay a transaction from a transaction file created using ‘sweep’
            or ‘transfer’ with the --no-relay option
txview    - view a transaction file or files created using ‘sweep’ or
            ‘transfer’ with the --no-relay option


                 ‘CREATE’, ‘SYNC’ AND ‘LIST’ OPERATION NOTES

These operations take an optional `wallets` argument: one or more address
indexes (expressed as a comma-separated list, hyphenated range, or both)
in the specified key-address file, each corresponding to a Monero wallet
to be created, synced or listed.  If omitted, all wallets are operated upon.


                           ‘LABEL’ OPERATION NOTES

This operation takes a LABEL_SPEC arg with the following format:

    WALLET:ACCOUNT:ADDRESS,"label text"

where WALLET is a wallet number, ACCOUNT an account index, and ADDRESS an
address index.


                            ‘NEW’ OPERATION NOTES

This operation takes a NEW_ADDRESS_SPEC arg with the following format:

    WALLET[:ACCOUNT][,"label text"]

where WALLET is a wallet number and ACCOUNT an account index.  If ACCOUNT is
omitted, a new account will be created in the wallet, otherwise a new address
will be created in the specified account.  An optional label text may be
appended to the spec following a comma.


                         ‘TRANSFER’ OPERATION NOTES

The transfer operation takes a TRANSFER_SPEC arg with the following format:

    SOURCE:ACCOUNT:ADDRESS,AMOUNT

where SOURCE is a wallet number; ACCOUNT the source account index; and ADDRESS
and AMOUNT the destination Monero address and XMR amount, respectively.


                           ‘SWEEP’ OPERATION NOTES

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


                    ‘SUBMIT’ AND ‘RELAY’ OPERATION NOTES

By default, transactions are relayed to a monerod running on localhost at the
default RPC port.  To relay transactions to a remote or non-default monerod
via optional SOCKS proxy, use the --tx-relay-daemon option described above.

When ‘submit’ is used together with --autosign, the transaction filename may
be omitted and the software will attempt to locate it automatically.


                    ‘DUMP’ AND ‘RESTORE’ OPERATION NOTES

These commands produce and read JSON wallet dump files located in the same
directories as their corresponding wallets and having the same filenames,
plus a .dump extension.


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
""".strip()
