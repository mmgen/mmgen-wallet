***Note: This is the source code repository of the MMGen wallet system.  For an
easier way to install MMGen, check out the prebuilt bootable USB images on the
[MMGenLive][8] home page.***

# MMGen = Multi-Mode GENerator

##### a Bitcoin and altcoin online/offline software wallet for the command line

### Description

MMGen is a wallet and cold storage solution for Bitcoin (and selected altcoins)
implemented as a suite of lightweight Python scripts.  The scripts work in
tandem with a reference Bitcoin Core daemon (or altcoin daemon) running on both
an online and offline computer to provide a robust solution for securely
storing, tracking, sending and receiving Bitcoins.

The online computer is used only for tracking balances and creating and sending
transactions.  Thus it holds no private keys that can be hacked or stolen.
All transactions are signed offline: **your seed and private keys never touch a
network-connected device.**  The offline computer used for wallet creation,
address generation and transaction signing is typically a low-powered device
such as a Raspberry Pi.

MMGen is designed for reliability by having the Bitcoin daemon itself, rather
than less-tested third-party software, do all the “heavy lifting” of tracking
and signing transactions.  It’s also designed with privacy in mind: unlike some
other online/offline wallet solutions, MMGen plus Bitcoin Core is a completely
self-contained system that makes **no connections to the Internet** except for
the Bitcoin network itself: no third parties are involved, and thus no
information about the addresses you’re tracking is leaked to the outside
world.

Like all deterministic wallets, MMGen can generate a virtually unlimited number
of address/key pairs from a single seed.  Your wallet never changes, so you need
back it up only once.

At the heart of the MMGen system is the seed, the “master key” providing access
to all your Bitcoins.  The seed can be stored in five different ways:

  1. as a password-encrypted wallet.  For password hashing, the crack-resistant
	 scrypt hash function is used.  Scrypt’s parameters can be tuned on the
	 command line to make your wallet’s password virtually impossible to crack
	 should it fall into the wrong hands.  The wallet is a tiny, six-line text
	 file suitable for printing or even writing out by hand;

  2. as a seed file: a one-line, conveniently formatted base-58 representation
	 of your unencrypted seed plus a checksum;

  3. as an Electrum-like mnemonic of 12, 18 or 24 words;

  4. as a brainwallet passphrase (this option is recommended only for users who
	 understand the risks of brainwallets and know how to create a strong
	 brainwallet passphrase).  The brainwallet is hashed using scrypt with
	 tunable parameters, making it much harder to crack than standard SHA-256
	 brainwallets; or

  5. as “incognito data”, an MMGen wallet encrypted to make it indistinguishable
	 from random data.  This data can be hidden in and retrieved from a
	 random-data filled disk partition or file at an offset of your choice.
	 This makes it possible to hide a wallet in a public location -- on cloud
	 storage, for example.  Incognito wallet hiding/retrieval is seamlessly
	 integrated into MMGen, making its use nearly as easy as that of the
	 standard wallet.

The best part is that all these methods can be combined.  If you forget your
mnemonic, for example, you can regenerate it and your keys from the stored
wallet or seed file.  Correspondingly, a lost wallet can be regenerated from the
mnemonic or seed or a lost seed from the wallet or mnemonic.  Keys from a
forgotten brainwallet can be recovered from the brainwallet’s corresponding
wallet file.

***mmgen-txcreate running in an Rxvt terminal window***
![mmgen-txcreate running in an Rxvt terminal window][9]

#### Why MMGen is not a BIP32 wallet

Most popular deterministic wallets use the elliptic-curve-based BIP32 or
Electrum protocols to generate their key/address pairs.  MMGen, on the other
hand, uses a much simpler system: a SHA-512 hash chain with double SHA-256
branches.  One advantage of this system is that you can recover your keys from
an MMGen seed without the MMGen program itself using standard command-line
utilities.  But the most important advantage is security: elliptic-curve wallets
are not only cryptographically weaker than hash-bashed ones but have a dangerous
flaw -- their “master public key” feature allows an attacker to recover any key
in the wallet from a single compromised key (for a detailed discussion of this
problem, see Vitalik Buterin’s article [Deterministic Wallets, Their Advantages
and Their Understated Flaws][7]).  Though the master public key feature of BIP32
and Electrum wallets is undeniably convenient, MMGen makes up for its absence by
allowing you to save a virtually unlimited number of Bitcoin addresses for
future use in an address file, which addresses may safely be made public.


### Download/Install

> #### [Install a prebuilt bootable image (MMGenLive) on a USB stick][8]

> #### [Install from source on Microsoft Windows][1]

> #### [Install from source on Debian, Ubuntu, Raspbian or Armbian Linux][2]


### Using MMGen

> #### [Getting Started with MMGen][3]

> #### [MMGen Quick Start with Regtest Mode][q]

> #### [MMGen command help][6]

> #### [Recovering your keys without the MMGen software][r]

> #### [Forkcoin and Altcoin support (BCH,LTC,ETH,ETC,ZEC,XMR and 144 Bitcoin-derived alts)][x]

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

[**Forum**][4] |
[Reddit][0] |
[PGP Public Key][5] |
Donate (BTC,BCH): 15TLdmi5NYLdqmtCqczUs5pBPkJDXRs83w

[0]: https://www.reddit.com/user/mmgen-py
[1]: https://github.com/mmgen/mmgen/wiki/Install-MMGen-on-Microsoft-Windows
[2]: https://github.com/mmgen/mmgen/wiki/Install-MMGen-on-Debian-or-Ubuntu-Linux
[3]: https://github.com/mmgen/mmgen/wiki/Getting-Started-with-MMGen
[4]: https://bitcointalk.org/index.php?topic=567069.0
[5]: https://github.com/mmgen/mmgen/wiki/MMGen-Signing-Key
[6]: https://github.com/mmgen/mmgen/wiki/MMGen-command-help
[q]: https://github.com/mmgen/mmgen/wiki/MMGen-Quick-Start-with-Regtest-Mode
[7]: http://bitcoinmagazine.com/8396/deterministic-wallets-advantages-flaw/
[8]: https://github.com/mmgen/MMGenLive
[9]: https://cloud.githubusercontent.com/assets/6071028/20677261/6ccab1bc-b58a-11e6-8ab6-094f88befef2.jpg
[r]: https://github.com/mmgen/mmgen/wiki/Recovering-Your-Keys-Without-the-MMGen-Software
[x]: https://github.com/mmgen/mmgen/wiki/Getting-Started-with-MMGen#a_alt
[z]: https://user-images.githubusercontent.com/6071028/31656274-a35a1252-b31a-11e7-93b7-3d666f50f70f.png
