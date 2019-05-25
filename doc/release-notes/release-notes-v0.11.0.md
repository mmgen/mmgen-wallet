### MMGen Version 0.11.0 Release Notes

#### Important new features:

 - Subwallets: 7538a94, d1b8aef, 82086c9 (see the [Subwallets][U] wiki page for
   additional information)

 - BIP69 ordering of transaction inputs and outputs: 6b2c138

 - Support for Microsoft Windows via MSYS2: dcab109, 13ab257 (see the
   [Install MMGen on Microsoft Windows][W] wiki page for complete
   information.  Windows users should note the following caveats:
     + no [autosigning][X] support
     + no [Monero wallet creation/syncing support][M] (due to password file
       descriptor issues with monero-wallet-cli)
     + due to unpredictable behavior of MSYS2's Python `getpass()`
       implementation, passwords containing non-ASCII symbols should be entered
       using the `--echo-passphrase` option or via a password file.  Otherwise,
       these symbols might end up being silently ignored.
     + Though MSYS2 support is well tested and considered stable, it’s a new
       feature and other glitches might remain.  If you think you've found a
       bug, don't hesistate to file an issue at
       <https://github.com/mmgen/mmgen/issues>.


#### Other changes/additions:

 - rewritten `mmgen-tool` utility: 729a547
 - new `tooltest2.py` test: 558fa58
 - new `unit_tests.py` test: e2d5146, ab8b5d0
 - rewritten and modularized `test.py` test suite: 91410dd
 - complete rewrite of SHA2 implementation used for Zcash addresses: 2b6dc95
 - use of `cryptography` package instead of `pycrypto`: 8a3b921, 7cc69a2
 - `pysha3` package dependency eliminated by using native Python implementation
   of Keccak hash function: a7126ed
 - dependencies on all Ethereum packages except `py_ecc` eliminated: 66d0f76,
   a7126ed
 - autosign: list non-MMGen output addresses and amounts as well as failed
   signing operations after each program run: d558822, 85236cd

This release has been tested on the following platforms:

        Ubuntu Bionic / x86_64
        Ubuntu Xenial (+Python 3.6.7) / x86_64
        Armbian Bionic / Orange Pi PC2 (no Parity or Monerod)
        Raspbian Stretch / Raspberry Pi B (no Parity or Monerod)
        Windows 7 Ultimate Eng. SP1 / MSYS2 / qemu-x86_64
        Windows 10 Professional Eng. / MSYS2 / qemu-x86_64

and with the following coin daemon versions:

        Bitcoin Core v0.17.1, v0.18.0
        Bitcoin-ABC v0.19.1, v0.19.6
        Litecoin Core v0.16.3, v0.17.1
        Monerod v0.14.0.2
        Parity Ethereum v2.5.1

Altcoin address generation has been additionally tested using the following
tools as references:

        zcash-mini a2b3504 (https://github.com/FiloSottile/zcash-mini)
        pycoin 6fb55ec (https://github.com/richardkiss/pycoin)
        vanitygen-plus 2212312 (https://github.com/exploitagency/vanitygen-plus)

[U]: https://github.com/mmgen/mmgen/wiki/Subwallets
[X]: https://github.com/mmgen/mmgen/wiki/autosign-[MMGen-command-help]
[W]: https://github.com/mmgen/mmgen/wiki/Install-MMGen-on-Microsoft-Windows
[M]: https://github.com/mmgen/mmgen/wiki/Altcoin-and-Forkcoin-Support#a_xmr
