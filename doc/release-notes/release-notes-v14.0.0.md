### MMGen Wallet Version 14.0.0 Release Notes

This special release marks the MMGen Project’s 10th anniversary on Github.

Though only one new noteworthy feature has appeared in MMGen Wallet since
v13.3.0, users can benefit from numerous bugfixes, code cleanups, and
installation and testing improvements, along with updated coin daemon support.
Upgrading is therefore highly recommended:

    $ pip3 install --upgrade mmgen-wallet

Note that the code repository and package have been renamed to `mmgen-wallet`
while the package toplevel currently remains `mmgen`.

#### Notable new feature:

 - b51868a5: support multiple loaded coin daemon wallets

#### Other important changes:

 - 159e1c8a, 5eb3eb84: build dynamically linked secp256k1 extension module
 - 11b131fd, 01783f63: Pylint integration, Github workflows

#### Minor changes and additions:

 - 7135744d: use `pycryptodomex` instead of `pysha3` for `keccak_256` function
 - efb3a3ff: new script `examples/whitepaper.py`: extract the Bitcoin whitepaper
   from the blockchain

Python requirement: >= 3.8 (tested on 3.8, 3.9 and 3.11)

This release has been tested on the following platforms:

    Debian 11 (Bullseye) / x86_64
    Debian 12 (Bookworm) / x86_64
    Ubuntu 20.04 (Focal) / x86_64
    Ubuntu 22.04 (Jammy) / x86_64
    Arch Linux 2023-11-20 (Python 3.11) / x86_64
    ArchLinuxArm 2023-11-20 [userspace] (Python 3.11) / Rock Pi 4 (armv8)
    Debian 11 (Bullseye) [Armbian] / Rock Pi 4 (armv8)
    Debian 11 (Bullseye) [Armbian] / Orange Pi PC2 (armv8) [BTC + XMR autosign]
    Windows 10 Enterprise / MSYS2 2023-10-26 / x86_64 [qemu]

and with the following coin daemon versions:

    Bitcoin Core 25.1.0
    Bitcoin-Cash-Node 26.1.0
    Litecoin Core 0.21.2.2
    Monerod 0.18.3.1
    Go-Ethereum (Geth) 1.13.4
    Parity Ethereum 2.7.2

Solc v0.8.7 is required for ERC20 token contract creation

Altcoin address generation has been additionally tested using the following
reference tools:

    zcash-mini a2b3504 (https://github.com/FiloSottile/zcash-mini)
    pycoin-0.92.20230326 (https://github.com/richardkiss/pycoin)
    vanitygen-plusplus e7858035 (https://github.com/10gic/vanitygen-plusplus)
    monero-python 1.1.1 (https://github.com/monero-ecosystem/monero-python)
    ethkey (OpenEthereum 3.3.5)
