## Table of Contents

#### [Preliminaries](#a_i)
* [Before you begin](#a_bb)
* [Invocation](#a_iv)
* [Configuration file](#a_cf)
* [Bob and Alice regtest mode](#a_ts)

#### [Generating a Wallet](#a_gw)

#### [Transacting](#a_tr)
* [Generate addresses](#a_ga)
* [Import addresses](#a_ia)
* [Create a transaction](#a_ct)
* [Sign a transaction](#a_sg)
* [Send a transaction](#a_st)

#### [Additional Features](#a_af)
* [Using the mnemonic, seed and hexseed formats](#a_ms)
* [Mnemonics, seeds and hexseeds: additional information](#a_ai)
* [Die roll wallet generation](#a_dr)
* [BIP39 seed phrase support](#a_39)
* [Monero seed phrase support](#a_mm)
* [Incognito wallets](#a_ic)
	* [Hidden incognito wallets](#a_hi)

#### [Advanced Topics](#a_at)
* [Hot wallets](#a_hw)
* [Transaction Fees](#a_fee)
* [BIP 125 replace-by-fee (RBF) transactions](#a_rbf)
	* [With an online (hot) wallet](#a_rbf_onl)
	* [With an offline (cold storage) wallet](#a_rbf_onf)
* [Keeping your installation up to date](#a_ud)
	* [Stable version](#a_uds)
	* [Development version](#a_udd)

### <a id="a_i">Preliminaries</a>

#### <a id="a_bb">Before you begin</a>

Before you begin, please note that the filenames, seed IDs and Bitcoin addresses
used in this primer are intentionally invalid and are for purposes of
illustration only.  As you perform the exercises, you will substitute real ones
in their place.

The up arrow (for repeating commands) and tab key (or Ctrl-I) (for completing
commands and filenames) will speed up your work at the command line greatly.

The examples in this tutorial are geared towards Bitcoin, but with some
modification they may be used with altcoins and forkcoins for which MMGen
Wallet supports transaction operations (BCH, LTC, ETH, ETC, RUNE and XMR as of
this writing).  See [Altcoin-and-Forkcoin-Support][09] for more details.

#### <a id="a_iv">Invocation</a>

MMGen Wallet is not a single program but a suite of scripts run from the command
line.  Commands all begin, not surprisingly, with `mmgen`, and thus you may view
all available commands by typing `mmgen` followed by the TAB key.  Every command
has a help screen displaying detailed usage and options information, available
by entering the command name followed by `--help`.  Note that most command
options have long and short versions.  For example, the `--help` option may be
abbreviated to `-h`.  Exceptions are the options listed by `--longhelp`, which
have no short versions.

MMGen Wallet’s scripts are generally interactive, providing you with information
and prompting you for input.  The `--verbose` or `-v` option requests commands
to be more wordy, while the `--quiet` or `-q` option suppresses all but the most
essential information.  These options are available for all MMGen Wallet
commands.  The `--yes` option (available only for certain commands) suppresses
even more information and can be used to make some commands non-interactive and
scriptable.

Certain options require parameters, such as the `--seed-len` option, for
instance, which takes a parameter of `128`, `192` or `256`.  Commands may also
take optional or required arguments.  For example, `mmgen-addrgen` requires an
address or range of addresses as an argument.  Arguments must always follow
options on the command line.

Sample command invocations:

```text
$ mmgen-txcreate --help
$ mmgen-txcreate --coin=eth --help
$ mmgen-addrgen --verbose 1-10
$ mmgen-walletgen
$ mmgen-walletgen --quiet --seed-len 128
```

Note that the help screens are contextual, so the first two invocations will
produce different output.

#### <a id="a_cf">Configuration file</a>

Just like Bitcoin Core, MMGen Wallet has its own data directory, `.mmgen` in the
user’s home directory, and configuration file, `mmgen.cfg`.  The config file
contains global settings which you may wish to edit at some point to customize
your installation.  These settings include the maximum transaction fee; the user
name, password and hostname used for communicating with your Bitcoin or altcoin
daemon; and many others.  For details, consult the configuration file itself,
which is extensively commented.

#### <a id="a_ts">Bob and Alice regtest mode</a>

If you just want to quickly test using MMGen Wallet, it’s possible to perform
all wallet generation, wallet format conversion, address and key generation, and
address import operations on an offline computer with no blockchain and no coin
balance.

However, if you want to practice creating, signing and sending transactions with
real assets, you’ll need a fully synced blockchain and some coins to play with.
This involves an expenditure of both time and money.

Fortunately, there’s an alternative: MMGen Wallet’s **regtest mode** creates a
virtual network of two users, Bob and Alice, who transact with each other on a
private blockchain.  All of MMGen Wallet’s functionality is available in regtest
mode, making it an ideal way to learn to use the wallet without risking real
coins.  You may wish to pause here and perform the steps in the tutorial [MMGen
Wallet Quick Start with Regtest Mode][04] before continuing on.

### <a id="a_gw">Generating a Wallet</a>

*NOTE: MMGen Wallet supports a “default wallet” feature.  After generating your
wallet, you’ll be prompted to make it your default.  If you answer ‘y’, the
wallet will be stored in your MMGen data directory and used for all future
commands that require a wallet or other seed source.*

*You may not want this feature if you plan to store your wallet in a location
other than your MMGen data directory.  Otherwise, it’s recommended, as it frees
you from having to type your wallet filename on the command line.*

*The following examples assume that you’ve chosen to use a default wallet.
If you haven’t, then you must include the path to a wallet file or other seed
source in all commands where a seed source is required.*

On your **offline** computer, generate a wallet:

```text
$ mmgen-walletgen
...
MMGen wallet written to file '/home/username/.mmgen/89ABCDEF-76543210[256,3].mmdat'
```

`89ABCDEF` is the Seed ID; `76543210` is the Key ID. These are randomly
generated, so your IDs will of course be different than these.

The Seed ID never changes and is used to identify all keys/addresses generated
by this wallet.  Since it’s your wallet’s primary identifier, you should
memorize it visually.  The Key ID changes whenever the wallet’s password or hash
preset are changed and doesn’t need to be memorized.

`256` is the seed length; `3` is the scrypt hash preset.  These values are
configurable: type `mmgen-walletgen --help` for details.

Before transferring funds into your wallet, you should back it up in several
places and preferably on several media such as paper, flash memory or optical
disk.  You’re advised to use a passphrase with your wallet.  Otherwise, anyone
who gains physical access to one of your backups can easily steal your coins.
Don’t forget your passphrase.  If you do, the coins in your wallet are gone
forever.

Since the wallet is a small, humanly readable ASCII file, it can easily be
printed out on paper.

Another highly recommended way to back up your wallet is to generate a mnemonic
seed phrase or seed file [as described below](#a_ms) and record or memorize it.
If you have an average or better memory, you’ll find memorizing your seed phrase
to be surprisingly easy. And the peace of mind that comes with knowing that your
coins are recoverable **even if you lose all your physical backups** can’t be
overestimated.

### <a id="a_tr">Transacting</a>

*The following transacting information is applicable to BTC, BCH, LTC, ETH, ETC
and RUNE. For transacting with Monero, consult [Altcoin-and-Forkcoin-Support][x]
and the [`mmgen-xmrwallet`][mx] help screen.*

#### <a id="a_ga">Generate addresses (offline computer)</a>

Now generate ten Segwit-P2SH addresses with your just-created wallet:

```text
$ mmgen-addrgen --type=segwit 1-10
...
Addresses written to file '89ABCDEF-S[1-10].addrs'

$ cat '89ABCDEF-S[1-10].addrs'
89ABCDEF SEGWIT {
  1    36bNmyYISiptuvJG3X7MPwiiS4HYvD7ksE
  2    3AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc
  3    3HgYCsfqYzIg7LVVfDTp7gYJocJEiDAy6N
  4    34Tu3z1tiexXDonNsFIkvzqutE5E3pTK8s
  5    3PeI55vtp2bX2uKDkAAR2c6ekHNYe4Hcq7
  6    3FEqfEsSILwXPfMvVvVuUovzTaaST62Mnf
  7    3LTTzuhMqPLwQ4IGCwwugny6ZMtUQJSJ1
  8    3F9495H8EJLb54wirgZkVgI47SP7M2RQWv
  9    3JbrCyt7BdxRE9GX1N7GiEct8UnIjPmpYd
  10   3H7vVTk4ejUbQXw45I6g5qvPBSe9bsjDqh
}
```

Note that the address range `1-10` specified on the command line is included in
the resulting filename.

MMGen Wallet currently supports four address types for Bitcoin and Bitcoin code
fork coins: `legacy` (uncompressed P2PKH), `compressed` (compressed P2PKH),
`segwit` (P2SH-P2WPKH) and `bech32` (native Segwit), denoted by the code letters
`L`, `C`, `S` and `B` respectively.  Address types can be referred to either in
full or by code letter.  To generate Bech32 addresses, for example, you can
specify either `--type=bech32` or `--type=B` on the command line.

For backwards compatibility, legacy addresses with uncompressed public keys
are generated by default, but this is almost certainly not what you want
unless you’re restoring an old MMGen Wallet installation created before
compressed address support was added.  Most new users will wish to generate
either Segwit-P2SH (`S`) or Bech32 (`B`) addresses instead.  For BCH, which
lacks Segwit support, compressed (`C`) addresses are the best choice.

Generation examples for various address types:

```text
# legacy (uncompressed P2PKH)
$ mmgen-addrgen 1-10
...

$ cat '89ABCDEF[1-10].addrs'
89ABCDEF {
  1   12GiSWo9zIQgkCmjAaLIrbPwXhKry2jHhj
...
```

```text
# compressed P2PKH
$ mmgen-addrgen --type=compressed 1-10
...

$ cat '89ABCDEF-C[1-10].addrs'
89ABCDEF COMPRESSED {
  1   13jbRxWjswXtaDzLBJDboMcIe6nLohFb9M
...
```

```text
# Bech32 (native Segwit)
$ mmgen-addrgen --type=bech32 1-10
...

$ cat '89ABCDEF-B[1-10].addrs'
89ABCDEF BECH32 {
  1   bc1q9c9273thh3xh86lk6z34raejz6j2s8ytgyb7my
...
```

Note that for non-legacy address types the code letter is included in the
filename.

#### <a id="a_ia">Import addresses (online computer)</a>

To fund your wallet, you must import the addresses you’ve generated into your
tracking wallet.

Start the coin daemon with the required options (see the [Install-Bitcoind][08]
wiki page for more details on invoking the daemon for your coin and platform).

Upon startup, older daemons used to automatically generate a new default
`wallet.dat`, which MMGen Wallet used as its tracking wallet.  With newer
daemons (e.g. Core 0.21.0 and above), the tracking wallet is generated when
first invoking `mmgen-addrimport` and will be a directory named
`mmgen-tracking-wallet` located by default under the `wallets` subdirectory
in your coin daemon’s datadir.

Create your tracking wallet and import the ten addresses generated above into
it as follows:

```text
$ mmgen-addrimport my.addrs
```

These addresses are now tracked: any BTC transferred to them will show up in
your listing of address balances, and balances will be updated automatically
as your node syncs with the blockchain.  Balances can be viewed using
`mmgen-tool listaddresses`:

```text
$ mmgen-tool listaddresses
MMGenID       Address                             Comment    Balance
89ABCDEF:S:1  36bNmyYISiptuvJG3X7MPwiiS4HYvD7ksE               0
89ABCDEF:S:2  3AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc               0
89ABCDEF:S:3  3HgYCsfqYzIg7LVVfDTp7gYJocJEiDAy6N               0
89ABCDEF:S:4  34Tu3z1tiexXDonNsFIkvzqutE5E3pTK8s               0
89ABCDEF:S:5  3PeI55vtp2bX2uKDkAAR2c6ekHNYe4Hcq7               0
...
TOTAL: 0 BTC
```

Invoke `mmgen-tool listaddresses interactive=1` and add some comments to your
newly-imported addresses using the ‘l’ key.  Depending on your comments, your
output will now look something like this:

```text
MMGenID       Address                             Comment    Balance
89ABCDEF:S:1  36bNmyYISiptuvJG3X7MPwiiS4HYvD7ksE  Donations    0
89ABCDEF:S:2  3AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc  Storage 1    0
89ABCDEF:S:3  3HgYCsfqYzIg7LVVfDTp7gYJocJEiDAy6N  Storage 2    0
89ABCDEF:S:4  34Tu3z1tiexXDonNsFIkvzqutE5E3pTK8s  Storage 3    0
89ABCDEF:S:5  3PeI55vtp2bX2uKDkAAR2c6ekHNYe4Hcq7               0
...
TOTAL: 0 BTC
```

*While not covered in this introduction, note that it’s also possible to [import
non-MMGen coin addresses into your tracking wallet][01].  This allows MMGen
Wallet to track and spend funds from another wallet without having to transfer
the coins via the blockchain.  To do this, you must save the private keys
corresponding to the given addresses in a separate file for use during
transaction signing.*

Note that each address has a unique ID (the ‘MMGen ID’) consisting of a Seed ID,
address type code letter, and index.  Addresses of different types may be
imported into the same tracking wallet, and since they’re generated from different
sub-seeds you needn’t worry about key reuse.  For example, the addresses
`89ABCDEF:S:1` and `89ABCDEF:B:1` are cryptographically unrelated: no one but the
wallet’s owner can see that they were generated from the same seed.

Now that your addresses are being tracked, you may send some BTC to them over
the Bitcoin network.  If you send 0.1, 0.2, 0.3 and 0.4 BTC respectively, your
address listing will look like this after the transactions have confirmed:

```text
$ mmgen-tool listaddresses
MMGenID       Address                             Comment    Balance
89ABCDEF:S:1  36bNmyYISiptuvJG3X7MPwiiS4HYvD7ksE  Donations    0.1
89ABCDEF:S:2  3AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc  Storage 1    0.2
89ABCDEF:S:3  3HgYCsfqYzIg7LVVfDTp7gYJocJEiDAy6N  Storage 2    0.3
89ABCDEF:S:4  34Tu3z1tiexXDonNsFIkvzqutE5E3pTK8s  Storage 3    0.4
TOTAL: 1 BTC
```

#### <a id="a_ct">Create a transaction (online computer)</a>

Now that you have some coins under MMGen Wallet’s control, you’re ready to
create a transaction.  Note that transactions are harmless until they’re signed
and broadcast to the network, so feel free to experiment and create transactions
with different combinations of inputs and outputs.  Of course, if you’re using
testnet or regtest mode, you risk nothing even when broadcasting transactions.

To send 0.1 BTC to the a third-party address
`3AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc`, for example, and send the change back to
yourself at address `89ABCDEF:S:5`, you’d issue the following command:

```text
$ mmgen-txcreate 3AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc,0.1 89ABCDEF:S:5
```

`mmgen-txcreate` accepts either MMGen IDs or Bitcoin addresses as arguments.

NOTE: For backwards compatibility, legacy addresses may omit the code letter
from the MMGen ID.  Thus address `89ABCDEF:L:5` may be expressed as
`89ABCDEF:5`.  For other address types the code letter is mandatory.

To send 0.1 BTC to each of addresses `89ABCDEF:S:6` and `89ABCDEF:S:7`,
sending the change to `89ABCDEF:S:8`, you’d do this:

```text
$ mmgen-txcreate 89ABCDEF:S:6,0.1 89ABCDEF:S:7,0.1 89ABCDEF:S:8
```

As you can see, each address is followed by a comma and an amount, except for
the change address, for which the amount will be calculated automatically.
All addresses belonging to your seed in the above examples are already
imported and tracked, so you’re OK.  If you wanted to send to `89ABCDEF:S:11`,
you’d have to import it first.


Let’s go with the first of our two examples above.

Upon invocation, the `mmgen-txcreate` command shows you a list of your
unspent outputs along with a menu allowing you to sort the outputs by four
criteria: transaction ID, address, amount and transaction age.  Your overall
balance in BTC appears at the top of the screen.  In our example, the display
will look something like this:

```text
UNSPENT OUTPUTS (sort order: Age)  Total BTC: 1
 Num  TX id  Vout    Address                               Amt(BTC) Age(d)
 1)   e9742b16... 5  3L3kxmi.. 89ABCDEF:S:1    Donations       0.1    1
 2)   fa84d709... 6  3N4dSGj.. 89ABCDEF:S:2    Storage 1       0.2    1
 3)   8dde8ef5... 6  3M1fVDc.. 89ABCDEF:S:3    Storage 2       0.3    1
 4)   c76874c7... 0  3E8MFoC.. 89ABCDEF:S:4    Storage 3       0.4    1

Sort options: [t]xid, [a]mount, a[d]dress, [A]ge, [r]everse, [M]mgen addr
Display options: show [D]ays, [g]roup, show [m]mgen addr, r[e]draw screen
'q'=quit view, 'p'=print to file, 'v'=pager view, 'w'=wide view, 'l'=add label:
```

After quitting the menu with ‘q’, you’ll see the following prompt:

```text
Enter a range or space-separated list of outputs to spend:
```

Here you must choose unspent outputs of sufficient value to cover the send
amount of 0.1 BTC, plus the transaction fee (for more on fees, see ‘Transaction
Fees’ under ‘Advanced Topics’ below).  Output #2 is worth 0.2 BTC, which is
sufficient, so we’ll choose that and hit ENTER.  When prompted for a
transaction fee, we’ll choose 0.0001 BTC (note that integer fees followed by
the letter ‘s’ for “satoshis per byte” are also accepted, and this is actually
the preferred way to indicate fees).  After a couple more prompts and
confirmations, your transaction will be saved:

```text
Transaction written to file 'FEDCBA[0.1].rawtx'
```

The transaction filename consists of a unique MMGen Transaction ID plus the
non-change spend amount.

As you can see, MMGen Wallet gives you complete control over your transaction
inputs and change addresses.  This feature will be appreciated by
privacy-conscious users.

#### <a id="a_sg">Sign a transaction (offline computer)</a>

Now transfer the the raw transaction file to your offline computer and sign it
using your default wallet:

```text
$ mmgen-txsign FEDCBA[0.1].rawtx
...
Signed transaction written to file 'FEDCBA[0.1].sigtx'
```

Note that the signed transaction file has a new extension, `.sigtx`.

#### <a id="a_st">Send a transaction (online computer)</a>

Now you’re ready for the final step: broadcasting the transaction to the
network.  Start bitcoind if it’s not already running, and make sure your
blockchain is fully synced.  Then copy the signed transaction file to your
online computer and issue the command:

```text
$ mmgen-txsend FEDCBA[0.1].sigtx
...
Transaction sent: abcd1234....
```

Like all MMGen Wallet commands, `mmgen-txsend` is interactive, so you’ll be
prompted before the transaction is actually broadcast.  If the send was
successful, a 64-character hexadecimal Bitcoin Transaction ID will be displayed
(`abcd1234...` in our case).

Once the transaction is broadcast to the network and confirmed, your address
listing should look something like this:

```text
$ mmgen-tool listaddresses
MMGenID       Address                             Comment    Balance
89ABCDEF:S:1  36bNmyYISiptuvJG3X7MPwiiS4HYvD7ksE  Donations    0.1
89ABCDEF:S:3  3HgYCsfqYzIg7LVVfDTp7gYJocJEiDAy6N  Storage 2    0.3
89ABCDEF:S:4  34Tu3z1tiexXDonNsFIkvzqutE5E3pTK8s  Storage 3    0.4
89ABCDEF:S:5  3PeI55vtp2bX2uKDkAAR2c6ekHNYe4Hcq7               0.0999
TOTAL: 0.8999 BTC
```

Alternatively, you may use view your addresses with `mmgen-tool twview`, which
lists only unspent outputs and provides some additional information:

```text
$ mmgen-tool twview
UNSPENT OUTPUTS (sort order: Age) Total BTC: 0.8999
Network: BTC MAINNET
 Num TXid Vout Address                                             Amt(BTC)      Confs
 1)  e3c3..  6 36bNmyYISiptuvJG3X7MPwii.. 89ABCDEF:S:1 Donations      0.1        68
 2)  face..  6 3HgYCsfqYzIg7LVVfDTp7gYJ.. 89ABCDEF:S:3 Storage 2      0.3        68
 3)  abab..  6 34Tu3z1tiexXDonNsFIkvzqu.. 89ABCDEF:S:4 Storage 3      0.4        68
 4)  123c..  6 3PeI55vtp2bX2uKDkAAR2c6e.. 89ABCDEF:S:5                0.0999     7
```

Since you’ve sent 0.1 BTC to a third party, your balance has decreased by 0.1
BTC plus the transaction fee of 0.0001 BTC.

Congratulations!  You’ve now mastered the basics of MMGen Wallet!  To learn
about some more advanced features, continue reading.

### <a id="a_af">Additional Features</a>

#### <a id="a_ms">Using the mnemonic, seed and hexseed formats</a>

Using your default wallet from the exercises above, generate a mnemonic seed
phrase:

```text
$ mmgen-walletconv -o words
...
Mnemonic data written to file '89ABCDEF.mmwords'

$ cat 89ABCDEF.mmwords
pleasure tumble spider laughter many stumble secret bother after search
float absent path strong curtain savior worst suspend bright touch away
dirty measure thorn
```

Since our seed is 256 bits long, the seed phrase contains 24 words.  128-bit and
192-bit seeds generate shorter mnemonics of 12 and 18 words, respectively.
Wallets with these seed lengths can be generated using the `--seed-len` option
to `mmgen-walletgen`.

Though some consider 128 bits of entropy to provide adequate security for the
foreseeable future, it’s advisable to stick to the default 256-bit seed length.
You’ll find that even a 24-word seed phrase is not difficult to memorize.

NOTE: MMGen mnemonics are generated from the Electrum wordlist, but using
ordinary base conversion instead of Electrum’s more complicated algorithm.

The seed phrase is a complete representation of your seed and may be used
anywhere where you’d use a wallet.  For example, you can generate addresses with
it:

```text
$ mmgen-addrgen --type=segwit 89ABCDEF.mmwords 1-10
...
Address data written to file '89ABCDEF-S[1-10].addrs'
```

You can use it to sign transactions:

```text
$ mmgen-txsign FEDCBA[0.1].rawtx 89ABCDEF.mmwords
...
Signed transaction written to file 'FEDCBA[0.1].sigtx'
```

The seed phrase can also be used to regenerate a lost wallet:

```text
$ mmgen-walletconv 89ABCDEF.mmwords
...
MMGen wallet written to file '89ABCDEF-01234567[256,3].mmdat'
```

Note that the regenerated wallet has a different Key ID but of course the same
Seed ID.

An alternative to seed phrases, seed files provide yet another way of representing
your seed.  They bear the extension `.mmseed` and are generated exactly the same
way as mnemonic files:

```text
$ mmgen-walletconv -o seed
...
Seed data written to file '89ABCDEF.mmseed'
```

They can be used just like mnemonics to regenerate a wallet:

```text
$ mmgen-walletconv 89ABCDEF.mmseed
...
MMGen wallet written to file '89ABCDEF-23456701[256,3].mmdat'
```

Here’s a sample seed file for a 256-bit seed:

```text
$ cat 8B7392ED.mmseed
f4c84b C5ZT wWpT Jsoi wRVw 2dm9 Aftd WLb8 FggQ eC8h Szjd da9L
```

And for a 128-bit seed:

```text
$ cat 8E0DFB78.mmseed
0fe02f XnyC NfPH piuW dQ2d nM47 VU
```

As you can see, seed files are short enough to be easily written out by hand or
memorized.  And their built-in checksum makes it easy to test your memory using
a simple Unix shell command:

```text
$ echo -n XnyC NfPH piuW dQ2d nM47 VU | tr -d ' '| sha256sum | cut -c 1-6
0fe02f
```

Or you can do the same thing with `mmgen-tool`:

```text
$ mmgen-tool str2id6 'XnyC NfPH piuW dQ2d nM47 VU'
0fe02f
```

Beginning with version 0.9.0, MMGen Wallet also supports seed files in
hexadecimal (hexseed) format.  Hexseed files are identical to seed files but
encoded in hexadecimal rather than base 58.  They bear the extension `.mmhex`:

```text
$ cat FE3C6545.mmhex
afc3fe 456d 7f5f 1c4b fe3b c916 b875 60ae 6a3e
```

You can easily check that a hexseed is correct by generating its Seed ID with
standard command-line tools:

```text
$ echo 456d 7f5f 1c4b fe3b c916 b875 60ae 6a3e | tr -d ' ' | xxd -r -p | sha256sum -b | xxd -r -p | sha256sum -b | cut -c 1-8
fe3c6545
```

Mnemonics and hexseeds can be used to generate keys even without the MMGen
Wallet software, using basic command-line utilities, as explained in [this
tutorial][03].

#### <a id="a_ai">Mnemonics, seeds and hexseeds: additional information</a>

All MMGen Wallet commands that take mnemonic, seed or hexseed data may receive
the data interactively from the user instead of from a file.  This feature
allows you to store your seed entirely in your head if you wish and never record
it on a physical medium.  To input your seed data at the prompt, just specify an
input format instead of a file name:

```text
$ mmgen-addrgen -i words 1-10
...
Choose a mnemonic length: 1) 12 words, 2) 18 words, 3) 24 words: 1
Mnemonic length of 12 words chosen. OK? (Y/n): y
Enter your 12-word mnemonic, hitting RETURN or SPACE after each word:
Enter word #1:
```

Here the script will prompt you interactively for each word of the seed phrase,
checking it for validity and reprompting if necessary.  The words are not
displayed on the screen.

As a safeguard against over-the-shoulder, Tempest and other side-channel
attacks, MMGen Wallet never outputs secret data to the screen, unless you
explicitly ask it to with the `--stdout` or `-S` option.  And even with this
option in effect, you’ll still be prompted before the secret data is actually
displayed.  This guard prompt is overridden by the `--quiet` option, however,
always think twice before using `--stdout` together with `--quiet`.

Files produced by MMGen Wallet’s commands may be written to a directory of your
choice using the `--outdir` or `-d` option.  For example, on a Linux system you
can use `--outdir=/dev/shm` to write keys and seeds to volatile memory instead
of disk, ensuring that no trace of your secret data remains once your computer’s
been powered down.

#### <a id="a_dr">Die roll wallet generation</a>

Interactive dieroll wallet generation works just like the interactive mnemonic
seed phrase input described in the preceding section.  To generate a new dieroll
wallet, type:

```text
$ mmgen-walletconv -i dieroll
```

To save the wallet in a format of your choice, use the `-o` option:

```text
$ mmgen-walletconv -i dieroll -o bip39
```

50, 75 and 100 rolls of the die are required to create 128, 192 and 256-bit
seeds, respectively.

#### <a id="a_39">BIP39 seed phrase support</a>

BIP39 mnemonic seed phrase support and usage is identical to that for native
MMGen mnemonics described above.  Just use the `bip39` format specifier and
extension instead of `words`.

Convert an MMGen native mnemonic wallet to BIP39:

```text
$ mmgen-walletconv -o bip39 mywallet.words
```

Restore a wallet from a BIP39 seed phrase in a file:

```text
$ mmgen-walletconv seed.bip39
```

#### <a id="a_mm">Monero seed phrase support</a>

MMGen Wallet has limited support for Monero new-style mnemonic seed phrases.
While they can’t be used as wallets, they’re supported as a password format by
the `mmgen-passgen` command and can be converted to and from hex data by the
`mmgen-tool` mnemonic commands.  The format specifier and extension is
`xmrseed`.  Only 25-word seed phrases (256-bit keys) are supported.  Key data
is reduced in accordance with the Monero protocol before conversion, so the
resulting seed phrases are guaranteed to be canonical.

Generate a random Monero seed phrase:

```text
$ mmgen-tool mn_rand256 fmt=xmrseed
```

Generate a list of passwords in Monero mnemonic format with ID 'foo' from your
default wallet:

```text
$ mmgen-passgen -f xmrseed 'foo' 1-10
```

#### <a id="a_ic">Incognito wallets</a>

An incognito format wallet is indistinguishable from random data, allowing you
to hide your wallet at an offset within a random-data-filled file or partition.
Barring any inside knowledge, a potential attacker has no way of knowing where
the wallet is hidden, or whether the file or partition contains anything of
interest at all, for that matter.

An incognito wallet with a reasonably secure password could even be hidden on
unencrypted cloud storage.  Hiding your wallet at some offset in a 1GB file
increases the difficulty of any attack by a factor of one billion, assuming
again that any potential attacker even knows or suspects you have a wallet
hidden there.

If you plan to store your incognito wallet in an insecure location such as cloud
storage, you’re advised to use a strong scrypt (hash) preset and a strong
password.  These can be changed using the `mmgen-passchg` utility:

```text
$ mmgen-passchg -p 5 89ABCDEF-01234567[256,3].mmdat
...
Hash preset of wallet: '3'
Enter old passphrase for MMGen wallet: <old weak passphrase>
...
Hash preset changed to '5'
Enter new passphrase for MMGen wallet: <new strong passphrase>
...
MMGen wallet written to file '89ABCDEF-87654321[256,5].mmdat'
```

The scrypt preset is the numeral in the wallet filename following the seed
length.  As you can see, it’s now changed to `5`.  Now export your new toughened
wallet to incognito format, using the `-k` option to leave the passphrase
unchanged:

```text
$ mmgen-walletconv -k -o incog 89ABCDEF-87654321[256,5].mmdat
...
Reusing passphrase at user request
...
New Incog Wallet ID: ECA86420
...
Incognito data written to file '89ABCDEF-87654321-ECA86420[256,5].mmincog'
```

Incog wallets have a special identifier, the Incog ID, which can be used to
locate the wallet data if you’ve forgotten where you hid it (see the example
below).  Naturally, an attacker could use this ID to find the data too, so it
should be kept secret.

Incog wallets can also be output to hexadecimal format:

```text
$ mmgen-walletconv -k -o incox 89ABCDEF-87654321[256,5].mmdat
...
Hex incognito data written to file '89ABCDEF-87654321-CA86420E[256,5].mmincox'
```

```text
$ cat 89ABCDEF-87654321-1EE402F4[256,5].mmincox
6772 edb2 10cf ad0d c7dd 484b cc7e 42e9
4fe6 e07a 1ce2 da02 6da7 94e4 c068 57a8
3706 c5ce 56e0 7590 e677 6c6e 750a d057
b43a 21f9 82c7 6bd1 fe96 bad9 2d54 c4c0
```

Note that the Incog ID is different here: it’s generated from an init vector,
which is a different random number each time, making the incog data as a whole
different as well.  This allows you to store your incog data in multiple
public locations without having repeated ‘random’ wallet data give you away.

This data is ideally suited for a paper wallet that could potentially fall into
the wrong hands.

Your incognito wallet (whether hex or binary) can be used just like any other
wallet, mnemonic or seed file to generate addresses and sign transactions:

```text
$ mmgen-addrgen --type=segwit 89ABCDEF-87654321-CA86420E[256,5].mmincox 101-110
...
Generated 10 addresses
Addresses written to file '89ABCDEF-S[101-110].addrs'

$ mmgen-txsign FABCDE[0.3].rawtx 89ABCDEF-87654321-CA86420E[256,5].mmincox
...
Signed transaction written to file FABCDE[0.3].sigtx
```

##### <a id="a_hi">Hidden incognito wallets</a>

With the `-o hincog` option, incognito wallet data can be created and hidden at
a specified offset in a file or partition in a single convenient operation, with
the random file being created automatically if necessary.  Here’s how you’d
create a 1GB file `random.dat` and hide a wallet in it at offset `123456789`:

```text
$ mmgen-walletconv -k -o hincog -J random.dat,123456789 89ABCDEF-87654321[256,5].mmdat
...
New Incog Wallet ID: ED1F2ACB
...
Requested file 'random.dat' does not exist.  Create? (Y/n): Y
Enter file size: 1G
...
Data written to file 'random.dat' at offset 123456789
```

Your ‘random’ file can now be uploaded to a cloud storage service, for example,
or some other, preferably non-public, location on the Internet (in a real-life
situation you will choose a less obvious offset than `123456789` though, won’t
you?).

Now let’s say at some point in the future you download this file to recover
your wallet and realize you’ve forgotten the offset where the data is hidden.
If you’ve saved your Incog ID, you’re in luck:

```text
$ mmgen-tool find_incog_data random.dat ED1F2ACB
...
Incog data for ID ED1F2ACB found at offset 123456789
```

The search process can be slow, so patience is required.  In addition, on
large files ‘false positives’ are a distinct possibility, in which case you’ll
need to use the `keep_searching=1` parameter to keep going until you find the
real offset.

Hidden incog wallets are nearly as convenient to use as ordinary ones.
Generating ten addresses with your hidden incog data is as easy as this:

```text
$ mmgen-addrgen -H random.dat,123456789 101-110
```

Transaction signing uses the same syntax:

```text
$ mmgen-txsign -H random.dat,123456789 ABCDEF[0.1].rawtx
...
Signed transaction written to file 'ABCDEF[0.1].sigtx'
```

### <a id="a_at">Advanced Topics</a>

#### <a id="a_hw">Hot wallets</a>

*Instead of using a hot wallet, you should consider setting up [transaction
autosigning][07] on your offline machine.  Autosigning makes it possible to
transact directly from cold storage in a secure and convenient way.  Ideally,
your autosigning device should be a Raspberry Pi or other single-board computer
for which MMGen Wallet provides LED support.  However, an old laptop running
Linux or macOS will also suffice, provided its network interfaces are removed
or disabled.*

To use MMGen Wallet for not only cold storage but also day-to-day transacting,
it’s possible to place a portion of your funds in a “hot wallet” on your online
computer.  You may then use the `mmgen-txdo` command to quickly create, sign and
send transactions in one operation.

*Note: prior to Version 0.11.0, MMGen Wallet implemented hot wallets using
[key-address files][05], but these have now been obsoleted by [subwallets][06].
Information on key-address files is archived [here][05] for the benefit of
legacy installations only.*

Setting up a hot wallet is easy.  Using the [Subwallets][06] wiki page as your
guide, generate a subwallet on your offline machine for use as a hot wallet.
Since this wallet is going to be used in an online environment, make sure it’s
protected with a strong password and hash preset.

```text
$ mmgen-subwalletgen -p5 1L
...
MMGen wallet written to file 'FC9A8735-ABCDEF00[256,5].mmdat'
```

Copy the subwallet to a USB stick or other removable device.

Now on your online computer, check your MMGen data directory for the presence of
wallet files:

```text
$ ls $HOME/.mmgen/*.mmdat
```

If any are present (there shouldn’t be if you’ve been following this guide!),
move them out of harm’s way, or copy them to a backup location and securely
delete the originals with `wipe` or `sdelete` if they’re securing any funds.

Copy the subwallet file to your MMGen data directory, making it your default
wallet for the online machine:

```text
$ cp 'FC9A8735-ABCDEF00[256,5].mmdat' $HOME/.mmgen
```

Securely delete the original file.

Generate a range of addresses with your online default wallet/subwallet and
import them into your tracking wallet:

```text
$ mmgen-addrgen --type=bech32 1-10
$ mmgen-addrimport FC9A8735-B*.addrs
```

Send some coins to an address or addresses in this range using your method of
choice.

Now you can spend from these addresses using `mmgen-txdo`, creating, signing
and sending transactions in one operation:

```text
$ mmgen-txdo 1AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc,0.1 FC9A8735:S:2
(choose an input from wallet FC9A8735)
...
Transaction sent: abcd1234....
```

Bear in mind that your subwallet/online default wallet doesn’t require a backup,
as it can always be regenerated from its offline parent.  If you ever wish to
delete it, however, you should do so securely if there are still funds under its
control.

#### <a id="a_fee">Transaction Fees</a>

MMGen Wallet gives you several options for dealing with transaction fees.

Firstly, and most simply, you may do nothing, in which case the fee will be
calculated automatically using bitcoind’s `estimatesmartfee` RPC call.  You can
adjust the estimated fee by any factor using the `--fee-adj` option, a handy
feature when you need transactions to confirm a bit more quickly.  If network
fee estimation fails for any reason, you’ll be prompted to enter the fee
manually.

Secondly, you may specify the fee as an absolute BTC amount (a decimal number).
This can be done either on the command line or at the interactive prompt when
creating transactions with `mmgen-txcreate`, `mmgen-txdo` or `mmgen-txbump`.

Thirdly, instead of using an absolute BTC amount, you may specify the fee in
satoshis per byte and let MMGen Wallet calculate the fee based on the
transaction size.  This also works both on the command line and at the
interactive prompt.  The satoshis-per-byte specification is an integer followed
by the letter `s`.  A fee of 90 satoshis per byte is thus represented as `90s`.

MMGen Wallet enforces a hard maximum fee (currently 0.003 BTC) which is
alterable only in the config file.  Thus the software will never create or
broadcast any transaction with a mistakenly or dangerously high fee unless you
expressly permit it to.

#### <a id="a_rbf">BIP 125 replace-by-fee (RBF) transactions</a>

As of version 0.9.1, MMGen Wallet supports creating replaceable and replacement
transactions in accordance with the BIP 125 replace-by-fee (RBF) specification.

To make your transactions replaceable, just specify the `--rbf` option when
creating them with `mmgen-txcreate` or `mmgen-txdo`.

Version 0.9.1 also introduces `mmgen-txbump`, a convenient command for quickly
creating replacement transactions from existing replaceable ones.
`mmgen-txbump` can create, sign and send transactions in a single operation if
desired.

Continuing the examples from our primer above, we’ll examine two RBF scenarios,
one for a hot wallet and one for a cold storage wallet.  In the first scenario,
initial and replacement transactions will be created, signed and sent in one
operation.  In the second, a batch of replacement transactions with
incrementally increasing fees will created online and then signed offline.

#### <a id="a_rbf_onl">With an online (hot) wallet</a>

Create, sign and send a BIP 125 replaceable transaction with a fee of 50
satoshis per byte:

```text
$ mmgen-txdo --rbf --fee 50s 1AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc,0.1 0FDE89AB:S:5
...
Signed transaction written to file 'FEDCBB[0.1,50].sigtx'
...
Transaction sent: dcba4321....
```

Here you’ve sent 0.1 BTC to a third-party address and the change back to
yourself at address #5 of your default hot wallet with Seed ID `0FDE89AB`.

Note that the fee is shown in the filename after the send amount.  The presence
of the fee in the filename identifies the transaction as replaceable.

If the transaction fails to confirm in your desired timeframe, then create, sign
and send a replacement transaction with a higher fee, say 100 satoshis per byte:

```text
$ mmgen-txbump --send --fee 100s --output-to-reduce c 'FEDCBB[0.1,50].sigtx'
...
Signed transaction written to file 'DAE123[0.1,100].sigtx'
...
Transaction sent: eef01357....
```

The `--send` switch instructs `mmgen-txbump` to sign and send the transaction
after creating it.  The `--output-to-reduce` switch with an argument of `c`
requests that the increased fee be deducted from the change (`c`) output, which
is usually what is desired.  If you want it taken from some other output,
identify the output by number.  Note that the resulting replacement transaction
has a different identifier, since it’s a new transaction.

If this transaction also fails to confirm, then repeat the above step as many
times as necessary to get a confirmation, increasing the fee each time.  The
only thing you have to modify with each iteration is the argument to `--fee`.
To reduce your typing even further, use the `--yes` switch to skip all
non-essential prompts.

#### <a id="a_rbf_onf">With an offline (cold storage) wallet</a>

To achieve the same result as in the above example using a cold wallet, just
create the initial transaction with `mmgen-txcreate` instead of `mmgen-txdo`:

```text
$ mmgen-txcreate --rbf --fee 50s 1AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc,0.1 89ABCDEF:S:5
...
Transaction written to file 'FEDCBC[0.1,50].rawtx'
```

Now create a series of transactions with incrementally increasing fees for
offline signing:

```text
$ mmgen-txbump --fee 100s --output-to-reduce c 'FEDCBC[0.1,50].rawtx'
$ mmgen-txbump --fee 150s --output-to-reduce c 'FEDCBC[0.1,50].rawtx'
$ mmgen-txbump --fee 200s --output-to-reduce c 'FEDCBC[0.1,50].rawtx'
```

To speed things up, add the `--yes` switch to make `mmgen-txbump` completely
non-interactive.

The result will be four raw transaction files with increasing fees, like this:

```text
FEDCBC[0.1,50].rawtx
3EBB00[0.1,100].rawtx
124FFF[0.1,150].rawtx
73DABB[0.1,200].rawtx
```

Copy the files to an empty folder, transfer the folder to your offline machine and batch sign them:

```text
$ mmgen-txsign -d my_folder --yes my_folder/*.rawtx
```

Then copy the signed transaction files back to your online machine and broadcast
them in turn until you get a confirmation:

```text
$ mmgen-txsend FEDCBC[0.1,50].sigtx   # ...if this doesn’t confirm, then
$ mmgen-txsend 3EBB00[0.1,100].sigtx  # ...if this doesn’t confirm, then
$ mmgen-txsend 124FFF[0.1,150].sigtx  # ...if this doesn’t confirm, then
$ mmgen-txsend 73DABB[0.1,200].sigtx
```

#### <a id="a_ud">Keeping your installation up to date</a>

To make sure you have all the latest features and bugfixes, it’s a good idea to
keep your MMGen Wallet installation upgraded to the latest version.  The
software does no checking for updates, so it’s up to you to do so yourself on a
periodic basis.

##### <a id="a_uds">Stable version:</a>

To update the stable version, simply perform:

```text
$ python3 -m pip install --update mmgen-wallet
```

For an offline installation, download the package on your online machine with
`pip download`, transfer the downloaded package to your offline machine and
install it with `pip install --no-isolation`.

Note that additional dependencies may appear from version to version, causing
an offline installation to fail.  Consult the latest release notes in
`doc/release-notes` or your platform’s installation page in the wiki
([Linux, macOS][li], [Windows][wi]) for more information.

##### <a id="a_udd">Development version:</a>

If you’ve deleted or lost your local copy of the MMGen Wallet repository, clone
it again from Github, Gitlab or mmgen.org:

```text
$ git clone https://github.com/mmgen/mmgen-wallet.git
$ git clone https://gitlab.com/mmgen/mmgen-wallet.git
$ git clone https://mmgen.org/project/mmgen/mmgen-wallet.git
```

Enter the repository and check out the master branch.  Pull the latest changes
from the remote repository:

```text
$ cd mmgen-wallet
$ git checkout master
$ git pull
```

Newly added features may not yet be covered in the documentation, but you may
often find information on them by invoking `git log` or visiting the online
[commits page][cp].

Now build and install:

```text
$ rm -rf dist build *.egg-info
$ python3 -m build --no-isolation
$ python3 -m pip install user --upgrade dist/*.whl
```

[01]: Tracking-and-spending-ordinary-Bitcoin-addresses.md
[02]: https://tpfaucet.appspot.com
[03]: Recovering-Your-Keys-Without-the-MMGen-Wallet-Software.md
[04]: MMGen-Wallet-Quick-Start-with-Regtest-Mode.md
[05]: Key-address-files.md
[06]: Subwallets.md
[07]: cmds/command-help-autosign.md
[08]: Install-Bitcoind.md
[09]: Altcoin-and-Forkcoin-Support.md
[x]:  Altcoin-and-Forkcoin-Support.md#a_xmr
[cp]: ../../../../commits/master
[mx]: cmds/command-help-xmrwallet.md
[li]: Install-MMGen-Wallet-on-Linux-or-macOS.md
[wi]: Install-MMGen-Wallet-on-Microsoft-Windows.md
