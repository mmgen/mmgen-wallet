### MMGen Wallet Version 14.1.0 Release Notes

#### Important new features:

 - 1c5c3319: offline transaction signing with automount for BTC, BCH, LTC and
             ETH/ERC20
 - c587ab39: support descriptor wallets for BTC
 - 92ab29a1: support use of alternate tracking wallet with `--tw-name`
 - ea1e8d12: `bip_hd`: a minimal, easy-to-use BIP-32/BIP-44 implementation

#### Other significant changes and features:

 - 6f0751b8: make transactions BIP-125 replace-by-fee by default
 - 21f43598: dieroll wallet: support `--seed-len` opt
 - 54d68ab3: tracking wallet view: ensure deterministic output of entries
 - 99e70578: mmgen-tool: new `decrypt_keystore` command
 - a9ea9ff5: mmgen-autosign: new `--seed-len` opt
 - 59e112ae: mmgen-autosign: new `wipe_key` operation
 - df7e8f0b: mmgen-autosign: new `xmr_setup` operation

#### New Monero features:

 - fc7e3c83: mmgen-xmrwallet: new `sweep_all` operation
 - f39da52b: mmgen-xmrwallet: support sweeping to specific account of wallet
 - 4c431500: mmgen-xmrwallet: support fee-prioritizing of transactions
 - 42a5821e: mmgen-xmrwallet: new `--rescan-spent` option
 - a5a24269: mmgen-xmrwallet submit, relay: display relay time
 - b6acf879: mmgen-xmrwallet: new `--skip-empty-accounts`,
             `--skip-empty-addresses` options
 - ea0f32e3: mmgen-xmrwallet list, listview: display per-address balances
 - 4f216ea9: mmgen-xmrwallet sync, list, view, listview: display addresses
             in truncated form (override with `--full-address`)
 - 0de5e47c: mmgen-xmrwallet: new `view` and `listview` operations

#### Security / bugfix:

 - a49aa2ba: keygen.py: forbid use of non-safe public key generation backends
 - 72a93dfc: proto.btc.tx: fix nLocktime functionality

Python requirement: >= 3.9 (tested on 3.9, 3.11 and 3.12)

This release has been tested on the following platforms:

    Debian 11 (Bullseye) / x86_64
    Debian 12 (Bookworm) / x86_64
    Ubuntu 22.04 (Jammy) / x86_64
    Ubuntu 24.04 (Noble) / x86_64
    Arch Linux 2024-07-08 (Python 3.12.4) / x86_64
    TBD ~~ArchLinuxArm 2024-XX-XX [userspace] (Python 3.11) / Rock Pi 4 (armv8)~~
    TBD ~~Debian 11 (Bullseye) [Armbian] / Rock Pi 4 (armv8)~~
    TBD ~~Debian 11 (Bullseye) [Armbian] / Orange Pi PC2 (armv8) [BTC + XMR autosign]~~
    Windows 10 Enterprise / MSYS2 2024-05-07 / x86_64 [qemu]

and with the following coin daemon versions:

    Bitcoin Core 27.1.0
    Bitcoin-Cash-Node 27.0.0
    Litecoin Core 0.21.3
    Monerod 0.18.3.3
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
