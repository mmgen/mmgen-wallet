## Table of Contents

#### <a href='#a_i'>Preliminaries</a>
* <a href='#a_bb'>Before you begin</a>
* <a href='#a_iv'>Invocation</a>
* <a href='#a_cf'>Configuration file</a>
* <a href='#a_ts'>Bob and Alice regtest mode</a>

#### <a href='#a_bo'>Basic Operations</a>
* <a href='#a_gw'>Generate an MMGen wallet</a>
* <a href='#a_ga'>Generate addresses</a>
* <a href='#a_ia'>Import addresses</a>
* <a href='#a_ct'>Create a transaction</a>
* <a href='#a_sg'>Sign a transaction</a>
* <a href='#a_st'>Send a transaction</a>

#### <a href='#a_af'>Additional Features</a>
* <a href='#a_ms'>Using the mnemonic, seed and hexseed formats</a>
* <a href='#a_ai'>Mnemonics, seeds and hexseeds: additional information</a>
* <a href='#a_ic'>Incognito wallets</a>
	* <a href='#a_hi'>Hidden incognito wallets</a>

#### <a href='#a_at'>Advanced Topics</a>
* <a href='#a_hw'>Hot wallets and key-address files</a>
* <a href='#a_fee'>Transaction Fees</a>
* <a href='#a_rbf'>BIP 125 replace-by-fee (RBF) transactions</a>
	* <a href='#a_rbf_onl'>With an online (hot) wallet</a>
	* <a href='#a_rbf_onf'>With an offline (cold storage) wallet</a>

#### <a href='#a_alt'>Forkcoin and Altcoin support</a>
* <a href='#a_bch'>Full support for Bcash (BCH) and Litecoin</a>
* <a href='#a_es'>Enhanced key/address generation support for Zcash (ZEC) and Monero (XMR)</a>
* <a href='#a_kg'>Key/address generation support for ETH, ETC and 144 Bitcoin-derived altcoins</a>

### <a name='a_i'>Preliminaries</a>

#### <a name='a_bb'>Before you begin</a>

Before you begin, note that the filenames, seed IDs and Bitcoin addresses used
in this primer are intentionally invalid and are for purposes of illustration
only.  As you perform the exercises, you'll naturally substitute real ones in
their place.

The up arrow (for repeating commands) and tab key (or Ctrl-I) (for completing
commands and filenames) will speed up your work at the command line greatly.

#### <a name='a_iv'>Invocation</a>

The MMGen wallet system is not a single program but a suite of lightweight
commands run from the command line.  MMGen's commands all begin, not
surprisingly, with 'mmgen'.  To see a list of available commands, type 'mmgen'
followed by the TAB key.  Every mmgen command has a help screen displaying
detailed usage and options information.  To view it, type the command name
followed by `--help`.  Note that most command options have long and short
versions.  For example, the `--help` option may be abbreviated to `-h`.
Exceptions are the options listed by `--longhelp`, which have no short versions.

MMGen commands are generally interactive, providing you with information and
prompting you for input.  The `--verbose` or `-v` option requests commands to be
more wordy, while the `--quiet` or `-q` option suppresses all but the most
essential information.  These options are available for all MMGen commands.  The
`--yes` option (available only for certain commands) suppresses even more
information and can be used to make some commands non-interactive and scriptable.

Certain options require parameters, such as the `--seed-len` option, for
instance, which takes a parameter of '128', '192' or '256'.  Commands may also
take optional or required arguments.  For example, `mmgen-addrgen` requires an
address or range of addresses as an argument.  Arguments must always follow
options on the command line.

Sample MMGen command invocations:

	$ mmgen-txcreate --help
	$ mmgen-addrgen --verbose 1-10
	$ mmgen-walletgen
	$ mmgen-walletgen --quiet --seed-len 128

#### <a name='a_cf'>Configuration file</a>

Just like Bitcoin Core, MMGen has its own data directory and configuration file.
The data directory is '.mmgen' in the user's home directory and the config
file is 'mmgen.cfg'.  The config file contains global settings which you may
wish to edit at some point to customize your installation.  These settings
include the maximum transaction fee; the user name, password and hostname
used for communicating with bitcoind; and a number of others.

#### <a name='a_ts'>Bob and Alice regtest mode</a>

If you just want to quickly try out MMGen, it's possible to perform all wallet
generation, wallet format conversion, address and key generation, and address
import operations on an offline computer with no blockchain and no bitcoin
balance.

If you want to practice creating, signing and sending transactions with real
bitcoins, however, you'll need a fully synced blockchain and some coins to play
with.  This involves an expenditure of both time and money.

Fortunately, there's an alternative: MMGen's **regtest mode** creates a virtual
network of two users, Bob and Alice, who transact with each other on a private
blockchain.  All of MMGen's functionality is available in regtest mode, making
it an ideal way to learn to use the MMGen wallet without risking real coins.
You may wish to pause here and perform the steps in the tutorial [MMGen Quick
Start with Regtest Mode][06] before continuing on.

### <a name='a_bo'>Basic Operations</a>

#### <a name='a_gw'>Generate an MMGen wallet (offline computer)</a>

*NOTE: MMGen supports a “default wallet” feature.  After generating your wallet,
you'll be prompted to make it your default.  If you answer 'y', the wallet will
be stored in your MMGen data directory and used for all future commands that
require a wallet or other seed source.*

