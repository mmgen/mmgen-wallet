#  MMGen = Multi-Mode GENerator
## a Bitcoin cold storage solution for the command line

NOTE: Parts of this README are now **out of date**.  In particular, the
new transaction scripts automate the process of offline signing, so that
your private keys never touch your online machine.	An updated README is
on the way.  For the time being, consult the `--help` option of the
`mmgen-tx*` scripts.

NOTE: For the time being, MMGen should be considered experimental software.
Downloading and testing it out is easy, risk-free and encouraged.
However, spending significant amounts of BTC into your mmgen-generated
addresses is done at your own risk.

### Features:

> Like all deterministic wallets, MMGen can generate a virtually
> unlimited number of address/key pairs from a single seed, allowing you
> to maintain and track a large number of addresses with balances.  Your
> wallet never changes (unless you change the password), so you need
> back it up only once.

> The "master key", the seed providing access to all your Bitcoins, can
> be stored in four different ways:

>> 1) in an encrypted wallet (the AES 256 key is generated from your
>> password using the crack-resistant scrypt hash function.  The
>> wallet's password and hash strength can be changed);

>> 2) in a one-line, human-readable seed file (unencrypted);

>> 3) as an Electrum-like mnemonic of 12, 18 or 24 words; or

>> 4) as a brainwallet password (this option is recommended for expert
>> users only).

> Furthermore, these methods can all be combined.  If you forget your
> mnemonic, for example, you can regenerate it and your keys from a
> stored wallet or seed.  Correspondingly, a lost wallet or seed can be
> recovered from the mnemonic.

> The wallet and seed files are in a simple, ASCII-based format suitable
> for printing or even writing out by hand.	Built-in checksums are used
> to verify they've been correctly copied.  The base-58-encoded seed
> file is short enough to memorize, providing another brain storage
> alternative.

> Transactions are signed offline: your private keys never touch an
> online computer.

> Implemented as a suite of lightweight Python scripts for the console,
> MMGen requires only a bare minimum of system resources.  Yet in tandem
> with a watch-only enabled bitcoind (see below), it provides a robust
> solution for securely storing, tracking, spending and receiving
> Bitcoins.

> MMGen is currently supported on Windows and Linux.

### Download/Install

#### Debian/Ubuntu Linux:

> **Perform the following steps on both your online and offline
> computers:**

> Install the pip Python installer:

			sudo apt-get install python-pip

> Install required Python modules:

			sudo pip install ecdsa scrypt pycrypto bitcoin-python

> Install MMGen:

			git clone https://github.com/mmgen/mmgen.git
			cd mmgen; sudo ./setup.py install

> Install vanitygen (optional but recommended):

			git clone https://github.com/samr7/vanitygen.git
			(build and put the 'keyconv' executable in your path)

> At this point you may begin using MMgen to create wallets, generate
> keys and create raw transactions as described in **Using MMGen**
> below.  But since you'd like to be able to track addresses and sign
> transactions too, you'll now need to install the bitcoin daemon,
> `bitcoind`, on both your online and offline machines.

> **Bitcoind installation**

> On the **offline machine**, the bitcoin daemon is used solely for
> signing transactions and can therefore be run without a blockchain.
> The version bundled with the prebuilt Bitcoin-QT is just fine for this
> purpose.  It can be obtained here:

			https://bitcoin.org/en/download

> After installation, locate the bitcoind executable, optionally place
> it in your path and start it with the arguments `-daemon -maxconnections=0`.

> Note that in the absence of a blockchain the daemon starts very quickly
> and uses practically no CPU power once running.  Thus you'll have no
> problem using a low-powered computer such as a netbook for your
> offline machine.

> On the **online machine**, the bitcoin daemon is used for tracking
> addresses and must be run with the full blockchain.  Thus a more
> powerful computer is required here.  In addition, the precompiled
> bitcoin package we installed above lacks (for now) the watch-only
> address support we need, so we must get and compile Sipa's
> watch-only enabled version from github:

            git clone https://github.com/sipa/bitcoin
            cd bitcoin
            git branch wo origin/watchonly
            git checkout wo
			./configure
            make
            (You may have to install the libboost-all-dev package for the build to succeed)
