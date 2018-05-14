### MMGen Version 0.9.8 Release Notes

#### Interesting new features:

  - Bech32 address support (BTC: `e4114ee`, LTC: `2cb4df7`)
  - Stealth mnemonic entry (`90ebc94`)

#### New comprehensive UTF-8 support:

  - UTF-8 filenames and paths (`896c7fe`)
  - UTF-8 tracking wallet comments (`d49c862`)
  - UTF-8 wallet labels (`2104273`)
  - Proper formatting of CJK strings (`ea6629d`)

#### Security/bugfixes:

  - `max_tx_file_size` and other TX file checks (`cf20311`)
  - TX size estimation fixes (`ed2b94c`)
  - Require brainwallet and passwords to be UTF-8 encoded (`9f2153c`)

#### Coin daemons used for testing:

  - Bitcoin Core v0.16.0
  - Litecoin Core v0.16.0rc1
  - Bitcoin-ABC v0.17.1
  - Monero v0.12.0.0 (Lithium Luna)

#### Tools used for testing:

  - Zcash-Mini (`a2b3504`)
  - Pycoin v0.90a
  - Pyethereum v2.1.2
  - Vanitygen-Plus (`5ca3d22`)

Note that some features, notably UTF-8 filename and path support, do not work
on the MS Windows/MinGW platform.  See the file [doc/README.mswin.md][1] for
details.

All user input is now required to be UTF-8 encoded.  This will break backward
compatibility in the unlikely event that a) you're using a non-ASCII wallet
password or brainwallet, and b) your native charset is non-UTF-8.  If this is
the case, you must change your wallet password to an ASCII one (or export your
brainwallet to another MMGen wallet format) using an older version of MMGen
before upgrading.

[1]: ../../doc/README.mswin.md
