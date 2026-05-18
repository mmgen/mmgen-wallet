### MMGen Wallet Version 16.1.0 Release Notes

This version of MMGen Wallet introduces XMR compatibility mode, which enables
transacting and tracking wallet operations for Monero using the same interface
as for other coins, thus unifying the user experience across all coins.

Compatibility mode is now the preferred way to transact Monero, replacing the
`mmgen-xmrwallet` script for most operations.

For details, see the XMR section of the Altcoin-and-Forkcoin-Support wiki page.

#### Major new feature:

 - XMR compatibility mode (d8439ba6, 4a4b8149, e69dfbe8, 907bdc2b, 7b53f433,
   cb99e13c, 1132d0ff, bdd7dd33)

#### Other features and improvements:

 - mmgen-txbump: support transaction selection (c4ec6271)
 - mmgen-txsend --status: support transaction ranges (48edcf41)
 - mmgen-txsend: support transaction selection with `--status` (4f1b16f4)
 - BTC: increase maximum OP_RETURN data size to 4096 bytes (81ece1ff)

#### Security, bugfix, cleanup:

 - aiohttp: restore use as context manager, remove version pin (a3e7c08f)
 - txbump: display outputs in correct (raw) order (e3799260)
 - decodeScriptPubKey(): parse nulldata correctly (4b55f115)
 - use hashlib for keccak-256 function on newer systems; eliminate dependency
   on pycryptodome package (20734cc7)
 - use hashlib for PBKDF2 function (263824b9)

Python requirement: >= 3.11 (tested on 3.11, 3.12, 3.13 and 3.14)

This release has been tested on the following platforms:

    NixOS 25.11 / x86_64
    Debian 13 (Trixie) / x86_64
    Debian 12 (Bookworm) / x86_64 (no Reth*)
    Ubuntu 26.04 (Resolute) / x86_64
    Ubuntu 24.04 (Noble) / x86_64
    Arch Linux 2026-05-16 (Python 3.14.5) / x86_64
    Armbian Debian 13 (Trixie) / Radxa Rock 5B [arm64] (Reth issue**)
    Armbian Debian 13 (Trixie) / Nano Pi M6 [arm64] (Reth issue**)
    Armbian Ubuntu 24.04 (Noble) / Banana Pi F3 [riscv64] (no Reth***)
    Windows 11 Enterprise / MSYS2 2026-03-22 (Python 3.14.5) / x86_64 [qemu]
    macOS 13.7.6 (Ventura) / Homebrew 5.1.11 (Python 3.14.5, Bash 5.3.9) / x86_64 [qemu]

	Notes:
	*   Reth requires newer libc
	**  arm64: aiohttp RPC backend fails with Reth
	*** riscv64: Reth builds without issue but fails to start:
		failed to open the database: Cannot allocate memory (12)
		Location: crates/storage/db/src/mdbx.rs:96:8

and with the following coin daemon versions:

    Bitcoin Core 31.0.0
    Bitcoin Cash Node 29.0.0
    Litecoin Core 0.21.5.5
    Monerod 0.18.5.0
    Go Ethereum (Geth) 1.17.4
    Rust Ethereum (Reth) 2.2.0
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
