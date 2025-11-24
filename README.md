# MMGen Wallet

##### A terminal-based online/offline cryptocurrency wallet

![build](https://github.com/mmgen/mmgen-wallet/workflows/build/badge.svg)
![ruff](https://github.com/mmgen/mmgen-wallet/workflows/ruff/badge.svg)

### Description

MMGen Wallet is a wallet and cold storage solution for Bitcoin (and selected
altcoins) implemented as a suite of lightweight Python scripts.  The scripts
work in tandem with a reference Bitcoin or altcoin daemon running on both online
and offline computers to provide a robust solution for securely storing,
tracking, sending and receiving your crypto assets.

The online computer is used for tracking balances and creating and sending
transactions, while the offline machine (typically an air-gapped, low-power
device such as a Raspberry Pi) takes care of wallet creation, address generation
and transaction signing.  All operations involving secret data are handled
offline: **your seed and private keys never come into contact with a
network-connected device.**

MMGen Wallet is designed for reliability by having the reference Bitcoin or
altcoin daemon, rather than less-tested third-party software, do all the “heavy
lifting” of tracking and signing transactions.  It’s also designed with privacy
in mind: unlike most cryptocurrency wallets, MMGen Wallet is a completely
self-contained system that makes **no connections to the Internet** apart from
the coin network itself (RUNE transacting excepted): no information about which
addresses you’re tracking is ever leaked to the outside world.

Like all deterministic wallets, MMGen Wallet can generate a virtually unlimited
number of address/key pairs from a single seed.  Your wallet never changes, so
you need back it up only once.

At the heart of the MMGen system is the seed, the “master key” providing access
to all your crypto assets.  The seed can be stored in many different formats:
as a password-encrypted wallet (the default), as a one-line base58 or
hexadecimal seed file, as formatted “dieroll base6” data, as an Electrum-based
or BIP39 mnemonic seed phrase, as a brainwallet passphrase, or as “incognito
data” hideable within random data in a file or block device.  Conversion among
all formats is supported.

***mmgen-txcreate running in a terminal window***
![mmgen-txcreate running in a terminal window][9]

#### Simplified key derivation and seed-phrase generation

To deterministically derive its keys, MMGen Wallet uses a non-hierarchical
scheme differing from the BIP32 protocol on which most of today’s popular
wallets are based.  One advantage of this simple, hash-based scheme is that you
can easily [recover your private keys from your seed without the MMGen Wallet
software][K] using standard command-line utilities.

MMGen Wallet also differs from most cryptocurrency wallets today in its use of
the original 1626-word [Electrum wordlist][ew] for mnemonic seed phrases.  Seed
phrases are derived using ordinary base conversion, similarly allowing you to
regenerate your seed from your seed phrase without the MMGen Wallet software
should the need arise.  An example of how to do this at the Python prompt is
provided [here.][S]

The original Electrum wordlist was derived from a [frequency list][fl] of words
found in contemporary English poetry.  The high emotional impact of these words
makes seed phrases easy to memorize.  Curiously, only 861 of them are shared by
the more prosaic 2048-word [BIP39 wordlist][bw] used in most wallets today.

Beginning with version 0.12.0, the BIP39 mnemonic format is also supported,
allowing you to use MMGen Wallet as a master wallet for other wallets supporting
that widespread standard.

#### A brief overview of MMGen Wallet’s unique feature set:

- **[Transaction support][T]** for BTC, [BCH][bx], [LTC][bx], [ETH][E],
  [ETC][E], [ERC20 tokens][E] and [RUNE][rx].
- **[Monero][bm]** transacting and wallet management via the interactive
  [`mmgen-xmrwallet`][xm] command.
- **[Native asset swaps via THORChain][tc]** (21 assets currently supported).
- **[Address generation support][ag]** for the above coins, plus [Zcash][zx]
  (t and z addresses) and [144 Bitcoin-derived altcoins][ax].
- **Support for all Bitcoin address types** including Segwit-P2SH and Bech32.
- **Independent key derivation for each address type:** No two addresses ever
  share the same private key.  Certain wallets in wide use today regrettably
  fail to guarantee this property, leading to the danger of inadvertent key
  reuse.
- **Coin control:** You select the outputs your transaction will spend.  An
  essential requirement for maintaining anonymity.
- **[BIP69 transaction input and output ordering][69]** helps anonymize the
  “signature” of your transactions.
- **[Full control over transaction fees][M]:** Fees are specified as absolute or
  satoshi/byte amounts and can be adjusted interactively, letting you round fees
  to improve anonymity.  Network fee estimation (with selectable estimation
  mode), [RBF][R] and [fee bumping][B] are supported.
- **Support for nine wallet formats:** three encrypted (native wallet,
  brainwallet, incognito wallet) and six unencrypted (native mnemonic,
  **BIP39,** mmseed, hexseed, plain hex, dieroll).
- Interactive **dieroll wallet** generation via `mmgen-walletconv -i dieroll`.
- Support for new-style **Monero mnemonics** in `mmgen-tool` and `mmgen-passgen`.
- **[Subwallets][U]:** Subwallets have many applications, the most notable being
  online hot wallets, decoy wallets and travel wallets.  MMGen subwallets are
  functionally and externally identical to ordinary wallets, which provides a
  key security benefit: only the user who generated the subwallet knows that it
  is indeed a subwallet.  Subwallets don’t need to be backed up, as they can
  always be regenerated from their parent.
- **[XOR (N-of-N) seed splitting][O]** with shares exportable to all MMGen
  wallet formats.  The [master share][ms] feature allows you to create multiple
  splits with a single master share.
- **[Transaction autosigning][X]:** This feature puts your offline signing
  machine into “hands-off” mode, allowing you to transact directly from cold
  storage securely and conveniently.  Additional LED signaling support is
  provided for Raspbian and Armbian platforms.
- **[Password generation][G]:** MMGen Wallet can be used to generate and manage
  your online passwords.  Password lists are identified by arbitrarily chosen
  strings like “alice@github” or “bob@reddit”.  Passwords of different lengths
  and formats, including BIP39, are supported.
- **[Message signing][MS]** for BTC, BCH, LTC, ETH and ETC.  Signing for
  multiple addresses and autosigning are supported.
- **Selectable seed lengths** of 128, 192 or 256 bits.  Subwallets may have
  shorter seeds than their parent.
- **User-enhanced entropy:** All operations requiring random data will prompt
  you for additional entropy from the keyboard.  Keystroke timings are used in
  addition to the characters typed.
- **Wallet-free operation:** All wallet operations can be performed directly
  from your seed phrase at the prompt, allowing you to dispense with a
  physically stored wallet entirely if you wish.
- Word-completing **mnemonic entry modes** customized for each of MMGen Wallet’s
  supported wordlists minimize keystrokes required during seed phrase entry.
- **Stealth mnemonic entry:** This feature allows you to obfuscate your seed
  phrase with “dead” keystrokes to guard against acoustic side-channel attacks.
- **Network privacy:** MMGen Wallet never “calls home” or checks for upgrades
  over the network.  No information about your wallet installation or crypto
  assets is ever leaked to third parties.
- **Human-readable wallet files:** All of MMGen Wallet’s wallet formats, with
  the exception of incognito wallets, can be printed or copied by hand.
- **Terminal-based:** MMGen Wallet can be run in a screen or tmux session on
  your local network.
- **Scriptability:** Most of MMGen Wallet’s commands can be made
  non-interactive, allowing you to automate repetitive tasks using shell
  scripts.
- The project also includes the [`mmgen-tool`][L] utility, a handy “Swiss
  Army knife” for cryptocurrency developers, and [`mmgen-cli`][cl], for
  easy communication with the RPC interfaces of all supported coin daemons.

#### Supported platforms:

Linux, macOS, Windows/MSYS2

### [Download / Install / Use][D]

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

Homepage:
[Clearnet](https://mmgen-wallet.cc) |
[I2P](http://mmgen-wallet.i2p) |
[Onion](http://mmgen55rtcahqfp2hn3v7syqv2wqanks5oeezqg3ykwfkebmouzjxlad.onion)    
Code Repository:
[Clearnet](https://mmgen.org/project/mmgen/mmgen-wallet) |
[I2P](http://mmgen-wallet.i2p/project/mmgen/mmgen-wallet) |
[Onion](http://mmgen55rtcahqfp2hn3v7syqv2wqanks5oeezqg3ykwfkebmouzjxlad.onion/project/mmgen/mmgen-wallet)    
Code Repository Mirrors:
[Github](https://github.com/mmgen/mmgen-wallet) |
[Gitlab](https://gitlab.com/mmgen/mmgen-wallet) |
[Codeberg](https://codeberg.org/mmgen/mmgen-wallet)     
IRC:
**#mmgen-wallet** ([OFTC](https://oftc.net) | postman.i2p) &nbsp; | &nbsp;
E-Mail:
[Tuta](mailto:mmgen@tuta.io) |
[Proton](mailto:mmgen-wallet@proton.me)  
Accounts:
[Twitter](https://twitter.com/TheMMGenProject) |
[Bitcointalk](https://bitcointalk.org/index.php?topic=567069.new#new) |
[Dread](http://dreadytofatroptsdj6io7l3xptbet6onoyno2yv7jicoxknyazubrad.onion/u/MMGen) |
[Reddit](https://www.reddit.com/user/mmgen-py) |
[Keybase](https://keybase.io/mmgen)  
PGP Signing Key: [5C84 CB45 AEE2 250F 31A6 A570 3F8B 1861 E32B 7DA2][5]    
Donate:    
&nbsp;⊙&nbsp;BTC:&nbsp;*bc1qxmymxf8p5ckvlxkmkwgw8ap5t2xuaffmrpexap*    
&nbsp;⊙&nbsp;BCH:&nbsp;*15TLdmi5NYLdqmtCqczUs5pBPkJDXRs83w*    
&nbsp;⊙&nbsp;XMR:&nbsp;*8B14zb8wgLuKDdse5p8f3aKpFqRdB4i4xj83b7BHYABHMvHifWxiDXeKRELnaxL5FySfeRRS5girgUvgy8fQKsYMEzPUJ8h*

[D]:  ../../wiki
[5]:  ../../wiki/MMGen-Signing-Keys
[9]:  https://mmgen.org/images/rxvt-txcreate.jpg
[K]:  ../../wiki/Recovering-Your-Keys-Without-the-MMGen-Wallet-Software
[S]:  ../../wiki/Recovering-Your-Keys-Without-the-MMGen-Wallet-Software#a_mh
[W]:  https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki
[ew]: https://github.com/spesmilo/electrum/blob/1.9.5/lib/mnemonic.py
[bw]: https://github.com/bitcoin/bips/blob/master/bip-0039/english.txt
[fl]: https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/Contemporary_poetry
[U]:  ../../wiki/Subwallets
[X]:  ../../wiki/command-help-autosign
[xm]: ../../wiki/command-help-xmrwallet
[G]:  ../../wiki/command-help-passgen
[MS]: ../../wiki/command-help-msg
[cl]: ../../wiki/command-help-cli
[T]:  ../../wiki/Getting-Started-with-MMGen-Wallet#a_ct
[E]:  ../../wiki/Altcoin-and-Forkcoin-Support#a_tx
[ag]: ../../wiki/command-help-addrgen
[bx]: ../../wiki/Altcoin-and-Forkcoin-Support#a_bch
[bm]: ../../wiki/Altcoin-and-Forkcoin-Support#a_xmr
[rx]: ../../wiki/Altcoin-and-Forkcoin-Support#a_rune
[tc]: ../../wiki/Altcoin-and-Forkcoin-Support#a_tcswap
[zx]: ../../wiki/Altcoin-and-Forkcoin-Support#a_zec
[ax]: ../../wiki/Altcoin-and-Forkcoin-Support#a_kg
[M]:  ../../wiki/Getting-Started-with-MMGen-Wallet#a_fee
[R]:  ../../wiki/Getting-Started-with-MMGen-Wallet#a_rbf
[B]:  ../../wiki/command-help-txbump
[69]: https://github.com/bitcoin/bips/blob/master/bip-0069.mediawiki
[O]:  ../../wiki/XOR-Seed-Splitting:-Theory-and-Practice
[ms]: ../../wiki/command-help-seedsplit
[ta]: ../../wiki/Tool-API
[L]:  ../../wiki/command-help-tool