*You may not want this feature if you plan to store your MMGen wallet in a
location other than your MMGen data directory.  Otherwise, it’s recommended,
as it frees you from having to type your wallet filename on the command line.*

*The following examples suppose that you’ve chosen to use a default wallet.
If you haven't, then you must include the path to a wallet file or other seed
source in all commands where a seed source is required.*

On your offline computer, generate an MMGen wallet:

	$ mmgen-walletgen
	...
	MMGen wallet written to file '/home/username/.mmgen/89ABCDEF-76543210[256,3].mmdat'

‘89ABCDEF’ is the Seed ID; ‘76543210’ is the Key ID. These are randomly
generated, so your IDs will of course be different than these.

The Seed ID never changes and is used to identify all keys/addresses generated
by this wallet.  Since it's your wallet's primary identifier, you should
memorize it visually.  The Key ID changes whenever the wallet’s password or hash
preset are changed and doesn't need to be memorized.

‘256’ is the seed length; ‘3’ is the scrypt hash preset.  These values are
configurable: type `mmgen-walletgen --help` for details.

Before moving any funds into your MMGen wallet, you should back it up in several
places and preferably on several media such as paper, flash memory or optical
disk.  You’re advised to use a passphrase with your wallet.  Otherwise, anyone
who gains physical access to one of your backups can easily steal your coins.
Don’t forget your passphrase.  If you do, the coins in your MMGen wallet are
gone forever.

Since the wallet is a small, humanly readable ASCII file, it can easily be
printed out on paper.

Another highly recommended way to back up your wallet is to generate a mnemonic
or seed file <a href='#a_ms'>as described below </a> and memorize it.  If you
have an average or better memory, you'll find memorizing your mnemonic to be
surprisingly easy. And the peace of mind that comes with knowing that your coins
are recoverable **even if you lose all your physical backups** can't be
overestimated.

#### <a name='a_ga'>Generate addresses (offline computer)</a>

Now generate ten Segwit addresses with your just-created wallet:

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

Note that the address range ‘1-10’ specified on the command line is included in
the resulting filename.

MMGen currently supports three address types: legacy uncompressed, compressed
P2PKH and Segwit, denoted by the respective code letters ‘L’, ‘C’ and ‘S’.  For
backwards compatibility, legacy addresses are generated by default.  To generate
compressed addresses, specify `--type=compressed` on the command line.

