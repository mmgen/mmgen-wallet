```text
  MMGEN-ADDRIMPORT: Import addresses into an MMGen tracking wallet
  USAGE:            mmgen-addrimport [opts] [MMGen address file]
  OPTIONS:
  -h, --help         Print this help message
      --longhelp     Print help message for long (global) options
  -a, --address a    Import the single coin address 'a'
  -b, --batch        Import all addresses in one RPC call
  -l, --addrlist     Address source is a flat list of non-MMGen coin addresses
  -k, --keyaddr-file Address source is a key-address file
  -q, --quiet        Suppress warnings
  -r, --rescan       Update address balances by selectively rescanning the
                     blockchain for unspent outputs that include the imported
                     address(es).  Required if any of the imported addresses
                     are already in the blockchain and have a balance.
  -t, --token-addr A Import addresses for ERC20 token with address 'A'


  This command can also be used to update the comment fields or balances of
  addresses already in the tracking wallet.

  Rescanning now uses the ‘scantxoutset’ RPC call and a selective scan of
  blocks containing the relevant UTXOs for much faster performance than the
  previous implementation.  The rescan operation typically takes around two
  minutes total, independent of the number of addresses imported.

  Bear in mind that the UTXO scan will not find historical transactions: to add
  them to the tracking wallet, you must perform a full or partial rescan of the
  blockchain with the ‘mmgen-tool rescan_blockchain’ utility.  A full rescan of
  the blockchain may take up to several hours.

  It’s recommended to use ‘--rpc-backend=aio’ with ‘--rescan’.

  MMGEN-WALLET 16.0.0            September 2025            MMGEN-ADDRIMPORT(1)
```
