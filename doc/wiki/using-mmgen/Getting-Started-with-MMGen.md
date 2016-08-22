## Table of Contents

#### <a href=#01>Basic Operations</a>
* <a href=#02>Generate a wallet</a>
* <a href=#03>Generate addresses</a>
* <a href=#04>Import addresses</a>
* <a href=#05>Create a transaction</a>
* <a href=#06>Sign a transaction</a>
* <a href=#07>Send a transaction</a>

#### <a href=#10>Additional Features</a>
* <a href=#11>Using the mnemonic and seed features</a>
* <a href=#12>Mnemonics and seeds: additional information</a>
* <a href=#13>Incognito wallets</a>
	* <a href=#13a>Hidden incognito wallets</a>

The following primer presupposes you have MMGen installed on two computers, one
offline and one online.  However, if you have an online computer and a few
Bitcoin addresses with small balances, it’s perfectly possible to perform the
operations described below on a single online machine.

For those who just want to experiment with MMGen: all wallet generation, wallet
format conversion, address and key generation, and address import operations can
be performed on either an online or offline computer with an empty blockchain
and no Bitcoin balance.

Note that all the filenames, seed IDs, Bitcoin addresses and so forth used in
this primer are fake.  Substitute real ones in their place as you go.  The up
arrow (for repeating commands) and tab key (or Ctrl-I) (for completing commands
and filenames) will speed up your work at the command line greatly.

### <a name=01>Basic Operations</a>

#### <a name=02>Generate a wallet (offline computer):</a>

On your offline computer, generate a wallet:

		$ mmgen-walletgen
		...
		MMGen wallet written to file '89ABCDEF-76543210[256,3].mmdat'

‘89ABCDEF’ is the Seed ID; ‘76543210’ is the Key ID. These are randomly
generated, so your IDs will of course be different than these.

The Seed ID never changes and is used to identify all keys/addresses generated
by this wallet.  You should make a note of it.  The Key ID changes whenever the
wallet’s password or hash preset are changed and is less important.

‘256’ is the seed length; ‘3’ is the scrypt hash preset.  These values are
configurable: type `mmgen-walletgen --help` for details.

Before moving any funds into your MMGen wallet, you should back it up in several
places and preferably on several media such as paper, flash memory or a CD-ROM.
You’re advised to use a passphrase with your wallet.  Otherwise, anyone who
gains physical access to one of your backups can easily steal your coins.  Don’t
forget your passphrase.  If you do, the coins in your MMGen wallet are gone
forever.

Since the wallet is a small, humanly readable ASCII file, it can easily be
printed out on paper.  It can also be exported to more compact forms, the seed
file and mnemonic (discussed below).  These formats are short enough to be
written out by hand or memorized.

#### <a name=03>Generate addresses (offline computer):</a>

Now generate ten addresses with your just-created wallet:

		$ mmgen-addrgen 89ABCDEF-76543210[256,3].mmdat 1-10
		...
		Addresses written to file '89ABCDEF[1-10].addrs'

		$ cat '89ABCDEF[1-10].addrs'
		89ABCDEF {
		  1    16bNmyYISiptuvJG3X7MPwiiS4HYvD7ksE
		  2    1AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc
		  3    1HgYCsfqYzIg7LVVfDTp7gYJocJEiDAy6N
		  4    14Tu3z1tiexXDonNsFIkvzqutE5E3pTK8s
		  5    1PeI55vtp2bX2uKDkAAR2c6ekHNYe4Hcq7
		  6    1FEqfEsSILwXPfMvVvVuUovzTaaST62Mnf
		  7    1LTTzuhMqPLwQ4IGCwwugny6ZMtUQJSJ1
		  8    1F9495H8EJLb54wirgZkVgI47SP7M2RQWv
		  9    1JbrCyt7BdxRE9GX1N7GiEct8UnIjPmpYd
		  10   1H7vVTk4ejUbQXw45I6g5qvPBSe9bsjDqh
		}

Note that the address range ‘1-10’ specified on the command line is included in
the resulting filename.  MMGen addresses consist of the Seed ID followed by ‘:’
and an index.  In this example, ‘89ABCDEF:1’ represents the Bitcoin address
‘16bNmy...’, ‘89ABCDEF:2’ represents ‘1AmkUx...’ and so forth.

To begin moving your Bitcoin holdings into your MMGen wallet, just spend into
any of these addresses.  If you run out of addresses, generate more.  To
generate a hundred addresses, for example, you’d specify an address range of ‘1-100’.