Legacy addresses are of interest only for existing pre-Segwit MMGen
installations, and it's unlikely you'll wish to generate them.  Compressed
addresses are the preferred choice for Bitcoin Cash (BCH) wallets, since Bitcoin
Cash doesn't support Segwit.

	# legacy uncompressed
	$ mmgen-addrgen 1-10
	...
	$ cat '89ABCDEF[1-10].addrs'
	89ABCDEF {
	  1   12GiSWo9zIQgkCmjAaLIrbPwXhKry2jHhj
	...

	# compressed P2PKH
	$ mmgen-addrgen --type=compressed 1-10
	...
	$ cat '89ABCDEF-C[1-10].addrs'
	89ABCDEF COMPRESSED {
	  1   13jbRxWjswXtaDzLBJDboMcIe6nLohFb9M
	...

Note that for non-legacy address types the code letter is included in the
filename.

To fund your MMGen wallet, first import the addresses into your tracking wallet
and then spend some BTC into any of them.  If you run out of addresses, generate
more.  To generate a hundred addresses you’d specify an address range of
‘1-100’.

Let’s say you’ve decided to spend some BTC into the first four addresses above.
Begin by importing these addresses into the tracking wallet on your online
machine so their balances will be visible.  For convenience of reference,
provide the addresses with labels.  We’ll use the labels ‘Donations’, ‘Storage
1’, ‘Storage 2’ and ‘Storage 3’.

Make a copy of the address file

	$ cp '89ABCDEF-S[1-10].addrs' my.addrs

and edit it using the text editor of your choice,

	$ nano my.addrs

adding labels to the addresses you’ve chosen to spend to:

	# My first MMGen addresses
	89ABCDEF SEGWIT {
	  1    36bNmyYISiptuvJG3X7MPwiiS4HYvD7ksE  Donations
	  2    3AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc  Storage 1
	  3    3HgYCsfqYzIg7LVVfDTp7gYJocJEiDAy6N  Storage 2
	  4    34Tu3z1tiexXDonNsFIkvzqutE5E3pTK8s  Storage 3
	  5    3PeI55vtp2bX2uKDkAAR2c6ekHNYe4Hcq7
	  6    3FEqfEsSILwXPfMvVvVuUovzTaaST62Mnf
	  7    3LTTzuhMqPLwQ4IGCwwugny6ZMtUQJSJ1
	  8    3F9495H8EJLb54wirgZkVgI47SP7M2RQWv
	  9    3JbrCyt7BdxRE9GX1N7GiEct8UnIjPmpYd
	  10   3H7vVTk4ejUbQXw45I6g5qvPBSe9bsjDqh
	}

Any line beginning with ‘#’ is a comment.  Comments may be placed at the ends
of lines as well.

Save the file, copy it onto a USB stick and transfer it to your online computer.

#### <a name='a_ia'>Import addresses (online computer)</a>

On your online computer, go to your bitcoind data directory and move any
existing 'wallet.dat' file out of harm’s way.  Start bitcoind and let it
generate a new 'wallet.dat'; this you’ll use as your tracking wallet.  Import
your ten addresses into the new tracking wallet with the command:

	$ mmgen-addrimport --batch my.addrs

These addresses will now be tracked: any BTC transferred to them will show up in
your listing of address balances.  Balances can be viewed using `mmgen-tool
listaddresses` (the `showempty` option requests the inclusion of addresses with
empty balances).

	$ mmgen-tool listaddresses showempty=1
	MMGenID       ADDRESS                             COMMENT    BALANCE
	89ABCDEF:S:1  36bNmyYISiptuvJG3X7MPwiiS4HYvD7ksE  Donations    0
	89ABCDEF:S:2  3AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc  Storage 1    0
	89ABCDEF:S:3  3HgYCsfqYzIg7LVVfDTp7gYJocJEiDAy6N  Storage 2    0
	89ABCDEF:S:4  34Tu3z1tiexXDonNsFIkvzqutE5E3pTK8s  Storage 3    0
	89ABCDEF:S:5  3PeI55vtp2bX2uKDkAAR2c6ekHNYe4Hcq7               0
	...
	TOTAL: 0 BTC

*While not covered in this introduction, note that it’s also possible to [import
ordinary Bitcoin addresses into your tracking wallet][01].  This allows you to
track and spend funds from another wallet using MMGen without having to go
through the network.  To use it, you must save the keys corresponding to the
addresses where the funds are stored in a separate file to use during signing.*

Note that each address has a unique ID (the ‘MMGen ID’) consisting of a Seed ID,
address type code letter, and index.  Addresses of different types may be
imported into the same tracking wallet; since they're generated from different
sub-seeds you needn't worry about key reuse.

Now that your addresses are being tracked, you may go ahead and send some BTC to
them over the Bitcoin network.  If you send 0.1, 0.2, 0.3 and 0.4 BTC
respectively, your address listing will look like this after the transactions
have confirmed:

	$ mmgen-tool listaddresses
	MMGenID       COMMENT    BALANCE
	89ABCDEF:S:1  Donations    0.1
	89ABCDEF:S:2  Storage 1    0.2
	89ABCDEF:S:3  Storage 2    0.3
	89ABCDEF:S:4  Storage 3    0.4
	TOTAL: 1 BTC

#### <a name='a_ct'>Create a transaction (online computer)</a>

Now that you have some BTC under MMGen’s control, you’re ready to create a
transaction.  Note that transactions are harmless until they’re signed and
broadcast to the network, so feel free to experiment and create transactions
with different combinations of inputs and outputs.  Of course, if you're using
testnet or regtest mode, then you risk nothing even when broadcasting
transactions.

To send 0.1 BTC to the a third-party address 3AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc,
for example, and send the change back to yourself at address 89ABCDEF:S:5, you’d
issue the following command:

	$ mmgen-txcreate 3AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc,0.1 89ABCDEF:S:5

'mmgen-txcreate' accepts either MMGen IDs or Bitcoin addresses as arguments.

NOTE: For backwards compatibility, legacy addresses may omit the code letter
from the MMGen ID.  Thus address ‘89ABCDEF:L:5’ may be expressed as
‘89ABCDEF:5’.  For other address types the code letter is mandatory.

To send 0.1 BTC to each of addresses 89ABCDEF:S:6 and 89ABCDEF:S:7 and return
the change to 89ABCDEF:S:8, you’d do this:

	$ mmgen-txcreate 89ABCDEF:S:6,0.1 89ABCDEF:S:7,0.1 89ABCDEF:S:8

As you can see, each send address is followed by a comma and the amount.  The
address with no amount is the change address.  All addresses belonging to your
seed in the above examples are already imported and tracked, so you’re OK.  If
you wanted to send to 89ABCDEF:S:11, you'd have to import it first.


Let’s go with the first of our two examples above.

Upon invocation, the 'mmgen-txcreate' command shows you a list of your
unspent outputs along with a menu allowing you to sort the outputs by four
criteria: transaction ID, address, amount and transaction age.  Your overall
balance in BTC appears at the top of the screen.  In our example, the display
will look something like this:

	UNSPENT OUTPUTS (sort order: Age)  Total BTC: 1
	 Num  TX id  Vout    Address                               Amt(BTC) Age(d)
	 1)   e9742b16... 5  3L3kxmi.. 89ABCDEF:S:1    Donations       0.1    1
	 2)   fa84d709... 6  3N4dSGj.. 89ABCDEF:S:2    Storage 1       0.2    1
	 3)   8dde8ef5... 6  3M1fVDc.. 89ABCDEF:S:3    Storage 1       0.3    1
	 4)   c76874c7... 0  3E8MFoC.. 89ABCDEF:S:4    Storage 3       0.4    1

	Sort options: [t]xid, [a]mount, a[d]dress, [A]ge, [r]everse, [M]mgen addr
	Display options: show [D]ays, [g]roup, show [m]mgen addr, r[e]draw screen
	'q'=quit view, 'p'=print to file, 'v'=pager view, 'w'=wide view, 'l'=add label:

After quitting the menu with 'q', you’ll see the following prompt:

	Enter a range or space-separated list of outputs to spend:

