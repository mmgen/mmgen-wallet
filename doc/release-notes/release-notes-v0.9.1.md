### MMGen version 0.9.1 Release Notes

#### BIP 125 replace-by-fee (RBF) support:

  - Create replaceable transactions using the `--rbf` switch to `mmgen-txcreate`
    and `mmgen-txdo`
  - Create, and optionally sign and send, replacement transactions with the new
    `mmgen-txbump` command

#### Satoshis-per-byte format:

  - Tx fees, both on the command line and at the interactive prompt, may be
    specified either as absolute BTC amounts or in satoshis-per-byte format (an
    integer followed by the letter 's')

#### Improved fee handling:

  - Completely reworked fee-handling code with better fee checking
  - default tx fee eliminated, `max_tx_fee` configurable in mmgen.cfg

#### Command scriptability:

  - New `--yes` switch makes `mmgen-txbump` and `mmgen-txsign` fully
    non-interactive and `mmgen-txcreate` and `mmgen-txsend` mostly
    non-interactive.

#### Bugfixes and usability improvements:

  - 'mmgen-tool listaddresses' now list addresses from multiple seeds correctly
  - Improved user interaction with all `mmgen-tx*` commands

The RBF and new fee functionality are documented in the [Getting Started][01] guide.

The guide has also been updated with a new [Preliminaries][03] section and a new
[Hot wallets and key-address files][02] section.

[01]: https://github.com/mmgen/mmgen/wiki/Getting-Started-with-MMGen#a_fee
[02]: https://github.com/mmgen/mmgen/wiki/Getting-Started-with-MMGen#a_hw
[03]: https://github.com/mmgen/mmgen/wiki/Getting-Started-with-MMGen#a_i
