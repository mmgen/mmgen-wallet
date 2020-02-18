### MMGen Version 0.12.0 Release Notes

#### Important new features:

 - XOR seed splitting: 7311f474, 237567bc, c7ca0c3d (see
   [XOR-Seed-Splitting:-Theory-and-Practice][xo] for additional information)
 - ETH tracking-wallet balance caching, Parity light client optimizations:
   d0f8c44b
 - Full BIP39 mnemonic support: 8519b68b, 8705e57b
 - Monero new-style mnemonic support: cfa16418
 - New die-roll wallet format, interactive die-roll entry: c7786369, 4714ef84

#### Other changes/additions/improvements:

 - New plain hex file wallet format: 15ac6c69
 - libsecp256k1 support for MSYS2: c260fbf9
 - Monero wallet creation/syncing tool reimplemented, now works under MSYS2:
   3951925a
 - New Tool API interface: f8056630
 - Full automation of test suite, automatic starting/stopping of daemons
 - Plus lots of code cleanups, bugfixes, and additional tests!

This release has been tested on the following platforms:

        Debian Buster / x86_64
        Windows 10 Enterprise Eng. / MSYS2 / qemu-x86_64

and with the following coin daemon versions:

        Bitcoin Core v0.19.0.1
        Bitcoin-ABC v0.20.9
        Litecoin Core v0.17.1
        Monerod v0.15.0.1
        Parity Ethereum v2.7.2

Testing TBD on the following platforms:

        Ubuntu Bionic / x86_64 / qemu-x86_64
        Ubuntu Xenial (+Python 3.6.7) / x86_64
        Armbian Bionic / Orange Pi PC2 (no Parity or Monerod)
        Raspbian Stretch / Raspberry Pi B (no Parity or Monerod)

Altcoin address generation has been additionally tested using the following
tools as references:

        zcash-mini a2b35042 (https://github.com/FiloSottile/zcash-mini)
        pycoin 11f60a7c (https://github.com/richardkiss/pycoin)
        vanitygen-plus 22123128 (https://github.com/exploitagency/vanitygen-plus)

[xo]: https://github.com/mmgen/mmgen/wiki/XOR-Seed-Splitting:-Theory-and-Practice.md