Here you must choose unspent outputs of sufficient value to cover the send
amount of 0.1 BTC, plus the transaction fee (for more on fees, see ‘Transaction
Fees’ under ‘Advanced Topics’ below).  Output #2 is worth 0.2 BTC, which is
sufficient, so we’ll choose that.  After several more prompts and confirmations,
your transaction will be saved:

	Transaction written to file 'FEDCBA[0.1].rawtx'

Note that the transaction filename consists of a unique MMGen Transaction ID
plus the non-change spend amount.

As you can see, MMGen gives you complete control over your transaction inputs
and change addresses.  This feature will be appreciated by privacy-conscious users.

#### <a name='a_sg'>Sign a transaction (offline computer)</a>

Now transfer the the raw transaction file to your offline computer and sign it
using your default wallet:

	$ mmgen-txsign FEDCBA[0.1].rawtx
	...
	Signed transaction written to file 'FEDCBA[0.1].sigtx'

Note that the signed transaction file has a new extension, '.sigtx'.

#### <a name='a_st'>Send a transaction (online computer)</a>

Now you’re ready for the final step: broadcasting the transaction to the
network.  Start bitcoind if it's not already running, and make sure your
blockchain is fully synced.  Then copy the signed transaction file to your
online computer and issue the command:

	$ mmgen-txsend FEDCBA[0.1].sigtx
	...
	Transaction sent: abcd1234....

Like all MMGen commands, 'mmgen-txsend' is interactive, so you’ll be prompted
before the transaction is actually broadcast.  If the send was successful, a
64-character hexadecimal Bitcoin Transaction ID will be displayed ('abcd1234...'
in our case).

Once the transaction is broadcast to the network and confirmed, your address
listing should look something like this:

	$ mmgen-tool listaddresses minconf=1
	MMGenID       COMMENT    BALANCE
	89ABCDEF:S:1  Donations    0.1
	89ABCDEF:S:3  Storage 2    0.3
	89ABCDEF:S:4  Storage 3    0.4
	89ABCDEF:S:5  Storage 1    0.0999
	TOTAL: 0.8999 BTC

Since you’ve sent 0.1 BTC to a third party, your balance has declined by 0.1 BTC
plus the tx fee of 0.0001 BTC.  To verify that your transaction’s received its
second, third and so on confirmations, increase `minconf` accordingly.

Congratulations!  You’ve now mastered the basics of MMGen!  To learn about some
of MMGen’s more advanced features, continue reading.

### <a name='a_af'>Additional Features</a>

#### <a name='a_ms'>Using the mnemonic, seed and hexseed formats</a>

Using your default wallet from the exercises above, generate a mnemonic:

	$ mmgen-walletconv -o words
	...
	Mnemonic data written to file '89ABCDEF.mmwords'

	$ cat 89ABCDEF.mmwords
	pleasure tumble spider laughter many stumble secret bother after search
	float absent path strong curtain savior worst suspend bright touch away
	dirty measure thorn

Since our seed is 256 bits long, the mnemonic contains 24 words.  128-bit and
192-bit seeds generate shorter mnemonics of 12 and 18 words, respectively.
Wallets with these seed lengths can be generated using the `--seed-len` option
to 'mmgen-walletgen'.

Though some consider 128 bits of entropy to provide adequate security for the
foreseeable future, it’s advisable to stick to the default 256-bit seed length.
You'll find that even a 24-word mnemonic is not difficult to memorize.

NOTE: MMGen mnemonics are generated from the Electrum wordlist, but using
ordinary base conversion instead of Electrum’s more complicated algorithm.

The mnemonic is a complete representation of your seed and may be used anywhere
where you’d use an MMGen wallet.  You can generate addresses with it just as you
do with a wallet:

	$ mmgen-addrgen --type=segwit 89ABCDEF.mmwords 1-10
	...
	Address data written to file '89ABCDEF-S[1-10].addrs'

You can use it to sign transactions:

	$ mmgen-txsign FEDCBA[0.1].rawtx 89ABCDEF.mmwords
	...
	Signed transaction written to file 'FEDCBA[0.1].sigtx'

The mnemonic can also be used to regenerate a lost wallet:

	$ mmgen-walletconv 89ABCDEF.mmwords
	...
	MMGen wallet written to file '89ABCDEF-01234567[256,3].mmdat'

Note that the regenerated wallet has a different Key ID but of course the same
Seed ID.

An alternative to mnemonics, seed files provide yet another way of representing
your seed.  They bear the extension '.mmseed' and are generated exactly the same
way as mnemonic files:

	$ mmgen-walletconv -o seed
	...
	Seed data written to file '89ABCDEF.mmseed'

They can be used just like mnemonics to regenerate a wallet:

	$ mmgen-walletconv 89ABCDEF.mmseed
	...
	MMGen wallet written to file '89ABCDEF-23456701[256,3].mmdat'

Here’s a sample seed file for a 256-bit seed:

	$ cat 8B7392ED.mmseed
	f4c84b C5ZT wWpT Jsoi wRVw 2dm9 Aftd WLb8 FggQ eC8h Szjd da9L

And for a 128-bit seed:

	$ cat 8E0DFB78.mmseed
	0fe02f XnyC NfPH piuW dQ2d nM47 VU

As you can see, seed files are short enough to be easily written out by hand or
memorized.  And their built-in checksum makes it easy to test your memory using
a simple Unix shell command:

	$ echo -n XnyC NfPH piuW dQ2d nM47 VU | tr -d ' '| sha256sum | cut -c 1-6
	0fe02f