> With your online machine connected to the Internet, start your freshly
> compiled daemon and let it synchronize, making sure to move your old
> `wallet.dat` out of harm's way beforehand if you have an existing
> bitcoin installation.  You'll use the new wallet created by the daemon
> on startup as your **tracking wallet**.

> Your setup is now complete.


### Using MMGen:
> On your offline computer:

> Generate a wallet with a random seed:

			$ mmgen-walletgen
			...
			Wallet saved to file '89ABCDEF-76543210[256,3].mmdat'

> "89ABCDEF" is the Seed ID; "76543210" is the Key ID. These are
> randomly generated, so your IDs will of course be different than the
> fictitious ones used here.

> The Seed ID never changes and is used to identify all keys/addresses
> generated by this wallet.	The Key ID changes when the wallet's
> password or hash preset are changed.

> "256" is the seed length; "3" is the scrypt hash preset.	These are
> configurable.


> Generate ten addresses with the wallet:

			$ mmgen-addrgen 89ABCDEF-76543210[256,3].mmdat 1-10
			...
			Address data saved to file '89ABCDEF[1-10].addrs'


> Note that the address range, "1-10", is reflected in the resulting filename.

			$ cat '89ABCDEF[1-10].addrs'
			89ABCDEF {
			  1		16bNmyYISiptuvJG3X7MPwiiS4HYvD7ksE
			  2		1AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc
			  3		1HgYCsfqYzIg7LVVfDTp7gYJocJEiDAy6N
			  4		14Tu3z1tiexXDonNsFIkvzqutE5E3pTK8s
			  5		1PeI55vtp2bX2uKDkAAR2c6ekHNYe4Hcq7
			  6		1FEqfEsSILwXPfMvVvVuUovzTaaST62Mnf
			  7		1LTTzuhMqPLwQ4IGCwwugny6ZMtUQJSJ1
			  8		1F9495H8EJLb54wirgZkVgI47SP7M2RQWv
			  9		1JbrCyt7BdxRE9GX1N7GiEct8UnIjPmpYd
			  10	1H7vVTk4ejUbQXw45I6g5qvPBSe9bsjDqh
			}

> Let's label the first two addresses "Donations" and "Client 1"
> and import them into our tracking wallet.  To do this,
> copy and edit the above file in a text editor such as vim:

			$ cat my.addrs
			89ABCDEF {
			  1		16bNmyYISiptuvJG3X7MPwiiS4HYvD7ksE  Donations
			  2		1AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc  Client 1
            }

> With the online bitcoind running, import the two addresses into the
> wallet:

			$ mmgen-addrimport my.addrs

### END rewrite

### Spending your stored coins:
> Take address 1 out of cold storage by generating a key for it:

			$ mmgen-keygen 89ABCDEF-76543210[256,3].mmdat 1
			...
			Key data saved to file '89ABCDEF[1].akeys'

			$ cat 89ABCDEF[1].akeys
			89ABCDEF {
			  1  sec:  5JCAfK1pjRoJgmpmd2HEMNwHxAzprGIXeQt8dz5qt3iLvU2KCbS
				 addr: 16bNmyYISiptuvJG3X7MPwiiS4HYvD7ksE
			}

> Save the .akeys file to a USB stick and transfer it to your online computer.

> On your online computer, import the secret key into a running bitcoind
> or bitcoin-qt:

			$ bitcoind importprivkey 5JCAfK1pjRoJgmpmd2HEMNwHxAzprGIXeQt8dz5qt3iLvU2KCbS

> You're done!	This address' balance can now be spent.

> OPTIONAL: To track balances without exposing secret keys on your
> online computer, download and compile sipa's bitcoind patched for
> watch-only addresses:

			$ git clone https://github.com/sipa/bitcoin
			$ git branch mywatchonly remotes/origin/watchonly
			$ git checkout mywatchonly
			(build, install)
			(You may have to install libboost-all-dev for the build to succeed)

> With your newly-compiled bitcoind running, import the addresses from
> '89ABCDEF[1-10].addrs' to track their balances:

			$ bitcoind importaddress 16bNmyYISiptuvJG3X7MPwiiS4HYvD7ksE
			$ bitcoind importaddress 1AmkUxrfy5dMrfmeYwTxLxfIswUCcpeysc
			$ ...

