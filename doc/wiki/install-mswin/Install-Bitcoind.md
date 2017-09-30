## Installing the Bitcoin daemon

The bitcoin daemon on the **offline computer** is used solely to sign
transactions and runs without a blockchain.  Thus even a low-powered computer
such as a netbook will suffice as your offline machine.

The bitcoin daemon on the **online computer** requires a complete and
up-to-date blockchain for tracking addresses.  Since its work is more CPU and
disk intensive, a more powerful computer is recommended here.  You'll also
need plenty of free disk space for the rapidly growing blockchain (~100GB at
the time of writing).

Two blockchain operations are especially resource-intensive: **synchronizing
the blockchain** and **importing existing addresses with balances**.  If you
synchronize often (once a week, for example) and take care to import your
addresses **before** spending into them, then it's possible to use a
low-powered netbook as your online machine.

### Download:

> **Bitcoin Core:**

>> Go to the Bitcoin Core [main download page][01].  Choose the 32-bit or 64-bit
>> versions appropriate for your online and offline computers.

> **Bitcoin ABC (optional):**

>> If you wish to transact BCH, a.k.a "Bitcoin Cash” or “Bcash”, then download
>> the appropriate [Bitcoin ABC binary][abc] for your system as well.  Windows
>> users should download the zip file rather than the installer.  Both Windows
>> and Linux users **must** rename the binary to 'bitcoind-abc' before
>> installing it in their executable path.

>> *Regard the Bitcoin ABC binaries as untrusted software.  The author of the
>> MMGen project makes no guarantees regarding their safety or reliability.*

### Install (both online and offline computers):

> **Windows users:**

>> Run the Windows installer.  When it's finished, determine where it installed
>> 'bitcoind.exe' (probably in `C:\Program Files\Bitcoin\daemon`) and append
>> that path to your [PATH variable][05].

> **Linux users:**

>> Unpack the tar archive and copy the bitcoind executable in bin/ to your
>> execution path or just run it in place.

### Run (both Windows and Linux):

> **On the online computer:**

>> Open a terminal and start bitcoind with the command:

		$ bitcoind -daemon

>> Warning: If you're using an existing Bitcoin Core installation, **move your
>> wallet.dat out of harm's way** before starting bitcoind.  The new wallet now
>> created will be used as your **tracking wallet**.

>> If you're connected to the Internet, bitcoind will begin downloading and
>> verifying the blockchain.  This can take from several hours to several days
>> (depending on the speed of your computer) for an initial download.

> **On the offline computer:**

>> Open a terminal and start bitcoind with the command:

		$ bitcoind -daemon -maxconnections=0 -listen=0

>> Note that in the absence of a blockchain the offline daemon starts very
>> quickly and uses practically no CPU once running.

>> *Note for Windows users:* Under Windows, the bitcoind daemon doesn't fork to
>> run as a background process, so you'll have to run it in a separate terminal
>> window

[01]: https://bitcoin.org/en/download
[bd]: https://bitcoin.org/bin/blockchain/
[05]: Editing-the-user-path-in-Windows
[abc]: https://download.bitcoinabc.org/
