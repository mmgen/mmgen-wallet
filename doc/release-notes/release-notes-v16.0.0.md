### MMGen Wallet Version 16.0.0 Release Notes

Version 16.0.0 brings THORChain swaps to MMGen Wallet, along with some other
major new features, other significant features and improvements, and the usual
bugfixes and code cleanups.  Users are highly encouraged to upgrade.

#### Major new features:

 - Swap support for 21 assets via THORChain (ff28d39a3, 85cec5655)
 - RUNE transaction and swap support (ec84abc90, ef76cf646)
 - Nix/NixOS support (d69fee71c, abbc9c843, 84b0843be)
 - Rust Ethereum (Reth) support (1e422b2c2, 5269b5efc)
 - Ethereum transaction sending via Etherscan (1eb0de793)
 - BCH cashaddr support (8edc7da5a, 3c726f909)
 - OP_RETURN data support (8fd463ecf, 6620b4dba)

#### Other significant features and improvements:

 - autosign: support signing TXs with non-MMGen inputs (b12fd879b)
 - txcreate: support sub-Satoshi fees (1cab2f9d6)
 - txbump: support new outputs in the replacement transaction (ef5f6e4b2)
 - txsend: new `--receipt` (ff9a1e08d) and `--test` (1f166ce45) options
 - txsend: new `--dump-hex` and `--mark-sent` options (6967456f8)
 - new `mmgen-cli` utility for communication with coin daemons (94bee46cb)
 - contextual command options (037c6bfb6)
 - contextual usage screens (4eb7c6456)
 - coin-specific and protocol-specific configuration options (f8a312e40)
 - negated command-line options (df3559d42)
 - LED signaling support for:
   - Radxa Rock 5 (b4898b9ae);
   - Banana Pi F3 (b4898b9ae);
   - Orange Pi 5 (3bcbde514); and
   - Nano Pi M6 (98c84a4a3)
 - new JSON transaction file format (4ffe5c48d)

#### Security-related changes:

 - Ethereum transaction signing with libsecp256k1 (60ca7a291)
 - secp256k1 extension mod: randomize context for enhanced protection against
   side-channel leakage (fbeda2f07)
 - mmgen-txcreate: prompt user if change address is not wallet address
   (6df695024)

#### Testing:

 - migrate from Pylint to Ruff (783b05e37, 487678bce)

Python requirement: >= 3.9 (tested on 3.9, 3.11, 3.12 and 3.13)

This release has been tested on the following platforms:

    NixOS 25.05 / x86_64
    Debian 13 (Trixie) / x86_64
    Debian 12 (Bookworm) / x86_64
    Debian 11 (Bullseye) / x86_64
    Ubuntu 25.04 (Plucky) / x86_64
    Ubuntu 24.04 (Noble) / x86_64
    Arch Linux 2025-09-09 (Python 3.13.7) / x86_64
    Armbian Debian 13 (Trixie) / Radxa Rock 5B [arm64]
    Armbian Debian 13 (Trixie) / Nano Pi M6 [arm64]
    Armbian Ubuntu 24.04 (Noble) / Banana Pi F3 [riscv64] (no Reth)
    Armbian Ubuntu 24.04 (Noble) / Orange Pi 5B [arm64]
    Windows 11 Enterprise / MSYS2 2025-08-30 / x86_64 [qemu]
    macOS 13.7.6 (Ventura) / Homebrew 4.6.10 (Python 3.13.7, Bash 5.3.3) / x86_64 [qemu]

and with the following coin daemon versions:

    Bitcoin Core 29.1.0
    Bitcoin-Cash-Node 28.0.1
    Litecoin Core 0.21.4
    Monerod 0.18.4.2
    Go-Ethereum (Geth) 1.16.3
    Rust Ethereum (Reth) 1.7.0
    Parity Ethereum 2.7.2

Solc 0.8.26 or newer is required for ERC20 token contract creation

Coin address generation has been additionally tested using the following
reference tools:

    pycoin-0.92.20241201 (https://github.com/richardkiss/pycoin)
    monero-python 1.1.1 (https://github.com/monero-ecosystem/monero-python)
    zcash-mini a2b3504 (https://github.com/FiloSottile/zcash-mini)
    vanitygen-plusplus e7858035 (https://github.com/10gic/vanitygen-plusplus)
    eth-keys 0.7.0 (https://github.com/ethereum/eth-keys)
    ethkey (OpenEthereum 3.1.0)
