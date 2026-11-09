### MMGen Wallet Version 17.0.0 Release Notes

This version of MMGen Wallet introduces THORChain memoless swaps and XMR swaps.
These features are enabled in the test suite only for now, but mainnet support
can easily be switched on when they go live on the THORChain network.

Most importantly for Monero users, this version introduces transaction data
integrity checking during the XMR signing process.  This critical security
upgrade ensures that the change address in the transaction belongs to your
wallet and that the amount shown is going to the destination shown, preventing
an attacker from stealing your funds in the event your online installation is
ever compromised.  These checks were always performed by the wallet for non-
privacy coins but were regrettably overlooked for Monero.  Monero users are
thus urgently advised to upgrade.

The release also includes some minor bugfixes, a new transaction versioning
system, more secure handling of legacy transaction files, and lots of code
cleanups suggested by static analyzers, so an upgrade will benefit all users.

As an afterword to the Monero security fix, it must be mentioned that no system,
however secure, can do everything for the user. When sending funds to an outside
address, for example, the offline installation has no way of knowing whether the
destination and amount are what the user intended.  A good rule of thumb is to
always check the offline signing summary to ensure that the transaction type is
correct and, for transfers, that the address and amount are correct. This advice
applies to all coins, by the way, not just Monero.

#### Important new features:

 - ffe488ff, d9e24494, ff35b01c THORChain memoless swaps (testing only)
 - ea9c2d29 THORChain XMR swaps (testing only)
 - 2fe498b1 transaction integrity checking for XMR

#### Other features and improvements:

 - ef61dd10 XMR subaddress generation
 - f17416ca XMR compat: encapsulate legacy transaction data
 - 13623ed9 mmgen-swaptxcreate: add `--quote` option
 - 8a23f986 new `mmgen-remote` utility
 - 9666e687 XMR compat: support viewing of transaction files via `mmgen-tool`
 - 5e41407b XMR: change handling of default datadirs

#### Testing:

 - 75b881a6 keygen: move unsafe pubkey generation backends to test suite
 - b036207b remove test-related env vars from production code

#### Security:

 - 7e2aa808 transaction versioning
 - 33773ecf new `allow_legacy_tx_files` and `forbid_version_mismatched_tx_files` options
 - dd714815, 852cdeda tx.file: refuse to parse legacy TX files for signing ops
 - 256970f3 setup.py extmod: convert gcc warnings to errors

Python requirement: >= 3.11 (tested on 3.11, 3.12, 3.13, 3.14 and 3.15)

This release has been tested on the following platforms:

    NixOS 26.05 / x86_64
    Arch Linux 2026-11-06 [Python 3.14.9] / x86_64
    Debian 14 (Forky) [Python 3.14.6] / x86_64
    Debian 13 (Trixie) [Python 3.13.3] / x86_64 (+)
    Debian 12 (Bookworm) [Python 3.11.2] / x86_64
    Debian 13 (Trixie) [Python 3.15.2 free-threaded] / x86_64 (++)
    Ubuntu 26.04 (Resolute) [Python 3.14.4] / x86_64
    Ubuntu 24.04 (Noble) [Python 3.12.3] / x86_64
    Radxa Debian 12 (Bookworm) [Python 3.11.2] / Radxa Rock 5B [arm64] (*, **)
    Armbian Debian 13 (Trixie) / Nano Pi M6 [arm64] (**, +)
    Armbian Debian 13 (Trixie) / Banana Pi F3 [riscv64] (***, +, +++)
    Windows 11 Enterprise / MSYS2 2026-06-11 (Python 3.14.7) / x86_64 [qemu] (no Reth)
    macOS 13.7.6 (Ventura) / Homebrew 7.0.12 (Python 3.15.2, Bash 5.3.9) / x86_64 [qemu]

    Notes:

	* (see notes to previous release)

and with the following coin daemon versions:

    Bitcoin Core 31.1
    Bitcoin Cash Node 29.1
    Litecoin Core 0.21.5.6
    Monero CLI 0.18.5.4
    Go Ethereum (Geth) 1.17.5
    Rust Ethereum (Reth) 2.8.1 (2.2.0 on macOS, 2.3.0 on NixOS)
    Parity Ethereum 2.7.2

Solc 0.8.26 or newer is required for ERC20 token contract creation

Coin address generation has been additionally tested using the following
reference tools:

    * (see reference tools list to previous release)
