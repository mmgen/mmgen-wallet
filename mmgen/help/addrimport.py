#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
help.addrimport: addrimport help notes for the MMGen Wallet suite
"""

def help(proto, cfg):
	match proto.base_proto:
		case 'Bitcoin':
			return """
Rescanning now uses the ‘scantxoutset’ RPC call and a selective scan of
blocks containing the relevant UTXOs for much faster performance than the
previous implementation.  The rescan operation typically takes around two
minutes total, independent of the number of addresses imported.

It’s recommended to use ‘--rpc-backend=aio’ with ‘--rescan’.

Bear in mind that the UTXO scan will not find historical transactions: to add
them to the tracking wallet, you must perform a full or partial rescan of the
blockchain with the ‘mmgen-tool rescan_blockchain’ utility.  A full rescan of
the blockchain may take up to several hours.

A full rescan is required if you plan to use ‘mmgen-tool txhist’ or the
automatic change address functionality of ‘mmgen-txcreate’, or wish to see
which addresses in your tracking wallet are used.  Without it, all addresses
without balances will be displayed as new."""
		case 'Monero':
			return """
For Monero, --autosign is required, and a key-address file on the removable
device is used instead of a user-specified address file as with other coins.

When ‘mmgen-autosign setup’ (or ‘xmr_setup’) is run with the --xmrwallets
option, an ephemeral Monero wallet is created for each wallet number listed,
to be used for transaction signing. In addition, a key-address file is created
on the removable device, with an address and viewkey matching the base address
of each signing wallet.

This script uses that file to create an online view-only Monero wallet to
match each offline signing wallet.  The set of view-only wallets currently
configured via --xmrwallets comprises the user’s tracking wallet.

If a view-only wallet for a given address already exists, it’s left untouched
and no action is performed.  To add view-only wallets to your tracking wallet,
just specify additional wallet indexes via --xmrwallets during the offline
setup process."""
		case _:
			return ''