Let’s say you’ve decided to spend some BTC into the first four addresses above.
Before doing so, you must import these addresses into the tracking wallet on
your online machine so their balances will be visible.  For convenience
of reference, provide the addresses with labels.  We’ll use the labels
‘Donations’, ‘Storage 1’, ‘Storage 2’ and ‘Storage 3’.

Make a copy of the address file

		$ cp '89ABCDEF[1-10].addrs' my.addrs

and edit it using the text editor of your choice,

		$ nano my.addrs

adding labels to the addresses you’ve chosen to spend to:

		# My first MMGen addresses
		89ABCDEF {
		  1    16bNmyYISiptuvJG3X7MPwiiS4HYvD7ksE  Donations
		  2    1AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc  Storage 1
		  3    1HgYCsfqYzIg7LVVfDTp7gYJocJEiDAy6N  Storage 2
		  4    14Tu3z1tiexXDonNsFIkvzqutE5E3pTK8s  Storage 3
		  5    1PeI55vtp2bX2uKDkAAR2c6ekHNYe4Hcq7
		  6    1FEqfEsSILwXPfMvVvVuUovzTaaST62Mnf
		  7    1LTTzuhMqPLwQ4IGCwwugny6ZMtUQJSJ1
		  8    1F9495H8EJLb54wirgZkVgI47SP7M2RQWv
		  9    1JbrCyt7BdxRE9GX1N7GiEct8UnIjPmpYd
		  10   1H7vVTk4ejUbQXw45I6g5qvPBSe9bsjDqh
		}

Any line beginning with ‘#’ is a comment.  Comments may be placed at the ends
of lines as well.

Save the file, copy it onto a USB stick and transfer it to your online computer.

#### <a name=04>Import addresses (online computer):</a>

On your online computer, go to your bitcoind data directory and move any
existing 'wallet.dat' file out of harm’s way.  Start bitcoind and let it
generate a new 'wallet.dat', which you’ll use as your tracking wallet.
Import your ten addresses into the new tracking wallet with the command:

		$ mmgen-addrimport --batch my.addrs

These addresses will now be tracked: any BTC transferred to them will show up in
your listing of address balances.  Balances can be viewed using `mmgen-tool
listaddresses` (the `showempty` option requests the inclusion of addresses with
empty balances, and `showbtcaddrs` causes Bitcoin addresses to be displayed
also).

		$ mmgen-tool listaddresses showempty=1 showbtcaddrs=1
		MMGenID     ADDRESS                             COMMENT    BALANCE
		89ABCDEF:1  16bNmyYISiptuvJG3X7MPwiiS4HYvD7ksE  Donations    0
		89ABCDEF:2  1AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc  Storage 1    0
		89ABCDEF:3  1HgYCsfqYzIg7LVVfDTp7gYJocJEiDAy6N  Storage 2    0
		89ABCDEF:4  14Tu3z1tiexXDonNsFIkvzqutE5E3pTK8s  Storage 3    0
		89ABCDEF:5  1PeI55vtp2bX2uKDkAAR2c6ekHNYe4Hcq7               0
		...
		TOTAL: 0 BTC

Note that it’s also possible to [track ordinary Bitcoin addresses with your
tracking wallet][1].  This is not recommended, however, as you must save their
corresponding keys in a key list in order to spend them.  Avoiding the use of
keys is precisely the reason MMGen was created!

Now that your addresses are being tracked, you may go ahead and send some BTC to
them.  If you send 0.1, 0.2, 0.3 and 0.4 BTC respectively, for example, your
address listing will look something like this after the transactions have been
confirmed:

		$ mmgen-tool listaddresses
		MMGenID     COMMENT    BALANCE
		89ABCDEF:1  Donations    0.1
		89ABCDEF:2  Storage 1    0.2
		89ABCDEF:3  Storage 2    0.3
		89ABCDEF:4  Storage 3    0.4
		TOTAL: 1 BTC

#### <a name=05>Create a transaction (online computer):</a>

Now that you have some BTC under MMGen’s control, you’re ready to create a
transaction.  Note that transactions are harmless until they’re signed and
broadcast to the network, so feel free to experiment and create transactions
with different combinations of inputs and outputs.

To send 0.1 BTC to the a third-party address 1AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc,
for example, and send the change back to yourself at address 89ABCDEF:5, you’d
issue the following command:

		$ mmgen-txcreate 1AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc,0.1 89ABCDEF:5

Note that 'mmgen-txcreate' accepts either MMGen IDs or Bitcoin addresses as
arguments.

