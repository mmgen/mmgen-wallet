MMGen = Multi-Mode GENerator
============================
##### a Bitcoin cold storage solution for the command line

### Description

MMGen is a Bitcoin cold-storage system implemented as a suite of Python
command-line scripts requiring only a bare minimum of system resources.  The
scripts work in tandem with a modified Satoshi bitcoind running on an online
computer and a stock bitcoind running offline to provide a robust solution for
securely storing, tracking, sending and receiving Bitcoins.  "Non-MMGen"
addresses can be tracked and spent as well, creating an easy migration path from
other wallets.

To track address balances, MMGen relies on a bitcoin daemon modified by
Bitcoin core developers to support watch-only addresses.  This feature
will one day be included in the mainline Satoshi build.  In the meantime,
instructions are provided below for compiling the modified bitcoind.  Under
Linux, this is a trivial task for even a casual user.  Unfortunately, the same
can't be said for Windows, but the thoroughly tested, step-by-step Windows build
instructions provided here should guarantee success if followed carefully and
make the process as painless as possible.

MMGen is designed for reliability by having the reference Satoshi daemon, rather
than less-tested third-party software, do all the "heavy lifting" of tracking
and signing transactions.  It's also designed for privacy: unlike some other
online/offline wallet solutions, the MMGen system is completely self-contained,
requiring no external server to do its work, which means no third party will
know which addresses you're tracking.

Like all deterministic wallets, MMGen can generate a virtually unlimited number
of address/key pairs from a single seed.  Your wallet never changes, so you need
to back it up only once.  Transactions are signed offline: your seed and private
keys never touch an online computer.

At the heart of the MMGen system is the seed, the "master key" providing access
to all your Bitcoins.  The seed can be stored in four different ways:

  1. as a password-encrypted wallet.  For password hashing, the crack-resistant
	 scrypt hash function is used.  Scrypt's parameters can be customized on the
	 command line to make your wallet's password virtually impossible to crack
	 should it fall into the wrong hands.  The wallet is a tiny, six-line text
	 file suitable for printing or even writing out by hand;

  2. as a seed file: a one-line base-58 representation of your unencrypted seed
     with a checksum;

  3. as an Electrum-like mnemonic of 12, 18 or 24 words; or

  4. as a brainwallet password (this option is recommended for expert users
     only).

The best part is that all these methods can be combined.  If you forget your
mnemonic, for example, you can regenerate it and your keys from the stored
wallet or seed file.  Correspondingly, a lost wallet can be regenerated from the
mnemonic or seed or a lost seed from the wallet or mnemonic.


### Download/Install

> #### [Install on Microsoft Windows][1]

> #### [Install on Debian/Ubuntu Linux][2]


### Using MMGen

> #### See [Getting Started with MMGen][3]

> #### [MMGen command help][6]

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

[**Forum**][4] |
[PGP Public Key][5] |
Donate: 15TLdmi5NYLdqmtCqczUs5pBPkJDXRs83w

[1]: https://github.com/mmgen/mmgen/wiki/Install-MMGen-on-Microsoft-Windows
[2]: https://github.com/mmgen/mmgen/wiki/Install-MMGen-on-Debian-or-Ubuntu-Linux
[3]: https://github.com/mmgen/mmgen/wiki/Getting-Started-with-MMGen
[4]: https://bitcointalk.org/index.php?topic=567069.0
[5]: https://github.com/mmgen/mmgen/wiki/MMGen-Signing-Key
[6]: https://github.com/mmgen/mmgen/wiki/Command-Help
