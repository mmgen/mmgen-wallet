### [BTC](#a_btc) | [ETH](#a_eth) | [XMR](#a_xmr)

### <a id="a_btc">mmgen-addrimport --coin=btc --help</a>

```text
  MMGEN-ADDRIMPORT: Import addresses into an MMGen tracking wallet

  USAGE: mmgen-addrimport [opts] [MMGen address file]

  OPTIONS:
  -h, --help         Print this help message
      --longhelp     Print help message for long (global) options
  -A, --address ADDR Import the single coin address ADDR
  -b, --batch        Import all addresses in one RPC call (where applicable)
  -l, --addrlist     Address source is a flat list of non-MMGen coin addresses
  -k, --keyaddr-file Address source is a key-address file
  -q, --quiet        Suppress warnings
  -r, --rescan       Update address balances by selectively rescanning the
                     blockchain for unspent outputs that include the imported
                     address(es).  Required if any of the imported addresses
                     are already in the blockchain and have a balance.


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
  without balances will be displayed as new.

  MMGEN-WALLET 16.1.dev37        May 2026                  MMGEN-ADDRIMPORT(1)
```

<br>

### <a id="a_eth">mmgen-addrimport --coin=eth --help</a>

```text
  MMGEN-ADDRIMPORT: Import addresses into an MMGen tracking wallet

  USAGE: mmgen-addrimport --coin=eth [opts] [MMGen address file]

  OPTIONS:
  -h, --help         Print this help message
      --longhelp     Print help message for long (global) options
  -A, --address ADDR Import the single coin address ADDR
  -b, --batch        Import all addresses in one RPC call (where applicable)
  -l, --addrlist     Address source is a flat list of non-MMGen coin addresses
  -k, --keyaddr-file Address source is a key-address file
  -q, --quiet        Suppress warnings
  -t, --token-addr ADDR Import addresses for ERC20 token with address ADDR

  MMGEN-WALLET 16.1.dev37        May 2026                  MMGEN-ADDRIMPORT(1)
```

<br>

### <a id="a_xmr">mmgen-addrimport --coin=xmr --help</a>

```text
  MMGEN-ADDRIMPORT: Import addresses into an MMGen tracking wallet

  USAGE: mmgen-addrimport --coin=xmr [opts]

  OPTIONS:
  -h, --help         Print this help message
      --longhelp     Print help message for long (global) options
  -a, --autosign     Import addresses from pre-created key-address file on the
                     removable device.  The removable device is mounted and
                     unmounted automatically.  See notes below.
  -q, --quiet        Suppress warnings


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

  If a view-only wallet for a given index already exists, it’s left untouched
  and no action is performed.  To add view-only wallets to your tracking wallet,
  just specify additional wallet indexes via --xmrwallets during the offline
  setup process.

  MMGEN-WALLET 16.1.dev37        May 2026                  MMGEN-ADDRIMPORT(1)
```
