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
help.xmrwallet: xmrwallet help notes for MMGen suite
"""

def help(proto,cfg):

	return """
Many operations take an optional ‘wallets’ argument: one or more address
indexes (expressed as a comma-separated list and/or hyphenated range) in
the default or specified key-address file, each corresponding to a Monero
wallet with the same index.  If the argument is omitted, all wallets are
operated upon.

All operations except for ‘relay’ require a running Monero daemon (monerod).
Unless --daemon is specified, the daemon is assumed to be listening on
localhost at the default RPC port.

If --tx-relay-daemon is specified, the monerod at HOST:PORT will be used to
relay any created transactions.  PROXY_HOST:PROXY_PORT, if specified, may
point to a SOCKS proxy, in which case HOST may be a Tor onion address.

All communications use the RPC protocol via SSL (HTTPS) or Tor.  RPC over
plain HTTP is not supported.


                            SUPPORTED OPERATIONS

create    - create wallets for all or specified addresses in key-address file
sync      - sync wallets for all or specified addresses in key-address file
list      - same as ‘sync’, but also list detailed address info for accounts
label     - set a label for an address
new       - create a new account in a wallet, or a new address in an account
transfer  - transfer specified XMR amount from specified wallet:account to
            specified address
sweep     - sweep funds in specified wallet:account to new address in same
            account or new account in another wallet
relay     - relay a transaction from a transaction file created using ‘sweep’
            or ‘transfer’ with the --no-relay option
submit    - submit an autosigned transaction to a wallet and the network
resubmit  - resubmit most recently submitted autosigned transaction (other
            actions are required: see Exporting Outputs below)
txview    - display detailed information about a transaction file or files
txlist    - same as above, but display terse information in tabular format
dump      - produce JSON dumps of wallet metadata (accounts, addresses and
            labels) for a list or range of wallets
restore   - same as ‘create’, but additionally restore wallet metadata from
            the corresponding JSON dump files created with ‘dump’
export-outputs    - export outputs of watch-only wallets for later import
                    into their corresponding offline wallets
import-key-images - import key images signed by offline wallets into their
                    corresponding watch-only wallets


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

When ‘submit’ is used with --autosign, the transaction filename must be
omitted.


                    ‘DUMP’ AND ‘RESTORE’ OPERATION NOTES

These commands produce and read JSON wallet dump files with the same
filenames as their source wallets, plus a .dump extension.

It’s highly advisable to make regular dumps of your Monero wallets and back
up the dump files, which can be used to easily regenerate the wallets using
the ‘restore’ operation, should the need arise.  For watch-only autosigning
wallets, creating the dumps is as easy as executing ‘mmgen-xmrwallet
--autosign dump’ from your wallet directory.  The dump files are formatted
JSON and thus suitable for efficient incremental backup using git.


                    ‘TXVIEW’ AND ‘TXLIST’ OPERATION NOTES

Transactions are displayed in chronological order based on submit time or
creation time.  With --autosign, submitted transactions on the removable
device are displayed.


                              SECURITY WARNING

If you have an existing MMGen Monero hot wallet setup, you’re strongly
advised to migrate to offline autosigning to avoid further exposing your
private keys on your network-connected machine.  See OFFLINE AUTOSIGNING
and ‘Replacing Existing Hot Wallets with Watch-Only Wallets’ below.


                                  EXAMPLES

Note that the transacting examples in this section apply for a hot wallet
setup, which is now deprecated.  See OFFLINE AUTOSIGNING below.

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


                             OFFLINE AUTOSIGNING

                                  Tutorial

Master the basic concepts of the MMGen wallet system and the processes of
wallet creation, conversion and backup described in the Getting Started
guide.  Optionally create a default MMGen wallet on your offline machine
using ‘mmgen-walletgen’.  If you choose not to do this, you’ll be prompted
for a seed phrase at the start of each signing session.

Familiarize yourself with the autosigning setup process as described in
‘mmgen-autosign --help’.  Prepare your removable device and set up the
mountpoints on your offline and online machines according to the instructions
therein.  Install ‘monero-wallet-rpc’ on your offline machine and the Monero
CLI wallet and daemon binaries on your online machine.

