### MMGen Version 13.1.0 Release Notes

This release completes the process of modularizing the MMGen code base and
fully separating protocol-dependent from protocol-independent code.

In addition to improved reliability, maintainability and extensibility, this
major code overhaul has led to significant performance improvements and
reductions in memory usage.

#### Important new feature:

 - message signing: 86e3b273, e5cf3b6ec, 25efac31b, 770b209af, a81ff33f0

#### Other changes/additions/improvements (most recent first):

 - add pure-Python RIPEMD-160 code and wrapper routine: 40d90b37
 - mmgen-tool: add `extract_key_from_geth_wallet` command: 096f363d
 - mmgen-tool: add `eth_checksummed_addr` command: aecc03e2
 - crypto.py: improve user entropy implementation: 589c3780
 - rewrite public key and address generation code: 32c522c0
 - rewrite test/gentest.py utility: b43d827b

#### Important bugfixes:

 - RPC: disable `*_PROXY` environment vars for `requests` backend: ba2cc40d
 - mmgen-tool pubhex2addr: fix incorrect output for ETH, XMR and ZEC-Z
   protocols: af65676d
 - mmgen-tool addr2pubhash: reject non-PKH addresses: 4e3b11a3
 - mmgen-passchg: improve secure wallet deletion logic: 9e3d8d92

Python requirements: >= 3.7 (3.7, 3.8, 3.9, 3.10 tested)

This release has been tested on the following platforms:

        Debian 10 (Buster) / x86_64
        Debian 11 (Bullseye) / x86_64
        Ubuntu 20.04 (Focal) / x86_64
        Ubuntu 22.04 (Jammy) / x86_64
        Arch Linux / x86_64
        Arch Linux [userspace] / Rock Pi 4 (armv8)
        Debian 10 (Buster) [Armbian] / Rock Pi 4 (armv8)
        Debian 11 (Bullseye) [Armbian] / Orange Pi PC2 (armv8) [BTC-only]
        Windows 10 Enterprise [MSYS2-2022.02.15] / x86_64 [qemu]

and with the following coin daemon versions:

        Bitcoin Core 23.0.0
        Bitcoin-Cash-Node 24.0.0
        Litecoin Core 0.18.1
        Monerod 0.17.3.0
        Parity Ethereum 2.7.2
        Go-Ethereum (Geth) 1.10.14 (1.10.17 works but has geth init issues)
        OpenEthereum 3.3.5
        Erigon v2022.05.02 [14557a234] (partial testing, eth_call() issues with devnet)

Solc v0.8.7 is required for ERC20 token contract creation

Altcoin address generation has been additionally tested using the following
reference tools:

        zcash-mini a2b3504 (https://github.com/FiloSottile/zcash-mini)
        pycoin 0.92.20220213 (https://github.com/richardkiss/pycoin)
        vanitygen-plusplus e7858035 (https://github.com/10gic/vanitygen-plusplus)
        MoneroPy 98e7feb (https://github.com/bigreddmachine/MoneroPy)
        ethkey (OpenEthereum 3.3.5)
