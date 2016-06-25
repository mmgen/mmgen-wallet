#### Note:

> The bitcoin daemon on the **offline computer** is used solely to sign
> transactions and runs without a blockchain.  Thus even a low-powered computer
> such as a netbook will suffice as your offline machine.
>
> The bitcoin daemon on the **online computer** requires a complete and
> up-to-date blockchain for tracking addresses.  Since its work is more CPU and
> disk intensive, a more powerful computer is recommended here.  You'll also
> need plenty of free disk space for the rapidly growing blockchain (~30GB at
> the time of writing).
>
> Two blockchain operations are especially resource-intensive: **synchronizing
> the blockchain** and **importing existing addresses with balances**.  If you
> synchronize often (once a week, for example) and take care to import your
> addresses **before** spending into them, then it's possible to use a
> low-powered netbook as your online machine.

#### Download:

> For the time being, Windows installers and Linux binary tarballs can be
> obtained [here][00].  Once version 0.10 is released, get them from Bitcoin
> Core's [main download page][01] instead.  Choose the 32-bit or 64-bit versions
> appropriate for your respective computers.

#### Install:

> **On both the online and offline computers:**

> Windows users: run the Windows installer.  Linux users: unpack the tar archive
> and copy the bitcoind executable in bin/ to your execution path or just run it
> in place.

#### Run:

> **On the online computer:**

> Open a terminal and start bitcoind with the command:

		$ bitcoind -daemon

> Warning: If you already have Bitcoin Core installed, **move your existing
> wallet.dat out of harm's way** before starting bitcoind.  The new wallet
> now created will be used as your **tracking wallet**.

> If you're connected to the Internet, bitcoind will begin downloading and
> verifying the blockchain.  This can take from several hours to several days
> (depending on the speed of your computer) if you're downloading the blockchain
> from scratch.

> **On the offline computer:**

> Open a terminal and start bitcoind with the command:

		$ bitcoind -daemon -maxconnections=0 -listen=0

> Note that in the absence of a blockchain the daemon starts very quickly and
> uses practically no CPU once running.

[00]: https://bitcoin.org/bin/0.10.0/test/
[01]: https://bitcoin.org/en/download
[bd]: https://bitcoin.org/bin/blockchain/
