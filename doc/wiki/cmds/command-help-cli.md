```text
  MMGEN-CLI: Communicate with a coin daemon via its JSON-RPC interface
  USAGE:     mmgen-cli [opts] <command> <command args>
  OPTIONS:
  -h, --help             Print this help message
      --longhelp         Print help message for long (global) options
  -a, --ascii-output     Ensure that output is ASCII encoded
  -w, --wallet NAME      Use tracking wallet with name NAME


  The utility accepts all MMGen global configuration options and sources the user
  config file, allowing users to preconfigure hosts, ports, passwords, datadirs,
  tracking wallets and so forth, thus saving a great deal of typing at the
  command line. This behavior may be overridden with the --skip-cfg-file option.

  Arguments are given in JSON format, with lowercase ‘true’, ‘false’ and ‘null’
  for booleans and None, and double-quoted strings in dicts and lists.


                                     EXAMPLES

    $ mmgen-cli --wallet=wallet2 listreceivedbyaddress 0 true

    $ mmgen-cli --coin=ltc --rpc-host=orion getblockcount

    $ mmgen-cli --regtest=1 --wallet=bob getbalance

    $ mmgen-cli --coin=eth eth_getBalance 0x00000000219ab540356cBB839Cbe05303d7705Fa latest

    $ mmgen-cli createrawtransaction \
      '[{"txid":"832f5aa9af55dc453314e26869c8f96db1f2a9acac9f23ae18d396903971e0c6","vout":0}]' \
      '[{"1111111111111111111114oLvT2":0.001}]'

  MMGEN-WALLET 16.0.0            September 2025                   MMGEN-CLI(1)
```
