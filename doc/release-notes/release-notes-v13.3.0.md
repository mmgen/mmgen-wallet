### MMGen Version 13.3.0 Release Notes

#### Notable new features for this release:

 - automatic change address selection
 - curses-like scrolling interface for tracking wallet views
 - offline transaction autosigning for Monero
 - Config API (encapsulates configuration data, making the entire MMGen
   code base usable as a library for other Python projects)

#### New features in chronological order:

 - a78be652: Support Monero integrated addresses

 - 164ef9d2: mmgen-xmrwallet: new `txview` operation

 - 1d392f17: mmgen-tool listaddresses: fully reimplemented UI (same as `twview`
   and `txhist`)

 - 68caeb31: mmgen-txcreate: warn user if change address is used

 - cbe74981: mmgen-txcreate: automatic change address selection

 - 045fdefd: mmgen-txcreate: automatic change address selection by address type

 - f62322b1: mmgen-tool twexport: address pruning

 - b26657fb: Curses-like scrolling UI for tracking wallet views via `--scroll`
   option

 - 55528989: proto.btc.tx: set sequence numbers for all inputs explicitly

 - 94125052: mmgen-txcreate: consider addresses in the tracking wallet with
   labels to be reserved, i.e. equivalent to used, for purposes of automatic
   change address selection (can be overridden with `--autochg-ignore-labels`
   option)

 - c7adb56e: Config API, Part I (eliminate global configuration variables)

 - e90e25b2: Config API, Part II (make entire MMGen code base usable as a
   library for external projects - usage example provided in script
   `examples/coin-daemon-info.py`)

 - dc685e9c: mmgen-keygen: new viewkey-address file type via `--viewkeys` option

 - 686fdfcc: mmgen-autosign: use default wallet as autosign wallet by default

 - de77f9c2: Monero offline transaction autosigning (invoke `mmgen-xmrwallet
   --help` for usage information and tutorial)

 - a1986fe6: mmgen-xmrwallet: new `txlist` operation

#### Windows/MSYS2 changes:

 - ebb77548: use native MSYS2 terminal and UCRT64 environment by default

#### Testing changes:

 - 4aa9f731: use monero-python instead of MoneroPy as reference tool

 - 056de3bc: test.py: add `--demo` option

 - e1f68963: use pycryptodome/pycryptodomex for Keccak testing

...plus loads of bugfixes, cleanups and code rewrites
(345 commits, 373 files changed, 17902 insertions, 10670 deletions)


Requires Python >= 3.7 (tested on 3.7, 3.9, 3.10 and 3.11)

This release has been tested on the following platforms:

        Debian 10 (Buster) / x86_64
        Debian 11 (Bullseye) / x86_64
        Debian 12 (Bookworm) / x86_64
        Ubuntu 22.04 (Jammy) / x86_64
        Arch Linux (Python 3.11) / x86_64
        ArchLinuxArm [userspace] (Python 3.11) / Rock Pi 4 (armv8)
        Debian 11 (Bullseye) [Armbian] / Rock Pi 4 (armv8)
        Debian 11 (Bullseye) [Armbian] / Orange Pi PC2 (armv8) [BTC + XMR autosign]
        Windows 10 Enterprise / MSYS2 2023.03.18 / x86_64 [qemu]

and with the following coin daemon versions:

        Bitcoin Core 25.0.0
        Bitcoin-Cash-Node 26.0.0
        Litecoin Core 0.21.2.2
        Monerod 0.18.2.2
        Go-Ethereum (Geth) 1.11.16
        Parity Ethereum 2.7.2

Solc v0.8.7 is required for ERC20 token contract creation

Altcoin address generation has been additionally tested using the following
reference tools:

        zcash-mini a2b3504 (https://github.com/FiloSottile/zcash-mini)
        pycoin 0.92.20220529 (https://github.com/richardkiss/pycoin)
        vanitygen-plusplus e7858035 (https://github.com/10gic/vanitygen-plusplus)
        monero-python 1.1.1 (https://github.com/monero-ecosystem/monero-python)
        ethkey (OpenEthereum 3.3.5)
