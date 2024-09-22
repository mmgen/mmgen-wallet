### MMGen Wallet Version 15.0.0 Release Notes

This release brings full macOS support to MMGen Wallet, along with a new
security feature and the usual code cleanups and testing improvements.

#### Important new features:

 - macOS support (bcff2e4f, a24eed08, 91991a13, d5939ef0, 19bc4af9)
 - disable swap on offline signing device (4483b0fb)

Python requirement: >= 3.9 (tested on 3.9, 3.11 and 3.12)

This release has been tested on the following platforms:

    Debian 11 (Bullseye) / x86_64
    Debian 12 (Bookworm) / x86_64
    Ubuntu 22.04 (Jammy) / x86_64
    Ubuntu 24.04 (Noble) / x86_64
    Arch Linux 2024-09-01 (Python 3.12.5) / x86_64
    Armbian Debian 11 (Bullseye) / Orange Pi PC2 [arm64] (offline signing)
    Armbian Ubuntu 24.04 (Noble) / Rock Pi 4 [arm64]
    Windows 11 Enterprise / MSYS2 2024-05-07 / x86_64 [qemu]
    macOS 13.7.6 (Ventura) / Homebrew 4.3.18 (Python 3.12.5, Bash 5.2.32) / x86_64 [qemu]

and with the following coin daemon versions:

    Bitcoin Core 27.1.0
    Bitcoin-Cash-Node 27.1.0
    Litecoin Core 0.21.3
    Monerod 0.18.3.4
    Go-Ethereum (Geth) 1.13.15
    Parity Ethereum 2.7.2

Solc v0.8.26 or newer is required for ERC20 token contract creation

Altcoin address generation has been additionally tested using the following
reference tools:

    zcash-mini a2b3504 (https://github.com/FiloSottile/zcash-mini)
    pycoin-0.92.20230326 (https://github.com/richardkiss/pycoin)
    vanitygen-plusplus e7858035 (https://github.com/10gic/vanitygen-plusplus)
    monero-python 1.1.1 (https://github.com/monero-ecosystem/monero-python)
    ethkey (OpenEthereum 3.3.5)
