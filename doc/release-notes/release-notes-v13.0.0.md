### MMGen Version 13.0.0 Release Notes

#### Important new features:

 - [XMR]: New 'mmgen-xmrwallet' interactive command: create and sync wallets,
   create and relay transactions (optionally via Tor proxy), support offline
   TX signing: 3d8ee62, cb98afd
 - [ETH]: Support Geth: ac7bced
 - Support multiple daemons per coin: dfc732a

#### Other changes/additions/improvements (most recent first):

 - Deterministic testing: 8e739e7, 08fc25d
 - Run test scripts from overlay tree: 96a250b
 - [ETH]: Support Erigon (WIP): 877be3f, b88c4bb
 - Migrate from distutils to setuptools, fully automate build and install
   process: 25fb862, 4a95714
 - Move data files to package directory: ea81d46
 - [ETH]: Support ETC via Parity (v2.7.2): 1575b30
 - Daemon version checking: a4eee3e

#### Important bugfixes:

 - mmgen-txsign: Support all address types with flat keylist: f64be2b

Python requirements: >= 3.7 (3.7, 3.8, 3.9 tested)

This release has been tested on the following platforms:

        Debian 10 (Buster) / x86_64
        Debian 11 (Bullseye) / x86_64
        Ubuntu 20.04 (Focal) / x86_64
        Arch Linux / x86_64
        Debian 10 (Buster) [Armbian] / Rock Pi 4 (armv8) (no Parity or OE)
        Windows 10 Enterprise [MSYS2] / qemu-x86_64

and with the following coin daemon versions:

        Bitcoin Core 22.0.0
        Bitcoin-Cash-Node 23.1.0
        Litecoin Core 0.18.1
        Monerod 0.17.2.3
        Parity Ethereum 2.7.2
        Go-Ethereum (Geth) 1.10.9
        OpenEthereum 3.3.0
        Erigon 2021.09.5-alpha [0976b9e45] (WIP, partial testing)

Solc v0.8.7 is required for ERC20 token contract creation

Altcoin address generation has been additionally tested using the following
reference tools:

        zcash-mini a2b3504 (https://github.com/FiloSottile/zcash-mini)
        pycoin 021907c (https://github.com/richardkiss/pycoin)
        vanitygen-plus 2212312 (https://github.com/exploitagency/vanitygen-plus)
        MoneroPy 98e7feb (https://github.com/bigreddmachine/MoneroPy)
        ethkey (OpenEthereum 3.3.0)