To send 0.1 BTC to each of your addresses 89ABCDEF:6 and 89ABCDEF:7 and return the
change to 89ABCDEF:8, you’d do this:

		$ mmgen-txcreate 89ABCDEF:6,0.1 89ABCDEF:7,0.1 89ABCDEF:8

As you can see, each send address is followed by a comma and the amount.  The
address with no amount is the change address.  All addresses belonging to your
seed in the above examples are already imported and tracked, so you’re OK.  If
you wanted to send to 89ABCDEF:11 instead, you'd have to import it first.


Let’s go with the first of our two examples above.

Upon invocation, the 'mmgen-txcreate' command shows you a list of your
unspent outputs along with a menu allowing you to sort the outputs by four
criteria: transaction ID, address, amount and transaction age.  Your overall
balance in BTC appears at the top of the screen.  In our example, the display
will look something like this:

		UNSPENT OUTPUTS (sort order: Age)  Total BTC: 1
		 Num  TX id  Vout    Address                               Amt(BTC) Age(d)
		 1)   e9742b16... 5  1L3kxmi.. 89ABCDEF:1    Donations       0.1    1
		 2)   fa84d709... 6  1N4dSGj.. 89ABCDEF:2    Storage 1       0.2    1
		 3)   8dde8ef5... 6  1M1fVDc.. 89ABCDEF:3    Storage 1       0.3    1
		 4)   c76874c7... 0  1E8MFoC.. 89ABCDEF:4    Storage 3       0.4    1

		Sort options: [t]xid, [a]mount, a[d]dress, [A]ge, [r]everse, [M]mgen addr
		Display options: show [D]ays, [g]roup, show [m]mgen addr, r[e]draw screen
		'q'=quit view, 'p'=print to file, 'v'=pager view, 'w'=wide view, 'l'=add label:

After quitting the menu with 'q', you’ll see the following prompt:

		Enter a range or space-separated list of outputs to spend:

Here you must choose outputs of sufficient value to cover the send amount of 0.1
BTC, plus the transaction fee.  By the way, MMGen calculates fees automatically
using bitcoind’s 'estimatefee' RPC call, which makes things very convenient.  If
you want to increase the fee a bit for speedier confirmation, use the
`--tx-fee-adj` option.  Type `mmgen-txcreate --help` for details.

Output #2 is worth 0.2 BTC, which is sufficient, so let’s choose it.  After
several more prompts and confirmations, your transaction will be saved:

		Transaction written to file 'FEDCBA[0.1].rawtx'

Note that the transaction filename consists of a unique ID plus the spend
amount.

As you can see, MMGen gives you complete control over your transaction inputs
and change addresses.  This feature will be appreciated by privacy-conscious users.

#### <a name=06>Sign a transaction (offline computer):</a>

Now transfer the the raw transaction file to your offline computer and sign it
using your wallet:

		$ mmgen-txsign FEDCBA[0.1].rawtx 89ABCDEF-76543210[256,3].mmdat
		...
		Signed transaction written to file 'FEDCBA[0.1].sigtx'

Note that the signed transaction file bears the extension '.sigtx'.

#### <a name=07>Send a transaction (online computer):</a>

Now you’re ready for the final step: broadcasting the transaction to the
network.  Copy the signed transaction file to your online computer, start
bitcoind if necessary, and issue the command:

		$ mmgen-txsend FEDCBA[0.1].sigtx

Like all MMGen commands, 'mmgen-txsend' is interactive, so you’ll be prompted
before the transaction is actually sent.

Once the transaction is broadcast to the network and confirmed, your address
listing should look something like this:

		$ mmgen-tool listaddresses minconf=1
		MMGenID     COMMENT    BALANCE
		89ABCDEF:1  Donations    0.1
		89ABCDEF:3  Storage 2    0.3
		89ABCDEF:4  Storage 3    0.4
		89ABCDEF:5  Storage 1    0.0999
		TOTAL: 0.8999 BTC

Since you’ve sent 0.1 BTC to a third party, your balance has declined by 0.1 BTC
plus the tx fee of 0.0001 BTC.  To verify that your transaction’s received its
second, third and so on confirmations, increase `minconf` accordingly.

Congratulations!  You’ve now mastered the basics of MMGen!

Some of MMGen’s more advanced features are discussed below.  Others are
documented in the help screens of the individual MMGen commands: display these
by invoking the desired command with the `-h` or `--help` switch.

### <a name=10>Additional Features</a>

#### <a name=11>Using the mnemonic and seed features:</a>

