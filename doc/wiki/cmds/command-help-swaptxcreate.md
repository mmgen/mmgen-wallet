```text
  MMGEN-SWAPTXCREATE: Create a DEX swap transaction from one MMGen tracking wallet to another
  USAGE:              mmgen-swaptxcreate [opts] COIN1 [AMT CHG_ADDR] COIN2 [ADDR] [addr file ...]
  OPTIONS:
  -h, --help            Print this help message
      --longhelp        Print help message for long (global) options
  -a, --autosign        Create a transaction for offline autosigning (see
                        ‘mmgen-autosign’). The removable device is mounted and
                        unmounted automatically
  -A, --fee-adjust   f  Adjust transaction fee by factor ‘f’ (see below)
  -B, --no-blank        Don't blank screen before displaying unspent outputs
  -c, --comment-file f  Source the transaction's comment from file 'f'
  -C, --fee-estimate-confs c Desired number of confirmations for fee estimation
                        (default: 3)
  -d, --outdir       d  Specify an alternate directory 'd' for output
  -E, --fee-estimate-mode M Specify the network fee estimate mode.  Choices:
                        'conservative','economical'.  Default: 'conservative'
  -f, --fee          f  Transaction fee, as a decimal BTC amount or as
                        satoshis per byte (an integer followed by ‘s’).
                        See FEE SPECIFICATION below.  If omitted, fee will be
                        calculated using network fee estimation.
  -g, --gas N           Set the gas limit for Ethereum (see GAS LIMIT below)
  -G, --router-gas N    Set the gas limit for the Ethereum router contract
                        (integer).  When unset, a hardcoded default will be
                        used.  Applicable only for swaps from token assets.
  -i, --info            Display unspent outputs and exit
  -I, --inputs       i  Specify transaction inputs (comma-separated list of
                        MMGen IDs or coin addresses).  Note that ALL unspent
                        outputs associated with each address will be included.
  -l, --trade-limit L   Minimum swap amount, as either percentage or absolute
                        coin amount (see TRADE LIMIT below)
  -L, --autochg-ignore-labels Ignore labels when autoselecting change addresses
  -m, --minconf      n  Minimum number of confirmations required to spend
                        outputs (default: 1)
  -q, --quiet           Suppress warnings; overwrite files without prompting
  -r, --stream-interval N Set block interval for streaming swap (default: 3)
  -s, --swap-proto      Swap protocol to use (Default: thorchain,
                        Choices: 'thorchain')
  -S, --list-assets     List available swap assets
  -v, --verbose         Produce more verbose output
  -V, --vsize-adj    f  Adjust transaction's estimated vsize by factor 'f'
  -x, --proxy P         Fetch the swap quote via SOCKS5h proxy ‘P’ (host:port).
                        Use special value ‘env’ to honor *_PROXY environment
                        vars instead.
  -y, --yes             Answer 'yes' to prompts, suppress non-essential output


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


  ADDRESS TYPES:

    Code Type           Description
    ---- ----           -----------
    ‘L’  legacy       - Legacy uncompressed address
    ‘C’  compressed   - Compressed P2PKH address
    ‘S’  segwit       - Segwit P2SH-P2WPKH address
    ‘B’  bech32       - Native Segwit (Bech32) address
    ‘X’  bech32x      - Cross-chain Bech32 address
    ‘E’  ethereum     - Ethereum address
    ‘Z’  zcash_z      - Zcash z-address
    ‘M’  monero       - Monero address


                                   GAS LIMIT

  This option specifies the maximum gas allowance for an Ethereum transaction.
  It’s generally of interest only for token transactions or swap transactions
  from token assets.

  Parameter must be an integer or one of the special values ‘fallback’ (for a
  locally computed sane default) or ‘auto’ (for gas estimate via an RPC call,
  in the case of a token transaction, or locally computed default, in the case
  of a standard transaction). The default is ‘auto’.


                                 FEE SPECIFICATION

  Transaction fees, both on the command line and at the interactive prompt, may
  be specified as either absolute coin amounts, using a plain decimal number, or
  as satoshis per byte, using an integer followed by ‘s’, for satoshi (for
  Bitcoin, Litecoin and Bitcoin Cash), or gas price, using an integer followed
  by ‘w’,‘K’,‘M’,‘G’,‘s’ or ‘f’, for wei, Kwei, Mwei, Gwei, szabo and finney,
  respectively (for Ethereum)


  EXAMPLES:

    Display available swap assets:

      $ mmgen-swaptxcreate -S

    Create a BTC-to-LTC swap transaction, prompting the user for transaction
    inputs.  The full value of the inputs, minus miner fees, will be swapped
    and sent to an unused address in the user’s LTC tracking wallet:

      $ mmgen-swaptxcreate BTC LTC

    Same as above, but swap 0.123 BTC, minus miner fees, and send the change to
    an unused address in the BTC tracking wallet:

      $ mmgen-swaptxcreate BTC 0.123 LTC

    Same as above, but specify that the change address be a Segwit P2SH (‘S’)
    address:

      $ mmgen-swaptxcreate BTC 0.123 S LTC

    Same as above, but additionally specify that the destination LTC address be
    a compressed P2PKH (‘C’) address:

      $ mmgen-swaptxcreate BTC 0.123 S LTC C

    Same as above, but specify the BTC change address explicitly and the
    destination LTC address by Seed ID and address type:

      $ mmgen-swaptxcreate BTC 0.123 BEADCAFE:S:6 LTC BEADCAFE:C

    Abort the above swap by creating a replacement transaction that returns the
    funds to the originating tracking wallet (omit the transaction filename if
    using --autosign):

      $ mmgen-txbump BEADCAFE:S:6 [raw transaction file]

    Swap 0.123 BTC to a non-wallet address (not recommended):

      $ mmgen-swaptxcreate BTC 0.123 LTC ltc1qaq8t3pakcftpk095tnqfv5cmmczysls0xx9388

    Create an LTC-to-BCH swap transaction, with the Litecoin daemon running on
    host ‘orion’ and Bitcoin Cash Node daemon on host ‘gemini’ with non-standard
    RPC port 8332.  Communicate with the swap quote server via Tor.

      $ mmgen-swaptxcreate --ltc-rpc-host=orion --bch-rpc-host=gemini --bch-rpc-port=8332 --proxy=localhost:9050 LTC BCH

    After sending, check the status of the above swap’s LTC deposit transaction
    (omit the transaction filename if using --autosign):

      $ mmgen-txsend --ltc-rpc-host=orion --status [transaction file]

    Check whether the funds have arrived in the BCH destination wallet:

      $ mmgen-tool --coin=bch --bch-rpc-host=gemini twview minconf=0

    Create a Tether-to-LTC swap transaction for autosigning, connecting to the
    swap quote server via Tor:

      $ mmgen-swaptxcreate --autosign --proxy=localhost:9050 ETH.USDT 1000 LTC

    After signing, send the transaction via public Etherscan proxy over Tor:

      $ mmgen-txsend --autosign --quiet --tx-proxy=etherscan --proxy=localhost:9050

    After sending, check the transaction status:

      $ mmgen-txsend --autosign --verbose --status

    Create a Tether-to-DAI swap transaction, with explicit destination account:

      $ mmgen-swaptxcreate ETH.USDT 1000 ETH.DAI E:01234ABC:3

    Create a RUNE-to-BTC swap transaction, proxying requests to the remote
    Thornode server via Tor:

      $ mmgen-swaptxcreate --proxy=localhost:9050 RUNE 1000 BTC

    Same as above, but proxy requests via the I2P router running on host gw1:

      $ https_proxy=http://gw1:4444 mmgen-swaptxcreate --proxy=env RUNE 1000 BTC

  MMGEN-WALLET 16.0.0            September 2025           MMGEN-SWAPTXCREATE(1)
```
