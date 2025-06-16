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
help.swaptxcreate_examples: swaptxcreate and swaptxdo help examples for the MMGen Wallet suite
"""

from ..cfg import gc

def help(proto, cfg):

	return f"""
EXAMPLES:

  Display available swap assets:

    $ {gc.prog_name} -S

  Create a BTC-to-LTC swap transaction, prompting the user for transaction
  inputs.  The full value of the inputs, minus miner fees, will be swapped
  and sent to an unused address in the user’s LTC tracking wallet:

    $ {gc.prog_name} BTC LTC

  Same as above, but swap 0.123 BTC, minus miner fees, and send the change to
  an unused address in the BTC tracking wallet:

    $ {gc.prog_name} BTC 0.123 LTC

  Same as above, but specify that the change address be a Segwit P2SH (‘S’)
  address:

    $ {gc.prog_name} BTC 0.123 S LTC

  Same as above, but additionally specify that the destination LTC address be
  a compressed P2PKH (‘C’) address:

    $ {gc.prog_name} BTC 0.123 S LTC C

  Same as above, but specify the BTC change address explicitly and the
  destination LTC address by Seed ID and address type:

    $ {gc.prog_name} BTC 0.123 BEADCAFE:S:6 LTC BEADCAFE:C

  Abort the above swap by creating a replacement transaction that returns the
  funds to the originating tracking wallet (omit the transaction filename if
  using --autosign):

    $ mmgen-txbump BEADCAFE:S:6 [raw transaction file]

  Swap 0.123 BTC to a non-wallet address (not recommended):

    $ {gc.prog_name} BTC 0.123 LTC ltc1qaq8t3pakcftpk095tnqfv5cmmczysls0xx9388

  Create an LTC-to-BCH swap transaction, with the Litecoin daemon running on
  host ‘orion’ and Bitcoin Cash Node daemon on host ‘gemini’ with non-standard
  RPC port 8332.  Communicate with the swap quote server via Tor.

    $ {gc.prog_name} --ltc-rpc-host=orion --bch-rpc-host=gemini --bch-rpc-port=8332 --proxy=localhost:9050 LTC BCH

  After sending, check the status of the above swap’s LTC deposit transaction
  (omit the transaction filename if using --autosign):

    $ mmgen-txsend --ltc-rpc-host=orion --status [transaction file]

  Check whether the funds have arrived in the BCH destination wallet:

    $ mmgen-tool --coin=bch --bch-rpc-host=gemini twview minconf=0

  Create a Tether-to-LTC swap transaction for autosigning, connecting to the
  swap quote server via Tor:

    $ {gc.prog_name} --autosign --proxy=localhost:9050 ETH.USDT 1000 LTC

  After signing, send the transaction via public Etherscan proxy over Tor:

    $ mmgen-txsend --autosign --quiet --tx-proxy=etherscan --proxy=localhost:9050

  After sending, check the transaction status:

    $ mmgen-txsend --autosign --verbose --status

  Create a Tether-to-DAI swap transaction, with explicit destination account:

    $ {gc.prog_name} ETH.USDT 1000 ETH.DAI E:01234ABC:3

  Create a RUNE-to-BTC swap transaction, proxying requests to the remote
  Thornode server via Tor:

    $ {gc.prog_name} --proxy=localhost:9050 RUNE 1000 BTC

  Same as above, but proxy requests via the I2P router running on host gw1:

    $ https_proxy=http://gw1:4444 {gc.prog_name} --proxy=env RUNE 1000 BTC
"""
