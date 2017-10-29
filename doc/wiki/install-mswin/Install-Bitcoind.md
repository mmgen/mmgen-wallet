## Install Bitcoind and other supported coin daemons

The bitcoin daemon on the **offline computer** is used solely to sign
transactions and runs without a blockchain.  Thus even a low-powered computer
such as a Raspberry Pi or an old netbook can serve nicely as your offline
machine.

The bitcoin daemon on the **online computer** requires a complete and
up-to-date blockchain for tracking addresses.  Since its work is more CPU and
disk intensive, a more powerful computer is required here.  You'll also need
plenty of free disk space for the growing blockchain (~160GB at the time of
writing).

Two blockchain operations are especially resource-intensive: **synchronizing
the blockchain** and **importing existing addresses with balances**.  If you
synchronize often (once a week, for example) and take care to import your
addresses **before** spending into them, then it's possible to get by with a
more low-powered computer as your online machine.

### <a name='a_d'>Download:</a>

> **Bitcoin Core:**

>> Go to the Bitcoin Core [download page][01].  Choose the 32-bit or 64-bit
>> versions appropriate for your online and offline computers.  Windows users
>> should choose the executable installer.

> **Bitcoin ABC (optional):**

>> If you wish to transact BCH (Bcash), then download the appropriate [Bitcoin
>> ABC binary][abc] for your system as well.  Windows users should choose the
>> executable installer.  
>> *Consider the Bitcoin ABC binaries untrusted software.  The author of the
>> MMGen project makes no guarantees regarding their safety or reliability.*

> **Litecoin (optional):**

>> Go to the Litecoin Core [download page][lc].  Choose the 32-bit or 64-bit
>> versions appropriate for your online and offline computers.  Windows users
>> should choose the executable installer.

### <a name='a_i'>Install (both online and offline computers):</a>

> **Bitcoin Core:**

>> **Windows:** Run the Windows installer with the default settings.  Add
>> 'C:\Program Files\Bitcoin\daemon' to your [path][05].  
>> **Linux:** Unpack the archive and copy the 'bitcoind' and 'bitcoin-cli'
>> binaries to /usr/local/bin.

> **Bitcoin ABC (optional):**

>> **Windows:** Run the Windows installer, installing into the alternate
>> folder 'C:\Program Files\Bitcoin_ABC'. Add 'C:\Program Files\Bitcoin_ABC\daemon'
>> to your [path][05]. Rename the file 'bitcoind' in that folder to
>> 'bitcoind-abc'.  
>> **Linux:** Unpack the archive, rename 'bitcoind' to 'bitcoind-abc' and
>> copy it to /usr/local/bin.

> **Litecoin (optional):**

>> **Windows:** Run the Windows installer with the default settings.  Add
>> 'C:\Program Files\Litecoin\daemon' to your [path][05].  
>> **Linux:** Unpack the archive and copy the 'litecoind' and
>> 'litecoin-cli' binaries to /usr/local/bin.

### <a name='a_r'>Run (both online and offline computers):</a>

> **Windows:**

>> In the Windows command-line environment processes don't fork to run in the
>> background, so to run multiple daemons simultaneously you must start each
>> one in a separate terminal window.  Start your daemons like this:

		# Bitcoin Core:
		$ bitcoind

		# ABC:
		$ mkdir $APPDATA/Bitcoin_ABC
		$ bitcoind-abc --listen=0 --rpcport=8442 --datadir=$APPDATA/Bitcoin_ABC

		# Litecoin
		$ litecoind

>> Note that the `--listen=0` argument is required only when running Core and ABC simultaneously.

> **Linux:**

>> Linux users start their daemons like this:

		# Bitcoin Core:
		$ bitcoind --daemon

		# ABC:
		$ mkdir ~/.bitcoin-abc
		$ bitcoind-abc --daemon --listen=0 --rpcport=8442 --datadir=$HOME/.bitcoin-abc

		# Litecoin:
		$ litecoind --daemon

> Communicate with your daemons like this:

		# Core:
		$ bitcoin-cli help

		# ABC:
		$ bitcoin-cli --rpcport=8442 help

		# Litecoin:
		$ litecoin-cli help

> Warning: If you're using an existing Bitcoin or Litecoin installation, **move
> your wallet.dat out of harm's way** before starting the daemon.  The new
> wallet now created will be used as your **tracking wallet**.

> If you're connected to the Internet, bitcoind will begin downloading and
> verifying the blockchain.  This can take from several hours to several days
> depending on the speed of your computer and Internet connection.  You can
> speed up your initial block download enormously by adding the `-assumevalid`
> option, followed by a recent block hash, to the command line.  Recent block
> hashes can be found on any blockchain explorer site.

> For the offline daemons you may add the options `-maxconnections=0 -listen=0`
> to the command line.  Note that offline daemons start very quickly, since they
> have no blockchains, and use practically no CPU once running.

[01]: https://bitcoin.org/en/download
[bd]: https://bitcoin.org/bin/blockchain/
[05]: Editing-the-user-path-in-Windows
[abc]: https://download.bitcoinabc.org/
[lc]: https://download.litecoin.org/litecoin-0.15.0.1rc1/
