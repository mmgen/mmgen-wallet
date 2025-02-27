## Install Bitcoind and other supported coin daemons

The bitcoin daemon on the **offline computer** is used solely to sign
transactions and runs without a blockchain.  Thus even a low-powered computer
such as a Raspberry Pi or an old netbook can serve nicely as your offline
machine.

The bitcoin daemon on the **online computer** requires a complete and
up-to-date blockchain for tracking addresses.  Since its work is more CPU and
disk intensive, a more powerful computer is required here.  You’ll also need
plenty of free disk space for the growing blockchain (~265GB at the time of
writing).

Two blockchain operations are especially resource-intensive: **synchronizing
the blockchain** and **importing existing addresses with balances**.  If you
synchronize often (once a week, for example) and take care to import your
addresses **before** spending into them, then it’s possible to get by with a
more low-powered computer as your online machine.

### <a id="a_d">Download:</a>

> **Bitcoin Core:**

>> Go to the Bitcoin Core download page ([here][00] or [here][01]).  Choose the
>> 32-bit or 64-bit versions appropriate for your online and offline computers.
>> Windows users should choose the executable installer.

> **Bitcoin Cash Node (optional):**

>> If you wish to transact BCH (Bitcoin Cash Node), then download the
>> appropriate [Bitcoin Cash Node binary][bch] for your system.
>> Windows users should choose the executable installer.

> **Litecoin (optional):**

>> Go to the Litecoin Core [download page][lc].  Choose the 32-bit or 64-bit
>> versions appropriate for your online and offline computers.  Windows users
>> should choose the executable installer.

### <a id="a_i">Install (both online and offline computers):</a>

> **Bitcoin Core:**

>> **Windows:** Run the Windows installer with the default settings.
>> At the end of the installation process, uncheck the Run box to prevent the
>> client from starting.
>>
>> **Linux, macOS:** Unpack the archive and copy the `bitcoind` and
>> `bitcoin-cli` binaries to `/usr/local/bin`.

> **Bitcoin Cash Node (optional):**

>> **Windows:** Run the Windows installer with the default settings.
>> At the end of the installation process, uncheck the Run box to prevent the
>> client from starting.
>>
>> Navigate to `C:\Program Files\Bitcoin-Cash-Node\daemon` and rename the file
>> `bitcoind` to `bitcoind-bchn` and `bitcoin-cli` to `bitcoin-cli-bchn`.
>>
>> **Linux, macOS:** Unpack the archive, rename `bitcoind` to `bitcoind-bchn`,
>> and `bitcoin-cli` to `bitcoin-cli-bchn`, and copy the renamed files to
>> `/usr/local/bin`.

> **Litecoin (optional):**

>> **Windows:** Run the Windows installer with the default settings.
>> At the end of the installation process, uncheck the Run box to prevent the
>> client from starting.
>>
>> **Linux, macOS:** Unpack the archive and copy the `litecoind` and
>> `litecoin-cli` binaries to `/usr/local/bin`.

### <a id="a_r">Run (both online and offline computers):</a>

> **Windows:**

>> In the Windows command-line environment processes don’t fork to run in the
>> background, so to run multiple daemons simultaneously you must start each
>> one in a separate terminal window.  Start your daemons like this:

```text
# Bitcoin Core:
$ bitcoind

# Bitcoin Cash Node:
$ mkdir $APPDATA/Bitcoin-Cash-Node
$ bitcoind-bchn --listen=0 --rpcport=8432 --datadir=$APPDATA/Bitcoin-Cash-Node

# Litecoin
$ litecoind
```

>> Note that the `--listen=0` argument is required only when running Bitcoin
>> Core and Bitcoin Cash Node simultaneously.

> **Linux, macOS:**

>> Linux and macOS users start their daemons like this:

```text
# Bitcoin Core:
$ bitcoind --daemon

# Bitcoin Cash Node:
$ mkdir ~/.bitcoin-bchn
$ BCH_DATADIR="$HOME/.bitcoin-bchn"                                 # Linux
$ BCH_DATADIR="$HOME/Library/Application Support/Bitcoin-Cash-Node" # macOS
$ bitcoind-bchn --daemon --listen=0 --rpcport=8432 --datadir="$BCH_DATADIR"

# Litecoin:
$ litecoind --daemon
```

> Communicate with your daemons like this:

```text
# Bitcoin Core:
$ bitcoin-cli help

# Bitcoin Cash Node:
$ BCH_DATADIR="$HOME/.bitcoin-bchn"                                 # Linux
$ BCH_DATADIR="$HOME/Library/Application Support/Bitcoin-Cash-Node" # macOS
$ bitcoin-cli-bchn --rpcport=8432 --datadir="$BCH_DATADIR" help

# Litecoin:
$ litecoin-cli help
```

> If you’re connected to the Internet, the daemon(s) will begin downloading and
> verifying the blockchain.  This can take from several hours to several days
> depending on the speed of your computer, the size of the blockchain(s) in
> question and your Internet connection.  You can speed up your initial block
> download enormously by adding the `-assumevalid` option, followed by a recent
> block hash, to the command line.  Recent block hashes can be found on any
> blockchain explorer site.

> For the offline daemons you may add the options `-maxconnections=0 -listen=0`
> to the command line.  Note that offline daemons start very quickly, since they
> have a blockchain consisting of one block, and use practically no CPU power
> once running.

[00]:  https://bitcoin.org/bin/
[01]:  https://bitcoincore.org/bin/
[bd]:  https://bitcoin.org/bin/blockchain/
[lc]:  https://litecoin.org
[bch]: https://bitcoincashnode.org/en/download.html