Continuing our example above, generate a mnemonic from the wallet:

		$ mmgen-walletconv -o words '89ABCDEF-76543210[256,3].mmdat'
		...
		Mnemonic data written to file '89ABCDEF.mmwords'

		$ cat 89ABCDEF.mmwords
		pleasure tumble spider laughter many stumble secret bother after search
		float absent path strong curtain savior worst suspend bright touch away
		dirty measure thorn

Note: a 128- or 192-bit seed will generate a shorter mnemonic of 12 or 18
words.  You may generate a wallet with these seed lengths using the `-l`
option to 'mmgen-walletgen'.

Though some consider 128 bits of entropy to provide adequate security for the
foreseeable future, it’s advisable to stick to the default 256-bit seed length
if you’re not planning to use the mnemonic feature.

NOTE: MMGen mnemonics are generated from the Electrum wordlist, but using
ordinary base conversion instead of Electrum’s more complicated algorithm.

The mnemonic file may be used any place you’d use a MMGen wallet with the same
Seed ID.  You can generate ten addresses with it just as you did with the
wallet, for example:

		$ mmgen-addrgen 89ABCDEF.mmwords 1-10
		...
		Address data written to file '89ABCDEF[1-10].addrs'

The resulting address file will be identical to one generated by any wallet with
Seed ID '89ABCDEF'.

The mnemonic can be used to regenerate a lost wallet:

		$ mmgen-walletconv 89ABCDEF.mmwords
		...
		MMGen wallet written to file '89ABCDEF-01234567[256,3].mmdat'

Note that the regenerated wallet has a different Key ID but of course the same
Seed ID.

Seed files bear the extension '.mmseed' and are generated and used exactly
the same way as mnemonic files:

		$ mmgen-walletconv -o seed '89ABCDEF-76543210[256,3].mmdat'
		...
		Seed data written to file '89ABCDEF.mmseed'

And they can also be used to regenerate a wallet:

		$ mmgen-walletconv 89ABCDEF.mmseed
		...
		MMGen wallet written to file '89ABCDEF-23456701[256,3].mmdat'

Here’s a sample seed file for a 256-bit wallet:

		$ cat 8B7392ED.mmseed
		f4c84b C5ZT wWpT Jsoi wRVw 2dm9 Aftd WLb8 FggQ eC8h Szjd da9L

And for a 128-bit wallet:

		$ cat 8E0DFB78.mmseed
		0fe02f XnyC NfPH piuW dQ2d nM47 VU

As you can see, seed files are short enough to be easily written out by hand or
even memorized.  And their built-in checksum makes it easy to test your memory
using a simple Unix shell command:

		$ echo -n XnyC NfPH piuW dQ2d nM47 VU | tr -d ' '| sha256sum | cut -c 1-6
		0fe02f

Or you can do the same thing with 'mmgen-tool':

		$ mmgen-tool str2id6 'XnyC NfPH piuW dQ2d nM47 VU'
		0fe02f

#### <a name=12>Mnemonics and seeds: additional information</a>

MMGen commands that take mnemonic and seed data may receive the data from a
prompt instead of a file.  Just omit the file name and specify the input format:

		$ mmgen-walletconv -i words
		...
		Enter mnemonic data: <type or paste your mnemonic here>

With the `-S` option, MMGen commands may be requested to print wallet data to
screen instead of a file.  To safeguard against over-the-shoulder, Van Eck
phreaking and other side-channel attacks, you’ll be prompted before this
sensitive data is actually displayed.  MMGen never prints unencrypted private
data to screen by default.

The output of any MMGen command may be written to a directory of your choice
using the `-d` option.  For example, on a Linux system you can use
`-d /dev/shm` to write keys and seeds to volatile memory instead of disk,
ensuring that no trace of this sensitive data remains once your computer’s been
powered down.

#### <a name=13><a name=incog>Incognito wallets</a>

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

		$ mmgen-addrgen 89ABCDEF-87654321-CA86420E[256,5].mmincox 101-110
		...
		Generated 10 addresses
		Addresses written to file '89ABCDEF[101-110].addrs'

		$ mmgen-txsign FABCDE[0.3].rawtx 89ABCDEF-87654321-CA86420E[256,5].mmincox
		...
		Signed transaction written to file FABCDE[0.3].sigtx

##### <a name=13a><a name=incog>Hidden incognito wallets</a>

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
or some other, preferably non-public, location on the Net (in a real-life
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

[1]: https://github.com/mmgen/mmgen/wiki/Tracking-and-spending-ordinary-Bitcoin-addresses