On the offline machine, insert the removable device and execute:

$ mmgen-autosign --xmrwallets=1-2,7 setup

This will create 3 Monero signing wallets with indexes 1, 2 and 7 and primary
addresses matching your seed’s Monero addresses with the same indexes.  (Note
that these particular indexes are arbitrary, for purposes of illustration
only.  Feel free to choose your own list and/or range – or perhaps just the
number ‘1’ if one wallet is all you require).

These signing wallets are written to volatile memory and exist only for the
duration of the signing session, just like the temporary MMGen signing wallet
they’re generated from (see ‘mmgen-autosign --help’).

A viewkey-address file for the 3 addresses will also be written to the
removable device.  The data in this file will be used to create and access
watch-only wallets on your online machine that match the signing wallets
you’ve just created.

When the setup operation completes, extract the removable device and restart
the autosign script in wait mode:

$ mmgen-autosign --coins=xmr --stealth-led wait

Your only further physical interaction with the offline signing machine now
(assuming everything goes as planned) will be inserting and extracting the
removable device on it.  And this is the whole point of autosigning: to make
cold signing as convenient as possible, almost like transacting with a hot
wallet.

If your signing machine is an SoC with MMGen Wallet LED support (see
‘mmgen-autosign --help’), a quickly flashing LED will indicate that signing
is in progress, a slowly flashing LED an error condition, and no LED that the
program is idle and waiting for device insertion.

On your online machine, start monerod, wait until it’s fully synced with the
network, insert the removable device and execute:

$ mmgen-xmrwallet --autosign --restore-height=current create

This will create 3 watch-only wallets matching your 3 offline signing wallets
and write them to the current directory (an alternate wallet directory may be
specified with the --wallet-dir option).

Note that --restore-height=current is required to prevent a time-consuming
full sync of the wallets from the Genesis block, a meaningless waste of time
in this case since the wallets contain no funds.

Also make note of the --autosign option, a requirement for ALL autosigning
operations with ‘mmgen-xmrwallet’.

Now list your newly created wallets:

$ mmgen-xmrwallet --autosign list

Note that you can also use the ‘sync’ operation here, which produces more
abbreviated output than ‘list’.

Send some XMR (preferably a tiny amount) to the primary address of wallet #7.
Once the transaction has confirmed, invoke ‘sync’ or ‘list’ again to verify
the funds have arrived.

Since offline wallet #7 has no knowledge of the funds received by its online
counterpart, we need to update its state.  Export the outputs of watch-only
wallet #7 as follows:

$ mmgen-xmrwallet --autosign export-outputs 7

The outputs are now saved to the removable device and will be imported into
offline wallet #7 when you sign your first transaction.

Now you’re ready to begin transacting.  Let’s start by sweeping your funds in
wallet #7’s primary address (account 0) to a new address in the same account:

$ mmgen-xmrwallet --autosign sweep 7:0

This operation creates an unsigned sweep transaction and saves it to the
removable device.

Now extract the removable device and insert it on the offline machine.  Wait
for the quick LED flashing to stop (or the blue ‘safe to extract’ message, in
the absence of LED support), signalling that signing is complete.

Note that the offline wallet has performed two operations in one go here:
an import of wallet outputs from the previous step and the signing of your
just-created sweep transaction.

Extract the removable device, insert it on your online machine and submit the
signed sweep transaction to the watch-only wallet, which will broadcast it to
the network:

$ mmgen-xmrwallet --autosign submit

Note that you may also relay the transaction to a remote daemon, optionally
via a Tor proxy, using the --tx-relay-daemon option documented above.

Once your transaction has confirmed, invoke ‘list’ or ‘sync’ to view your
wallets’ balances.

Congratulations, you’ve performed your first autosigned Monero transaction!

For other examples, consult the EXAMPLES section above, noting the following
differences that apply to autosigning:

  1) The --autosign option must always be included.
  2) The key-address file argument must always be omitted.
  3) The ‘relay’ operation is replaced by ‘submit’, with TX filename omitted.
  4) Always remember to sign your transactions after a ‘sweep’ or ‘transfer’
     operation.
  5) Always remember to export a wallet’s outputs when it has received funds
     from an outside source.


                              Exporting Outputs

