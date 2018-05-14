### MMGen version 0.8.8 Release Notes

#### Data directory, config file and default wallet support:

  - Data directory is `~/.mmgen`; config file is `mmgen.cfg`.
  - When default wallet is present in data directory, specifying the wallet
    on the command line is optional.
  - Datadir structure mirrors that of Bitcoin Core: mainnet and testnet share
    a common config file, with testnet putting its own files, including the
    default wallet, in the subdirectory 'testnet3'.
  - Global vars are now overriden in this order:
    1) config file
    2) environmental variables beginning with `MMGEN_` (listed in globalvars.py)
    3) command line
  - Long (common) opts added for setting global vars; display with `--longhelp`.

  The test suite has been updated to test these new features.

#### Other changes:

  - Always get user entropy, even for non-critical randomness, unless `-r0`.
  - rpcuser,rpcpassword now override cookie authentication, as with Core.
  - Communication with remote bitcoind supported with `--rpc-host` option.
  - Testnet use can be overridden with the `--testnet=0|1` option.