Or you can do the same thing with 'mmgen-tool':

	$ mmgen-tool str2id6 'XnyC NfPH piuW dQ2d nM47 VU'
	0fe02f

Beginning with version 0.9.0, MMGen also supports seed files in hexadecimal
(hexseed) format.  Hexseed files are identical to seed files but encoded in
hexadecimal rather than base 58.  They bear the extension '.mmhex':

	$ cat FE3C6545.mmhex
	afc3fe 456d 7f5f 1c4b fe3b c916 b875 60ae 6a3e

You can easily check that a hexseed is correct by generating its Seed ID with
standard command-line tools:

	$ echo 456d 7f5f 1c4b fe3b c916 b875 60ae 6a3e | tr -d ' ' | xxd -r -p | sha256sum -b | xxd -r -p | sha256sum -b | cut -c 1-8
	fe3c6545

Mnemonics and hexseeds can be used to generate keys even without the MMGen
software, using basic command-line utilities, as explained in [this
tutorial][03].

#### <a name='a_ai'>Mnemonics, seeds and hexseeds: additional information</a>

All MMGen commands that take mnemonic, seed or hexseed data may receive the data
from a prompt instead of a file.  Just omit the file name and specify the input
format:

	$ mmgen-addrgen -i words 1-10
	...
	Choose a mnemonic length: 1) 12 words, 2) 18 words, 3) 24 words: 1
	Mnemonic length of 12 words chosen. OK? (Y/n): y
	Enter your 12-word mnemonic, hitting RETURN or SPACE after each word:
	Enter word #1:

MMGen prompts you for each of the mnemonic's words individually, checking it for
validity and reprompting if necessary.  What you type is not displayed on the
screen of course, being secret data.

The mnemonic prompt feature allows you to store and use your seed entirely in
your head if you wish, never recording it on a persistent physical medium.

With the `-S` option, MMGen commands may be requested to print wallet data to
screen instead of a file.  To safeguard against over-the-shoulder, Tempest and
other side-channel attacks, you’ll be prompted before this sensitive data is
actually displayed.  MMGen never prints decrypted private data to screen unless
you ask it to.

The output of any MMGen command may be written to a directory of your choice
using the `-d` option.  For example, on a Linux system you can use
`-d /dev/shm` to write keys and seeds to volatile memory instead of disk,
ensuring that no trace of secret data remains once your computer’s been
powered down.

#### <a name='a_ic'>Incognito wallets</a>

An incognito format wallet is indistinguishable from random data, allowing you
to hide your wallet at an offset within a random-data-filled file or partition.
Barring any inside knowledge, a potential attacker has no way of knowing where
the wallet is hidden, or whether the file or partition contains anything of
interest at all, for that matter.

An incognito wallet with a reasonably secure password could even be hidden on
unencrypted cloud storage.  Hiding your wallet at some offset in a 1 GB file
increases the difficulty of any attack by a factor of one billion, assuming
again that any potential attacker even knows or suspects you have an MMGen
wallet hidden there.

If you plan to store your incognito wallet in an insecure location such as cloud
storage, you’re advised to use a strong scrypt (hash) preset and a strong
password.  These can be changed using the 'mmgen-passchg' utility:

	$ mmgen-passchg -p 5 89ABCDEF-01234567[256,3].mmdat
	...
	Hash preset of wallet: '3'
	Enter old passphrase for MMGen wallet: <old weak passphrase>
	...
	Hash preset changed to '5'
	Enter new passphrase for MMGen wallet: <new strong passphrase>
	...
	MMGen wallet written to file '89ABCDEF-87654321[256,5].mmdat'

The scrypt preset is the numeral in the wallet filename following the seed
length.  As you can see, it’s now changed to '5'.  Now export your new toughened
wallet to incognito format, using the `-k` option to leave the passphrase
unchanged:

	$ mmgen-walletconv -k -o incog 89ABCDEF-87654321[256,5].mmdat
	...
	Reusing passphrase at user request
	...
	New Incog Wallet ID: ECA86420
	...
	Incognito data written to file '89ABCDEF-87654321-ECA86420[256,5].mmincog'

Incog wallets have a special identifier, the Incog ID, which can be used to
locate the wallet data if you’ve forgotten where you hid it (see the example
below).  Naturally, an attacker could use this ID to find the data too, so it
should be kept secret.

Incog wallets can also be output to hexadecimal format:

	$ mmgen-walletconv -k -o incox 89ABCDEF-87654321[256,5].mmdat
	...
	Hex incognito data written to file '89ABCDEF-87654321-CA86420E[256,5].mmincox'

	$ cat 89ABCDEF-87654321-1EE402F4[256,5].mmincox
	6772 edb2 10cf ad0d c7dd 484b cc7e 42e9
	4fe6 e07a 1ce2 da02 6da7 94e4 c068 57a8
	3706 c5ce 56e0 7590 e677 6c6e 750a d057
	b43a 21f9 82c7 6bd1 fe96 bad9 2d54 c4c0

Note that the Incog ID is different here: it’s generated from an init vector,
which is a different random number each time, making the incog data as a whole
different as well.  This allows you to store your incog data in multiple
public locations without having repeated ‘random’ wallet data give you away.

This data is ideally suited for a paper wallet that could potentially fall into
the wrong hands.

