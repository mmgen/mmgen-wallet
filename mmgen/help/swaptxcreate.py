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
help.swaptxcreate: swaptxcreate and swaptxdo help notes for the MMGen Wallet suite
"""

def help(proto, cfg):
	return """
This script is similar in operation to ‘mmgen-txcreate’, only with additional
steps.  Users are advised to first familiarize themselves with the use of that
script before attempting to perform a swap with this one.

The tracking wallets of both the send and receive coins must be available when
the script is invoked.  If the two coin daemons are running on different hosts
than the script, or with non-standard ports, coin-specific RPC options may be
required (see EXAMPLES below).

The swap protocol’s quote server on the Internet must be reachable either
directly or via the SOCKS5 proxy specified with the --proxy option. To improve
privacy, it’s recommended to proxy requests to the quote server via Tor or
some other anonymity network.

The resulting transaction file is saved, signed, sent, and optionally bumped,
exactly the same way as one created with ‘mmgen-txcreate’.  Autosign with
automount is likewise supported via the --autosign option.

The command line must contain at minimum a send coin (COIN1) and receive coin
(COIN2) symbol.  Currently supported coins are BTC, LTC, BCH and ETH.  All
other arguments are optional.  If AMT is specified, the specified value of
send coin will be swapped and the rest returned to a change address in the
originating tracking wallet.  Otherwise, the entire value of the interactively
selected inputs will be swapped.

By default, the change (if applicable) and destination addresses are chosen
automatically by finding the lowest-indexed unused addresses of the preferred
address types in the send and receive tracking wallets.  For Bitcoin and
forks, types ‘B’, ‘S’ and ‘C’ (see ADDRESS TYPES below) are searched in that
order for unused addresses.  Note that sending to an unused address may be
undesirable for Ethereum, where address (i.e. account) reuse is the norm.  In
that case, the user should specify a destination address on the command line.

If the wallet contains eligible unused addresses with multiple Seed IDs, the
user will be presented with a list of the lowest-indexed addresses of
preferred type for each Seed ID and prompted to choose from among them.

Change and destination addresses may also be specified manually with the
CHG_ADDR and ADDR arguments.  These may be given as full MMGen IDs or in the
form ADDRTYPE_CODE or SEED_ID:ADDRTYPE_CODE (see EXAMPLES below and the
‘mmgen-txcreate’ help screen for details).  For Ethereum, the CHG_ADDR
argument is not supported.

While discouraged, sending change or swapping to non-wallet addresses is also
supported, in which case the signing script (‘mmgen-txsign’ or ‘mmgen-
autosign’, as applicable) must be invoked with the --allow-non-wallet-swap
option.

Rather than specifying a transaction fee on the command line, it’s advisable
to start with the fee suggested by the swap protocol quote server (the script
does this automatically) and then adjust the fee interactively if desired.

When choosing a fee, bear in mind that the longer the transaction remains
unconfirmed, the greater the risk that the vault address will expire, leading
to loss of funds.  It’s therefore recommended to learn how to create, sign and
send replacement transactions with ‘mmgen-txbump’ before performing a swap
with this script.  When bumping a stuck swap transaction, the safest option
is to create a replacement transaction with one output that returns funds back
to the originating tracking wallet, thus aborting the swap, rather than one
that merely increases the fee (see EXAMPLES below).

Before broadcasting the transaction, it’s a good idea to double-check the
vault address on a block explorer such as thorchain.net or runescan.io.

The MMGen Node Tools suite contains two useful tools to help with fine-tuning
transaction fees, ‘mmnode-feeview’ and ‘mmnode-blocks-info’, in addition to
‘mmnode-ticker’, which can be used to calculate the current cross-rate between
the asset pair of a swap, as well as the total receive value in terms of send
value.


                                TRADE LIMIT

A target value for the swap may be set, known as the “trade limit”.  If
this target cannot be met, the network will refund the user’s coins, minus
transaction fees (note that the refund goes to the address associated with the
transaction’s first input, leading to coin reuse).  Since under certain
circumstances large amounts of slippage can occur, resulting in significant
losses, setting a trade limit is highly recommended.

The target may be given as either an absolute coin amount or percentage value.
In the latter case, it’s interpreted as the percentage below the “expected
amount out” returned by the swap quote server.  Zero or negative percentage
values are also accepted, but are likely to result in your coins being
refunded.

The trade limit is rounded to four digits of precision in order to reduce
transaction size.
"""