### Using the mnemonic and seed features:

> Continuing our example above,

> Generate a mnemonic from the wallet:

			$ mmgen-walletchk -m '89ABCDEF-76543210[256,3].mmdat'
			...
			Mnemonic data saved to file '89ABCDEF.mmwords'

			$ cat 89ABCDEF.mmwords
			pleasure tumble spider laughter many stumble secret bother
			after search float absent path strong curtain savior
			worst suspend bright touch away dirty measure thorn

> Note: a 128- or 192-bit seed will generate a shorter mnemonic of 12 or
> 18 words.  You may generate a wallet with a these seed lengths by
> using the `-l` option of `mmgen-walletgen`.  Whether you consider
> 128 bits of entropy enough is your call.	It's probably adequate for
> the foreseeable future.

> Generate addresses 1-11 using the mnemonic instead of the wallet:

			$ mmgen-addrgen -m 89ABCDEF.mmwords 1-11
			...
			Address data saved to file '89ABCDEF[1-11].addrs'

> Compare the first ten addresses with those earlier generated from the
> wallet.  You'll see they're the same.

> Recover a lost wallet using the mnemonic:

			$ mmgen-walletgen -m 89ABCDEF.mmwords
			...
			Wallet saved to file '89ABCDEF-01234567[256,3].mmdat'

> Note that the regenerated wallet has a different Key ID but
> of course the same Seed ID.

> Seeds are generated and input the same way as mnemonics.	Just change
> the `-m` option to `-s` in the preceding commands.

> A seed file for a 256-bit seed looks like this:

			$ cat 8B7392ED.mmseed
			f4c84b C5ZT wWpT Jsoi wRVw 2dm9 Aftd WLb8 FggQ eC8h Szjd da9L

> And for a 128-bit seed:

			$ cat 8E0DFB78.mmseed
			0fe02f XnyC NfPH piuW dQ2d nM47 VU

> The latter is short enough to be memorized or written down.

> The first word in the seed file is a checksum.
> To check that you've written or memorized the seed correctly (should
> you choose to do so), compare it with the first 6 characters of a
> sha256 hash of the remainder of the line (with spaces removed).

#### Mnemonics and seeds — additional information:
> Mnemonic and seed data may be entered at a prompt instead of from a
> file.  Just omit the filename on the command line.

> Mnemonic and seed data may be printed to standard output instead of a
> file using the `-S` option of `mmgen-walletchk`.

> Mnemonic and seed files may be output to a directory of your choice
> using the `-d` option of `mmgen-walletchk`.

> Bear in mind that mnemonic and seed data is unencrypted.	If it's
> compromised, your Bitcoins can easily be stolen.	Make sure no one's
> looking over your shoulder when you print mnemonic or seed data to
> screen.  Securely delete your mnemonic and seed files.  In Linux, you
> can achieve additional security by writing the files to volatile
> memory in '/dev/shm' instead of disk.

### Vanitygen note:
> When available, the 'keyconv' utility from the vanitygen package is
> used to generate addresses as it's much faster than the Python ecdsa
> library.

### Test suite:
> To see what tests are available, run the scripts in the 'tests'
> directory with no arguments.	Among others, you might find the
> following tests to be of interest:

>> Compare 10 addresses generated by 'keyconv' with mmgen's
>> internally-generated ones:
>>> `tests/bitcoin.py keyconv_compare_randloop 10`

>> Convert a string to base 58 and back:
>>> `tests/bitcoin.py strtob58 'a string'`

>> Convert a hex number to base 58 and back:
>>> `tests/bitcoin.py hextob58 deadbeef`

>> Perform 1000 hex -> base58 -> hex conversions, comparing results stringwise:
>>> `tests/bitcoin.py hextob58_pad_randloop 1000`

>> Generate a 12-word mnemonic from a random 128-bit seed:
>>> `tests/mnemonic.py random128`

>> or an 18-word mnemonic from a random 192-bit seed:
>>> `tests/mnemonic.py random192`

>> or a 24-word mnemonic from a random 256-bit seed:
>>> `tests/mnemonic.py random256`