Your incognito wallet (whether hex or binary) can be used just like any other
MMGen wallet, mnemonic or seed file to generate addresses and sign transactions:

	$ mmgen-addrgen --type=segwit 89ABCDEF-87654321-CA86420E[256,5].mmincox 101-110
	...
	Generated 10 addresses
	Addresses written to file '89ABCDEF-S[101-110].addrs'

	$ mmgen-txsign FABCDE[0.3].rawtx 89ABCDEF-87654321-CA86420E[256,5].mmincox
	...
	Signed transaction written to file FABCDE[0.3].sigtx

##### <a name='a_hi'>Hidden incognito wallets</a>

With the `-o hincog` option, incognito wallet data can be created and hidden at
a specified offset in a file or partition in a single convenient operation, with
the random file being created automatically if necessary.  Here’s how you’d
create a 1GB file 'random.dat' and hide a wallet in it at offset 123456789:

	$ mmgen-walletconv -k -o hincog -J random.dat,123456789 89ABCDEF-87654321[256,5].mmdat
	...
	New Incog Wallet ID: ED1F2ACB
	...
	Requested file 'random.dat' does not exist.  Create? (Y/n): Y
	Enter file size: 1G
	...
	Data written to file 'random.dat' at offset 123456789

Your ‘random’ file can now be uploaded to a cloud storage service, for example,
or some other location on the Net, preferably non-public one (in a real-life
situation you will choose a less obvious offset than '123456789' though, won’t
you?).

Now let’s say at some point in the future you download this file to recover
your wallet and realize you’ve forgotten the offset where the data is hidden.
If you’ve saved your Incog ID, you’re in luck:

	$ mmgen-tool find_incog_data random.dat ED1F2ACB
	...
	Incog data for ID ED1F2ACB found at offset 123456789

The search process can be slow, so patience is required.  In addition, on
large files ‘false positives’ are a distinct possibility, in which case you’ll
need to use the `keep_searching=1` parameter to keep going until you find the
real offset.

Hidden incog wallets are nearly as convenient to use as ordinary ones.
Generating ten addresses with your hidden incog data is as easy as this:

	$ mmgen-addrgen -H random.dat,123456789 101-110

Transaction signing uses the same syntax:

	$ mmgen-txsign -H random.dat,123456789 ABCDEF[0.1].rawtx
	...
	Signed transaction written to file 'ABCDEF[0.1].sigtx'

### <a name='a_at'>Advanced Topics</a>

#### <a name='a_hw'>Hot wallets and key-address files</a>

Chances are you'll want to use MMGen not only for cold storage but for
day-to-day transactions too.  For this you'll need to place a portion of your
funds in a “hot wallet” on your online computer.  With hot wallet funds you
can use the command `mmgen-txdo` to quickly create, sign and send transactions
in one operation.

There are two hot wallet strategies you can use.  The first is to generate a
separate MMGen wallet on your online computer for use as the hot wallet.  The
advantage of this is convenience: you won't have to specify a wallet or seed
source on the command line.  In addition, your hot wallet and cold wallet funds
will be easily distinguishable in your tracking wallet by their different Seed
IDs.  The drawback of this strategy is that you now have two seeds that need
backing up or memorizing.

The other strategy, which avoids this drawback, is to partition your cold wallet
by mentally setting aside “hot” and “cold” address ranges.  For example, you
might choose to reserve all addresses in the range 1-1000 for cold storage and
everything above that for your hot wallet.

The next step is to create a key-address file for a sufficient number of “hot”
addresses to cover your day-to-day transaction needs for the foreseeable future.
A key-address file is just like an address file except that it contains keys as
well as addresses, thus functioning as a hot wallet for a range of addresses.
Assuming your hot address range begins at 1001, you could start by creating a
key-address file for a hundred hot addresses like this:

	$ mmgen-keygen --type=segwit 1001-1100
	...
	Secret keys written to file '89ABCDEF-S[1001-1100].akeys.mmenc'

`mmgen-keygen` prompts you for a password to encrypt the key-address file with.
This is a wise precaution, as it provides at least some security for keys that
will be stored on an online machine.

Now copy the key-address file to your online machine and import the addresses
into your tracking wallet:

	$ mmgen-addrimport --batch --keyaddr-file '89ABCDEF-S[1001-1100].akeys.mmenc'

After funding your hot wallet by spending into some addresses in this range you
can do quickie transactions with these funds using the `mmgen-txdo` command:

	$ mmgen-txdo -M '89ABCDEF-S[1001-1100].akeys.mmenc' 1AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc,0.1 89ABCDEF:S:1010
	...
	Transaction sent: dcea1357....

The `--mmgen-keys-from-file` or `-M` option is required when using a key-address
file in place of a default wallet.  Note that your change address
89ABCDEF:S:1010 is within the range covered by the key-address file, so your
change funds will remain “hot spendable”.

Using `mmgen-txdo` with a default online hot wallet is even simpler.  For a hot
wallet with Seed ID 0FDE89AB, for instance, creating and sending a transaction
would look like this:

	$ mmgen-txdo 1AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc,0.1 0FDE89AB:S:10


#### <a name='a_fee'>Transaction Fees</a>

MMGen gives you several options for dealing with transaction fees.

Firstly, and most simply, you may do nothing, in which case MMGen will calculate
the fee automatically using bitcoind’s 'estimatefee' RPC call.  You can adjust
the estimated fee by any factor using the `--tx-fee-adj` option, a handy feature
when you need transactions to confirm a bit more quickly.  MMGen has no default
fee, so if network fee estimation fails for any reason, you'll be prompted to
enter the fee manually.

