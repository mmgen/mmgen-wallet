### [BTC](#a_btc) | [RUNE](#a_rune)

### <a id="a_btc">mmgen-remote --coin=btc --help</a>

```text
  MMGEN-REMOTE: Retrieve data from a remote JSON-RPC server

  USAGE: mmgen-remote [OPTS] COMMAND ARGS

  OPTIONS:
  -h, --help       Print this help message
      --longhelp   Print help message for long (global) options
  -d, --outdir D   Output logfile to directory ‘D’ instead of working dir
  -l, --log        Log output to file

  COMMANDS:
    No configured commands for coin BTC
    Supported coins: RUNE

  MMGEN-WALLET 17.0.0            November 2026                 MMGEN-REMOTE(1)
```

<br>

### <a id="a_rune">mmgen-remote --coin=rune --help</a>

```text
  MMGEN-REMOTE: Retrieve data from a remote JSON-RPC server

  USAGE: mmgen-remote --coin=rune [OPTS] COMMAND ARGS

  OPTIONS:
  -h, --help       Print this help message
      --longhelp   Print help message for long (global) options
  -d, --outdir D   Output logfile to directory ‘D’ instead of working dir
  -l, --log        Log output to file
  -s, --swap-proto Swap protocol to use (Default: thorchain, Choices: 'thorchain')
  -x, --proxy P    Connect to remote server(s) via SOCKS5h proxy P (host:port)
                   Use special value ‘env’ to honor *_PROXY env vars instead.

  Communicating with a remote server can harm your privacy!
  To improve anonymity, proxy requests via Tor or I2P

  COMMANDS:

    Retrieve data from a remote THORChain JSON-RPC endpoint:

      ping            - ping the remote REST endpoint
      health          - check the health of the THORChain network
      pools           - get available pools on the THORChain network
      lastblock       - get last block info for all coins or a given coin
      mimir           - get Mimir constants for the THORChain network
      actions         - get actions for a given address or TxID
      inbound_addrs   - get current inbound (vault) addresses
      acct_info       - get account information for a given address
      balance         - get balance for a given address
      quote           - get a swap quote for a given send asset, receive asset
                        and amount
      tx_info         - get information for a transaction by TxID
      get_refnum      - get reference memo info for a reference request
                        transaction by TxID
      validate_refnum - check that given asset/reference combination is valid
      validate_amt    - check that given asset/amount combination resolves to a
                        valid reference

  For individual command usage, invoke ‘mmgen-remote --coin=rune help COMMAND’

  MMGEN-WALLET 17.0.0            November 2026                 MMGEN-REMOTE(1)
```
