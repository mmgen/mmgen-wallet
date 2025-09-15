```text
  MMGEN-REGTEST: Coin daemon regression test mode setup and operations for the MMGen suite
  USAGE:         mmgen-regtest [opts] <command>
  OPTIONS:
  -h, --help          Print this help message
      --longhelp      Print help message for long (global) options
  -b, --bdb-wallet    Create and use a legacy Berkeley DB coin daemon wallet
  -e, --empty         Don't fund Bob and Alice's wallets on setup
  -n, --setup-no-stop-daemon  Don't stop daemon after setup is finished
  -q, --quiet         Produce quieter output
  -v, --verbose       Produce more verbose output


                           AVAILABLE COMMANDS

    setup           - set up Bob and Alice regtest mode
    start           - start the regtest coin daemon
    stop            - stop the regtest coin daemon
    generate N      - mine N blocks (defaults to 1)
    send ADDR AMT   - send amount AMT of miner funds to address ADDR
    state           - show current state of daemon (ready, busy, or stopped)
    balances        - get Bob and Alice's balances
    mempool         - show transaction IDs in mempool
    cli             - execute an RPC call with supplied arguments
    wallet_cli      - execute a wallet RPC call with supplied arguments (wallet
                      is first argument)

  MMGEN-WALLET 16.0.0            September 2025               MMGEN-REGTEST(1)
```