Secondly, you may specify the fee as an absolute BTC amount (a decimal number).
This can be done either on the command line or at the interactive prompt when
creating transactions with `mmgen-txcreate`, `mmgen-txdo` or `mmgen-txbump`.

Thirdly, instead of using an absolute BTC amount, you may specify the fee in
satoshis per byte and let MMGen calculate the fee based on the transaction size.
This also works both on the command line and at the interactive prompt.  The
satoshis-per-byte specification is an integer followed by the letter 's'.  A fee
of 90 satoshis per byte is thus represented as '90s'.

MMGen has a hard maximum fee (currently 0.003 BTC) which is alterable only in the
config file.  Thus MMGen will never create or broadcast any transaction with a
mistakenly or dangerously high fee unless you expressly permit it to.

#### <a name='a_rbf'>BIP 125 replace-by-fee (RBF) transactions</a>

As of version 0.9.1, MMGen supports creating replaceable and replacement
transactions in accordance with the BIP 125 replace-by-fee (RBF) specification.

To make your transactions replaceable, just specify the `--rbf` option when
creating them with `mmgen-txcreate` or `mmgen-txdo`.

Version 0.9.1 also introduces `mmgen-txbump`, a convenient command for quickly
creating replacement transactions from existing replaceable ones.
`mmgen-txbump` can create, sign and send transactions in a single operation if
desired.

Continuing the examples from our primer above, we'll examine two RBF scenarios,
one for a hot wallet and one for a cold storage wallet.  In the first scenario,
initial and replacement transactions will be created, signed and sent in one
operation.  In the second, a batch of replacement transactions with
incrementally increasing fees will created online and then signed offline.

#### <a name='a_rbf_onl'>With an online (hot) wallet</a>

Create, sign and send a BIP 125 replaceable transaction with a fee of 50
satoshis per byte:

	$ mmgen-txdo --rbf --tx-fee 50s 1AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc,0.1 0FDE89AB:S:5
	...
	Signed transaction written to file 'FEDCBB[0.1,50].sigtx'
	...
	Transaction sent: dcba4321....

Here you've sent 0.1 BTC to a third-party address and the change back to
yourself at address #5 of your default hot wallet with Seed ID 0FDE89AB.

Note that the fee is shown in the filename after the send amount.  The presence
of the fee in the filename identifies the transaction as replaceable.

If the transaction fails to confirm in your desired timeframe, then create, sign
and send a replacement transaction with a higher fee, say 100 satoshis per byte:

	$ mmgen-txbump --send --tx-fee 100s --output-to-reduce c 'FEDCBB[0.1,50].sigtx'
	...
	Signed transaction written to file 'DAE123[0.1,100].sigtx'
	...
	Transaction sent: eef01357....

The `--send` switch instructs `mmgen-txbump` to sign and send the transaction
after creating it.  The `--output-to-reduce` switch with an argument of 'c'
requests that the increased fee be deducted from the change ('c') output, which
is usually what is desired.  If you want it taken from some other output,
identify the output by number.  Note that the resulting replacement transaction
has a different identifier, since it's a new transaction.

If this transaction also fails to confirm, then repeat the above step as many
times as necessary to get a confirmation, increasing the fee each time.  The
only thing you have to modify with each iteration is the argument to `--tx-fee`.
To reduce your typing even further, use the `--yes` switch to skip all
non-essential prompts.

Note that if you're using a key-address file instead of a default hot wallet,
you'll need to supply it on the command line as a parameter to the `-M` option.

#### <a name='a_rbf_onf'>With an offline (cold storage) wallet</a>

To achieve the same result as in the above example using a cold wallet, just
create the initial transaction with `mmgen-txcreate` instead of `mmgen-txdo`:

	$ mmgen-txcreate --rbf --tx-fee 50s 1AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc,0.1 89ABCDEF:S:5
	...
	Transaction written to file 'FEDCBC[0.1,50].rawtx'

Now create a series of transactions with incrementally increasing fees for
offline signing:

	$ mmgen-txbump --tx-fee 100s --output-to-reduce c 'FEDCBC[0.1,50].rawtx'
	$ mmgen-txbump --tx-fee 150s --output-to-reduce c 'FEDCBC[0.1,50].rawtx'
	$ mmgen-txbump --tx-fee 200s --output-to-reduce c 'FEDCBC[0.1,50].rawtx'

To speed things up, add the `--yes` switch to make `mmgen-txbump` completely
non-interactive.

The result will be four raw transaction files with increasing fees, like this:

	FEDCBC[0.1,50].rawtx
	3EBB00[0.1,100].rawtx
	124FFF[0.1,150].rawtx
	73DABB[0.1,200].rawtx

