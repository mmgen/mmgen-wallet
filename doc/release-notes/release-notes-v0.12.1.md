### MMGen Version 0.12.1 Release Notes

In addition to some new features, this release includes many changes “under the
hood” that make the MMGen code base harder, more modular, and more extensible.

#### Significant new features:

 - asyncio/aiohttp support: f9a483f3
 - txcreate,twview,listaddresses: display exact transaction date: b671453c
 - mnemonic entry modes: 04add0df

#### Significant code changes:

 - data objects: always raise exception on failure: 0852321c
 - new Lockable class: lock global vars after initialization: 4c2410e0
 - eliminate global vars g.proto, g.coin, g.rpc and others: c3f185e8
 - rewritten transaction classes: c3f185e8
 - new LEDControl class: 5ba2f51e
 - rewritten terminal code: d8e1d5f8

This release has been tested on the following platforms:

        Debian Buster / x86_64
        Ubuntu Focal / x86_64
        Armbian Bionic / Rock Pi 4 (armv8)
        Armbian Bionic / Orange Pi PC2 (armv8)
        Raspbian Buster / Raspberry Pi B (armv7) (BTC only)
        Windows 10 Enterprise Eng. / MSYS2 / qemu-x86_64

and with the following coin daemon versions:

        Bitcoin Core 0.20.0
        Bitcoin-ABC 0.21.8
        Litecoin Core 0.18.1
        Monerod 0.16.0.0
        OpenEthereum 3.0.1

Python version 3.6 or greater is required.

Altcoin address generation has been additionally tested using the following
tools as references:

        zcash-mini a2b35042 (https://github.com/FiloSottile/zcash-mini)
        pycoin 11f60a7c (https://github.com/richardkiss/pycoin)
        vanitygen-plus 22123128 (https://github.com/exploitagency/vanitygen-plus)
        MoneroPy 98e7feb2 (https://github.com/bigreddmachine/MoneroPy)
        ethkey 2.7.2 (https://github.com/paritytech/parity-ethereum)
