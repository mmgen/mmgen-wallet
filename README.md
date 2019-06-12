***Note: This is the source code repository of the MMGen wallet system.  For an
easier way to install MMGen, check out the prebuilt bootable USB images on the
[MMGenLive][8] home page.***

# MMGen = Multi-Mode GENerator

##### a Bitcoin and altcoin online/offline software wallet for the command line

### Description

MMGen is a wallet and cold storage solution for Bitcoin (and selected altcoins)
implemented as a suite of lightweight Python scripts.  The scripts work in
tandem with a reference Bitcoin or altcoin daemon running on both online and
offline computers to provide a robust solution for securely storing, tracking,
sending and receiving your crypto assets.

The online computer is used for tracking balances and creating and sending
transactions, while the offline computer (typically an air-gapped, low-power
device such as a Raspberry Pi) takes care of wallet creation, address generation
and transaction signing.  All operations involving secret data are handled
offline: **your seed and private keys never come into contact with a
network-connected device.**

MMGen is designed for reliability by having the reference Bitcoin or altcoin
daemon, rather than less-tested third-party software, do all the “heavy lifting”
of tracking and signing transactions.  It’s also designed with privacy in mind:
unlike some other online/offline wallets, MMGen is a completely self-contained
system that makes **no connections to the Internet** apart from the coin network
itself: no information about which addresses you’re tracking is ever leaked to
the outside world.

Like all deterministic wallets, MMGen can generate a virtually unlimited number
of address/key pairs from a single seed.  Your wallet never changes, so you need
back it up only once.

At the heart of the MMGen system is the seed, the “master key” providing access
to all your crypto assets.  The seed can be stored in five different ways:

  1. as a password-encrypted wallet.  The crack-resistant Scrypt hash function
	 is used for password hashing.  Scrypt’s parameters can be tuned to make
	 your wallet’s password very difficult to crack should it fall into the
	 wrong hands.  The wallet is a compact, six-line text file suitable for
	 printing or even writing out by hand;

  2. as a seed file: a one-line, conveniently formatted base-58 representation
	 of your unencrypted seed plus a checksum;

  3. as an Electrum-like mnemonic seed phrase of 12, 18 or 24 words;

  4. as a brainwallet passphrase (this option is recommended only for users who
	 understand the risks of brainwallets and know how to create a strong
	 brainwallet passphrase).  The brainwallet is hashed using Scrypt with
	 tunable parameters, making it much harder to crack than standard SHA256
	 brainwallets; or

  5. as “incognito data”, a wallet encrypted to make it indistinguishable
	 from random data.  This data can be hidden on a disk partition filled with
	 random data, or in a file at an offset of your choice.  This makes it
	 possible to hide a wallet at a non-private location—on cloud storage, for
	 example.  Incognito wallet hiding/retrieval is seamlessly integrated into
	 MMGen, making its use nearly as easy as that of the standard wallet.

The best part is that all these methods can be combined.  If you forget your
mnemonic seed phrase, for example, you can regenerate it from a stored wallet
or seed file.  Correspondingly, a lost wallet can be regenerated from a mnemonic
or seed or vice-versa.

***mmgen-txcreate running in a terminal window***
![mmgen-txcreate running in a terminal window][9]

#### Simplified key derivation and seed-phrase generation

To deterministically derive its keys, MMGen uses a non-hierarchical scheme
differing from the BIP32 protocol on which most of today’s popular wallets are
based.  One advantage of this simple, hash-based scheme is that you can easily
[recover your private keys from your seed without the MMGen program itself][K]
using standard command-line utilities.

MMGen also differs from most cryptocurrency wallets today in its use of the
original 1626-word [Electrum wordlist][ew] for mnemonic seed phrases.  Seed
phrases are derived using ordinary base conversion, similarly allowing you to
regenerate your seed from your seed phrase without MMGen program itself, should
the need arise.  An example of how to do this at the Python prompt is provided
[here.][S]

The original Electrum wordlist was derived from a [frequency list][fl] of words
found in contemporary English poetry.  The high emotional impact of these words
makes seed phrases easy to memorize.  Curiously, only 861 of them are shared by
the more prosaic 2048-word [BIP39 wordlist][bw] used in most wallets today.

#### A brief overview of MMGen’s unique feature set:

- **[Full transaction and address tracking support][T]** for Bitcoin, [Bcash][bx],
  [Litecoin][bx], [Ethereum][E], Ethereum Classic and [ERC20 tokens][E].
- **[Address generation support][ag]** for the above coins, plus [Monero][mx],
  [Zcash][zx] (t and z addresses) and [144 Bitcoin-derived altcoins][ax].
- **Support for all Bitcoin address types** including segwit-p2sh and bech32.
- **Independent key derivation for each address type:** No two addresses ever
  share the same private key.  Certain wallets in wide use today regrettably
  fail to guarantee this property, leading to the danger of inadvertent key
  reuse.
- **Coin control:** You select the outputs your transaction will spend.  An
  essential requirement for maintaining anonymity.
- **[BIP69 transaction input and output ordering][69]** helps anonymize the
  “signature” of your transactions.
- **[Full control over transaction fees][M]:** Fees are specified as absolute or
  sat/byte amounts and can be adjusted interactively, letting you round fees to
  improve anonymity.  Network fee estimation is available. [RBF][R] and [fee
  bumping][B] are supported.
- **Support for six wallet formats:** three encrypted (native wallet,
  brainwallet, incognito wallet) and three unencrypted (mnemonic, mmseed,
  hexseed).
- **[Subwallets][U]:** Subwallets have many applications, the most notable being
  online hot wallets, decoy wallets and travel wallets.  MMGen subwallets are
  functionally and externally identical to ordinary wallets, which provides a
  key security benefit: only the user who generated the subwallet knows that it
  is indeed a subwallet.  Subwallets don’t need to be backed up, as they can
  always be regenerated from their parent.