Copy the files to an empty folder, transfer the folder to your offline machine and batch sign them:

	$ mmgen-txsign -d my_folder --yes my_folder/*.rawtx

Then copy the signed transaction files back to your online machine and broadcast
them in turn until you get a confirmation:

	$ mmgen-txsend FEDCBC[0.1,50].sigtx   # ...if this doesn't confirm, then
	$ mmgen-txsend 3EBB00[0.1,100].sigtx  # ...if this doesn't confirm, then
	$ mmgen-txsend 124FFF[0.1,150].sigtx  # ...if this doesn't confirm, then
	$ mmgen-txsend 73DABB[0.1,200].sigtx

### <a name='a_alt'>Forkcoin and Altcoin support</a>

#### <a name='a_bch'>Full support for Bcash (BCH) and Litecoin</a>

Bcash and Litecoin are fully supported by MMGen, on the same level as Bitcoin.

To use MMGen with Bcash or Litecoin, first make sure the respective Bitcoin ABC
and Litecoin daemons are properly installed ([source][si])([binaries][bi]),
[running][p8] and synced.

MMGen requires that the bitcoin-abc daemon be listening on non-standard
[RPC port 8442][p8].

Then just add the `--coin=bch` or `--coin=ltc` option to all your MMGen
commands.  It's that simple!

#### <a name='a_es'>Enhanced key/address generation support for Zcash (ZEC) and Monero (XMR)</a>

MMGen's enhanced key/address generation support for Zcash and Monero includes
**Zcash z-addresses** and automated Monero wallet creation.

Generate ten Zcash z-address key/address pairs from your default wallet:

	$ mmgen-keygen --coin=zec --type=zcash_z 1-10

The addresses' view keys are included in the file as well.

NOTE: Since your key/address file will probably be used on an online computer,
you should encrypt it with a good password when prompted to do so. The file can
decrypted as required using the `mmgen-tool decrypt` command.  If you choose a
non-standard Scrypt hash preset, take care to remember it.

To generate Zcash t-addresses, just omit the `--type` argument:

	$ mmgen-keygen --coin=zec 1-10

Generate ten Monero address pairs from your default wallet:

	$ mmgen-keygen --coin=xmr 1-10

In addition to spend and view keys, Monero key/address files also include a
wallet password for each address (the password is the double Sha256 of the spend
key, truncated to 16 bytes).  This allows you to easily generate wallets for
each address by running the following command

	$ monero-wallet-cli --generate-from-spend-key MyMoneroWallet

and pasting in the key and password data when prompted.  Monerod must be
running and `monero-wallet-cli` be located in your executable path.

This process is completely automated by the `mmgen-tool` utility:

	$ mmgen-tool keyaddrlist2monerowallet *XMR*.akeys.mmenc

This will generate Monero wallets for each key/address pair in the key/address
file and encrypt them with their respective passwords.  No user interaction is
required.  By default, wallets are synced to the current block height, as
they're assumed to be empty.  This behavior can be overridden:

	$ mmgen-tool keyaddrlist2monerowallet *XMR*.akeys.mmenc blockheight=123456

#### <a name='a_kg'>Key/address generation support for ETH, ETC and 144 Bitcoin-derived altcoins</a>

To generate key/address pairs for these coins, just specify the coin's symbol
with the `--coin` argument:

	# For DASH:
	$ mmgen-keygen --coin=dash 1-10
	# For Emercoin:
	$ mmgen-keygen --coin=emc 1-10

If it's just the addresses you want, then use `mmgen-addrgen` instead:

	$ mmgen-addrgen --coin=dash 1-10

Regarding encryption of key/address files, see the note for Zcash above.

Here's a complete list of supported altcoins as of this writing:

	2give,42,611,ac,acoin,alf,anc,apex,arco,arg,aur,bcf,blk,bmc,bqc,bsty,btcd,
	btq,bucks,cann,cash,cat,cbx,ccn,cdn,chc,clam,con,cpc,crps,csh,dash,dcr,dfc,
	dgb,dgc,doge,doged,dope,dvc,efl,emc,emd,enrg,esp,fai,fc2,fibre,fjc,flo,flt,
	fst,ftc,gcr,good,grc,gun,ham,html5,hyp,icash,infx,inpay,ipc,jbs,judge,lana,
	lat,ldoge,lmc,ltc,mars,mcar,mec,mint,mobi,mona,moon,mrs,mue,mxt,myr,myriad,
	mzc,neos,neva,nka,nlg,nmc,nto,nvc,ok,omc,omni,onion,onx,part,pink,pivx,pkb,
	pnd,pot,ppc,ptc,pxc,qrk,rain,rbt,rby,rdd,ric,sdc,sib,smly,song,spr,start,
	sys,taj,tit,tpc,trc,ttc,tx,uno,via,vpn,vtc,wash,wdc,wisc,wkc,wsx,xcn,xgb,
	xmg,xpm,xpoke,xred,xst,xvc,zet,zlq,zoom,zrc,bch,etc,eth,ltc,xmr,zec

Note that support for these coins is EXPERIMENTAL.  Many of them have received
only minimal testing, or no testing at all.  At startup you'll be informed of
the level of your selected coin's support reliability as deemed by the MMGen
Project.

[01]: https://github.com/mmgen/mmgen/wiki/Tracking-and-spending-ordinary-Bitcoin-addresses
[02]: https://tpfaucet.appspot.com
[03]: Recovering-Your-Keys-Without-the-MMGen-Software
[04]: https://bitcoin.org/en/developer-examples#testnet
[05]: https://bitcoin.org/en/developer-examples#regtest-mode
[06]: https://github.com/mmgen/mmgen/wiki/MMGen-Quick-Start-with-Regtest-Mode
[si]: Install-Bitcoind-from-Source-on-Debian-or-Ubuntu-Linux
[bi]: Install-Bitcoind#a_d
[p8]: Install-Bitcoind#a_r
