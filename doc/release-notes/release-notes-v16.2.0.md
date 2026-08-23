### MMGen Wallet Version 16.2.0 Release Notes

This version of MMGen Wallet introduces Nostr key/address generation support,
reenables THORChain swaps halted after the May 2026 network hack incident, and
adds support for free-threaded Python.

In addition, it contains an important error-handling fix in the secp256k1
extension module, numerous fixes and cleanups throughout the codebase, and
improved code checking with static analysis tools.  All users are advised
to upgrade.

#### Important new feature:

 - e322b433 Nostr key/address generation

#### Other features and improvements:

 - a09a6c6b reenable THORChain swaps and RUNE transacting after May 2026 hack
 - efe3cd22, 7ca24493, 86ac4e84 support free-threaded Python

#### Bugfix:

 - 93938d4f secp256k1 extmod: handle context init failure correctly

#### Security & code analysis:

 - 7d89ab19 move `ecdsa` and `pexpect` package dependencies to test suite
 - 66fc415a, 158c5919 add Bandit static security checker to CI pipeline
 - b4044c9a, bb4aaf8a re-enable Pylint static analyzer in CI pipeline
 - 05b297ef secp256k1 extmod: compile with `-Wextra` and static analyzer enabled

Python requirement: >= 3.11 (tested on 3.11, 3.12, 3.13, 3.14 and 3.15)

This release has been tested on the following platforms:

    NixOS 26.05 / x86_64
    Arch Linux 2026-08-18 [Python 3.14.7] / x86_64
    Debian 14 (Forky) [Python 3.14.6] / x86_64
    Debian 13 (Trixie) [Python 3.13.5/ x86_64 (+)
    Debian 13 (Trixie) [Python 3.14.7 free-threaded] / x86_64 (++)
    Debian 13 (Trixie) [Python 3.15.0rc1 free-threaded] / x86_64 (++)
    Ubuntu 26.04 (Resolute) [Python 3.14.4] / x86_64
    Ubuntu 24.04 (Noble) [Python 3.12.3] / x86_64
    Radxa Debian 12 (Bookworm) [Python 3.11.2] / Radxa Rock 5B [arm64] (*, **)
    Armbian Debian 13 (Trixie) / Nano Pi M6 [arm64] (**, +)
    Armbian Debian 13 (Trixie) / Banana Pi F3 [riscv64] (***, +, +++)
    Windows 11 Enterprise / MSYS2 2026-06-11 (Python 3.14.7) / x86_64 [qemu] (no Reth)
    macOS 13.7.6 (Ventura) / Homebrew 6.0.18 (Python 3.14.5, Bash 5.3.9) / x86_64 [qemu]

    Notes:
    *   Reth unsupported, newer libc required
    **  arm64: aiohttp RPC backend fails with Reth
    *** riscv64: Reth builds without issue but fails to start:
        failed to open the database: Cannot allocate memory (12)
        Location: crates/storage/db/src/mdbx.rs:96:8
	+   The Debian Trixie Python interpreter (v3.13.5) crashes on exit after
		executing scripts that write signed transactions (`mmgen-txsign` and
		`mmgen-txsend`) for certain tests in the test suite.  This bug is
		unlikely to be observed under normal usage and in any case won’t prevent
        users from signing and sending transactions.  Nonetheless, users running
        Debian Trixie may wish to compile Python from source just to be safe and
        use the locally compiled Python to run MMGen Wallet. For instructions on
        how to do this, see the [**Build Python from Source**][ip] wiki page.
    ++  Readline text insertion is not currently supported under free-threaded
        Python.  Label-editing functionality will be sub-optimal.
    +++ BCH and ETH untested due to lack of prebuilt binaries for RISC-V.

and with the following coin daemon versions:

    Bitcoin Core 31.1
    Bitcoin Cash Node 29.1
    Litecoin Core 0.21.5.6
    Monerod 0.18.5.1
    Go Ethereum (Geth) 1.17.5
    Rust Ethereum (Reth) 2.5.1 (2.2.0 on macOS, 2.3.0 on NixOS)
    Parity Ethereum 2.7.2

Solc 0.8.26 or newer is required for ERC20 token contract creation

Coin address generation has been additionally tested using the following
reference tools:

    pycoin 0.92718.20260405 (https://github.com/richardkiss/pycoin)
    monero-python 1.1.1 (https://github.com/monero-ecosystem/monero-python)
    zcash-mini a2b3504 (https://github.com/FiloSottile/zcash-mini)
    vanitygen-plusplus e7858035 (https://github.com/10gic/vanitygen-plusplus)
    eth-keys 0.7.0 (https://github.com/ethereum/eth-keys)
    ethkey (OpenEthereum 3.1.0)

[ip]: ../wiki/Build-Python-from-Source