- **[Transaction autosigning][X]:** This feature puts your offline signing
  machine into “hands-off” mode, allowing you to transact directly from cold
  storage securely and conveniently.  Additional LED signaling support is
  provided for RPi and Armbian-based boards.
- **[Password generation][G]:** MMGen can be used to generate and manage your
  online passwords.  Passwords are identified by arbitrarily chosen strings like
  “alice@github” or “bob@reddit”.
- **Selectable seed lengths** of 128, 192 or 256 bits.  Subwallets may have
  shorter seeds than their parent.
- **User-enhanced entropy:** All operations requiring random data will prompt
  you for additional entropy from the keyboard.  Keystroke timings are used in
  addition to the characters typed.
- **Wallet-free operation:** All wallet operations can be performed directly
  from your seed phrase at the prompt, allowing you to dispense with a
  physically stored wallet entirely if you wish.
- **Stealth mnemonic entry:** To guard against acoustic side-channel attacks,
  you can obfuscate your seed phrase with “dead” keystrokes as you enter it from
  the keyboard.
- **Network privacy:** MMGen never “calls home” or checks for upgrades over the
  network.  No information about your wallet installation or crypto assets is
  ever leaked to third parties.
- **Human-readable wallet files:** All of MMGen’s wallet formats, with the
  exception of incognito wallets, can be printed or copied by hand.
- **Terminal-based:** MMGen can be run in a screen or tmux session on your local
  network.
- **Scriptability:** Most MMGen commands can be made non-interactive, allowing
  you to automate repetitive tasks using shell scripts.  Most of the
  `mmgen-tool` utility’s commands can be piped.

### Download/Install

> #### [Install a prebuilt bootable image (MMGenLive) on a USB stick][8]

> #### [Install from source on Microsoft Windows][1]

> #### [Install from source on Debian, Ubuntu, Raspbian or Armbian Linux][2]


### Using MMGen

> #### [Getting Started with MMGen][3]

> #### [MMGen Quick Start with Regtest Mode][Q]

> #### [MMGen command help][6]

> #### [Recovering your keys without the MMGen software][K]

> #### [Altcoin and Forkcoin support (ETH,ETC,XMR,ZEC,LTC,BCH and 144 Bitcoin-derived alts)][F]

> #### [Subwallets][U]

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

[**Forum**][4] |
[Reddit][0] |
[PGP Public Keys][5] |
Donate (BTC,BCH): 15TLdmi5NYLdqmtCqczUs5pBPkJDXRs83w

[0]: https://www.reddit.com/user/mmgen-py
[1]: https://github.com/mmgen/mmgen/wiki/Install-MMGen-on-Microsoft-Windows
[2]: https://github.com/mmgen/mmgen/wiki/Install-MMGen-on-Debian-or-Ubuntu-Linux
[3]: https://github.com/mmgen/mmgen/wiki/Getting-Started-with-MMGen
[4]: https://bitcointalk.org/index.php?topic=567069.0
[5]: https://github.com/mmgen/mmgen/wiki/MMGen-Signing-Keys
[6]: https://github.com/mmgen/mmgen/wiki/MMGen-command-help
[7]: http://bitcoinmagazine.com/8396/deterministic-wallets-advantages-flaw/
[8]: https://github.com/mmgen/MMGenLive
[9]: https://cloud.githubusercontent.com/assets/6071028/20677261/6ccab1bc-b58a-11e6-8ab6-094f88befef2.jpg
[Q]: https://github.com/mmgen/mmgen/wiki/MMGen-Quick-Start-with-Regtest-Mode
[K]: https://github.com/mmgen/mmgen/wiki/Recovering-Your-Keys-Without-the-MMGen-Software
[S]: https://github.com/mmgen/mmgen/wiki/Recovering-Your-Keys-Without-the-MMGen-Software#a_mh
[F]: https://github.com/mmgen/mmgen/wiki/Altcoin-and-Forkcoin-Support
[W]: https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki
[ew]: https://github.com/spesmilo/electrum/blob/1.9.5/lib/mnemonic.py
[bw]: https://github.com/bitcoin/bips/blob/master/bip-0039/english.txt
[fl]: https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/Contemporary_poetry
[U]: https://github.com/mmgen/mmgen/wiki/Subwallets
[X]: https://github.com/mmgen/mmgen/wiki/autosign-[MMGen-command-help]
[G]: https://github.com/mmgen/mmgen/wiki/passgen-[MMGen-command-help]
[T]: https://github.com/mmgen/mmgen/wiki/Getting-Started-with-MMGen#a_ct
[E]: https://github.com/mmgen/mmgen/wiki/Altcoin-and-Forkcoin-Support#a_tx
[ag]: https://github.com/mmgen/mmgen/wiki/addrgen-[MMGen-command-help]
[bx]: https://github.com/mmgen/mmgen/wiki/Altcoin-and-Forkcoin-Support#a_bch
[mx]: https://github.com/mmgen/mmgen/wiki/Altcoin-and-Forkcoin-Support#a_xmr
[zx]: https://github.com/mmgen/mmgen/wiki/Altcoin-and-Forkcoin-Support#a_zec
[ax]: https://github.com/mmgen/mmgen/wiki/Altcoin-and-Forkcoin-Support#a_kg
[M]: https://github.com/mmgen/mmgen/wiki/Getting-Started-with-MMGen#a_fee
[R]: https://github.com/mmgen/mmgen/wiki/Getting-Started-with-MMGen#a_rbf
[B]: https://github.com/mmgen/mmgen/wiki/txbump-[MMGen-command-help]
[69]: https://github.com/bitcoin/bips/blob/master/bip-0069.mediawiki
