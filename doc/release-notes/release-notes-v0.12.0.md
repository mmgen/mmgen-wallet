### MMGen Version 0.12.0 Release Notes

#### Important new features:

 - XOR seed splitting: 7311f474, 237567bc, c7ca0c3d (see
   [XOR-Seed-Splitting:-Theory-and-Practice][xo] for additional information)
 - Full BIP39 mnemonic support: 8519b68b, 8705e57b
 - Monero new-style mnemonic support: cfa16418
 - New dieroll wallet format, interactive dieroll entry: c7786369, 4714ef84
 - ETH tracking-wallet balance caching, Parity light client optimizations:
   d0f8c44b

#### Other changes/additions/improvements:

 - New plain hex file wallet format: 15ac6c69
 - libsecp256k1 support for MSYS2: c260fbf9
 - Monero wallet creation/syncing tool reimplemented, now works under MSYS2:
   3951925a
 - New Tool API interface: f8056630
 - New [Daemon control interface][dc] and [test daemon start/stop utilities][ss]
 - Full automation of test suite with automatic starting/stopping of daemons
 - New wiki documentation for the [Test Suite][ts] and [Tool API][ta]
 - UTF8 password entry works reliably under MSYS2, warnings disabled
 - Plus lots of code reorganization, cleanups, bugfixes and new tests!

This release has been tested on the following platforms:

        Debian Buster / x86_64
        Ubuntu Bionic / x86_64 / qemu-x86_64
        Armbian Bionic / Orange Pi PC2 (armv8) 
        Raspbian Buster / Raspberry Pi B (armv7) (no Parity, no Monerod)
        Windows 10 Enterprise Eng. / MSYS2 / qemu-x86_64

and with the following coin daemon versions:

        Bitcoin Core 0.17.1, 0.19.0.1
        Bitcoin-ABC 0.21.0
        Litecoin Core 0.17.1
        Monerod 0.15.0.1
        Parity Ethereum 2.7.2*

        * Parity crashes on startup on some systems when in developer mode,
        causing the 'eth' test to fail.  This is a problem with Parity, not
        MMGen.  On cleanly installed systems, Parity and the 'eth' test run
        without issue on all tested platforms.

Altcoin address generation has been additionally tested using the following
tools as references:

        zcash-mini a2b35042 (https://github.com/FiloSottile/zcash-mini)
        pycoin 11f60a7c (https://github.com/richardkiss/pycoin)
        vanitygen-plus 22123128 (https://github.com/exploitagency/vanitygen-plus)
        MoneroPy 98e7feb2 (https://github.com/bigreddmachine/MoneroPy)
        ethkey 2.7.2 (https://github.com/paritytech/parity-ethereum)

[xo]: https://github.com/mmgen/mmgen/wiki/XOR-Seed-Splitting:-Theory-and-Practice
[dc]: https://github.com/mmgen/mmgen/blob/master/mmgen/daemon.py
[ss]: https://github.com/mmgen/mmgen/blob/master/test/start-coin-daemons.py
[ts]: https://github.com/mmgen/mmgen/wiki/Test-Suite
[ta]: https://github.com/mmgen/mmgen/wiki/Tool-API