Exporting outputs from a watch-only wallet is generally required in only
three cases:

  a) at the start of each signing session (after ‘mmgen-autosign setup’);
  b) after the wallet has received funds from an outside source or another
     wallet; and
  c) after performing a ‘resubmit’ operation.

You might also need to do it, however, if an offline wallet is unable to sign
a transaction due to missing outputs.

Export outputs from a wallet as follows (note that the --rescan-blockchain
option is required only after a ‘resubmit’ – otherwise it should be omitted):

$ mmgen-xmrwallet --autosign --rescan-blockchain export-outputs <wallet index>

At the start of a new signing session, you must export outputs from ALL
wallets you intend to transact with.  This is necessary because the offline
signing wallets have just been created and know nothing about the state of
their watch-only counterparts.

Then insert the removable device on the offline machine to import the outputs
into the corresponding signing wallet(s) (and optionally redo any failed
transaction signing operation).  The signing wallet(s) will also create
signed key images.

Following a ‘resubmit’, you must then import the signed key images into your
online wallet as follows:

$ mmgen-xmrwallet --autosign import-key-images


           Replacing Existing Hot Wallets with Watch-Only Wallets

If you have an existing MMGen Monero hot wallet setup, you can migrate to
offline transaction signing by ‘cloning’ your existing hot wallets as
watch-only ones via the ‘dump’ and ‘restore’ operations described below.

For additional security, it’s also wise to create new watch-only wallets that
have never had keys exposed on an online machine and gradually transfer all
funds from your ‘cloned’ wallets to them.  The creation of new wallets is
explained in the Tutorial above.

Start the cloning process by making dump files of your hot wallets’ metadata
(accounts, subaddresses and labels).  ‘cd’ to the wallet directory (or use
--wallet-dir) and execute:

$ mmgen-xmrwallet dump /path/to/key-address-file.akeys{.mmenc}

If you’ve been transacting with the wallets, you know where their key-address
file is along with its encryption password, if any.  Supply an additional
index range and/or list at the end of the command line if the key-address
file contains more wallets than exist on disk or there are wallets you wish
to ignore.

Do a directory listing to verify that the dump files are present alongside
their source wallet files ending with ‘MoneroWallet’.  Then execute:

$ mmgen-xmrwallet --watch-only restore /path/to/key-address-file.akeys{.mmenc}

This will create watch-only wallets that “mirror” the old hot wallets and
populate them with the metadata saved in the dump files.

Note that watch-only wallet filenames end with ‘MoneroWatchOnlyWallet’.  Your
old hot wallets will be ignored from here on.  Eventually, you’ll want to
destroy them.

Your new wallets must now be synced with the blockchain.  Begin by starting
monerod and synchronizing with the network.

Mount ‘/mnt/mmgen_autosign’ and locate the file in the ‘xmr’ directory with
the .vkeys extension, which contains the passwords you’ll need to log into
the wallets.  This is a plain text file viewable with ‘cat’, ‘less’ or your
favorite text editor.

Then log into each watch-only wallet in turn as follows:

$ monero-wallet-cli --wallet <wallet filename>

Upon login, each wallet will begin syncing, a process which can take more
than an hour depending on your hardware.  Note, however, that the process
is interruptible: you may exit ‘monero-wallet-cli’ at any point, log back
in again and resume where you left off.

Once your watch-only wallets are synced, you need to export their outputs:

$ mmgen-xmrwallet --autosign export-outputs

Now insert the removable device on the offline machine and wait until the LED
stops flashing (or ‘safe to extract’).  The wallet outputs are now imported
into the signing wallets and corresponding signed key images have been
written to the removable device.

Insert the removable device on your online machine and import the key images
into your watch-only wallets:

$ mmgen-xmrwallet --autosign import-key-images

Congratulations, your watch-only wallets are now complete and you may begin
transacting!  First perform a ‘sync’ or ‘list’ to ensure that your balances
are correct.  Then you might try sweeping some funds as described in the
Tutorial above.

Once you’ve gained proficiency with the autosigning process and feel ready
to delete your old hot wallets, make sure to do so securely using ‘shred’,
‘wipe’ or some other secure deletion utility.
""".strip()
