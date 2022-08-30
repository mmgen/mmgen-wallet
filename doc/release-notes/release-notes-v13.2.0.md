### MMGen Version 13.2.0 Release Notes

This release introduces three important new features: 1) transaction history
via `mmgen-tool txhist`, an invaluable aid in helping you to choose which
outputs to spend; 2) tracking wallet export/import to JSON; and 3) fast
blockchain rescanning during address import and elsewhere.

#### Important new features:

 - transaction history: 7d216564
 - import/export tracking wallets to JSON: 0514ec24
 - fast blockchain rescanning via `scantxoutset`: c96833c5, 5488c513, e7ac7fd2

 - new `mmgen-tool` commands:
   + `txhist`: 7d216564
   + `twimport`: 0514ec24
   + `twexport`: 0514ec24
   + `resolve_address`: cd2e2240
   + `rescan_blockchain`: c96833c5
   + `rescan_address`: 5488c513

 - new `mmgen-xmrwallet` operations:
   + `new`: 34f30fbf
   + `list`: b0d1a794

#### New testing feature:

 - command subgroups: 170a9ead

#### Important workaround:

 - localhost resolution workaround for MSWin/MSYS2 (may speed up RPC
   performance for all backends on some systems): 8cbdab9d

Python requirements: >= 3.7 (3.7, 3.8, 3.9, 3.10 tested)

This release has been tested on the following platforms:

        Debian 10 (Buster) / x86_64
        Debian 11 (Bullseye) / x86_64
        Ubuntu 20.04 (Focal) / x86_64
        Ubuntu 22.04 (Jammy) / x86_64
        Arch Linux / x86_64
        ArchLinuxArm [userspace] / Rock Pi 4 (armv8)
        Debian 11 (Bullseye) [Armbian] / Rock Pi 4 (armv8)
        Debian 11 (Bullseye) [Armbian] / Orange Pi PC2 (armv8) [BTC-only]
        Windows 10 Enterprise / MSYS2 2022.06.03 / x86_64 [qemu]

and with the following coin daemon versions:

        Bitcoin Core 23.0.0
        Bitcoin-Cash-Node 24.1.0
        Litecoin Core 0.21.2.1
        Monerod 0.18.1.0
        Go-Ethereum (Geth) 1.10.21
        OpenEthereum 3.3.5
        Parity Ethereum 2.7.2
        Erigon v2022.05.02 [14557a234] (no token operations, eth_call() issues with devnet)

Solc v0.8.7 is required for ERC20 token contract creation

Altcoin address generation has been additionally tested using the following
reference tools:

        zcash-mini a2b3504 (https://github.com/FiloSottile/zcash-mini)
        pycoin 0.92.20220529 (https://github.com/richardkiss/pycoin)
        vanitygen-plusplus e7858035 (https://github.com/10gic/vanitygen-plusplus)
        MoneroPy 98e7feb (https://github.com/bigreddmachine/MoneroPy)
        ethkey (OpenEthereum 3.3.5)
