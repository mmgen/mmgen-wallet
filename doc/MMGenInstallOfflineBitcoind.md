MMGen = Multi-Mode GENerator
============================
##### a Bitcoin cold storage solution for the command line

### Install the offline bitcoind:

The bitcoin daemon on the **offline machine** is used solely for signing
transactions and is therefore run without a blockchain.  The version bundled
with the prebuilt Bitcoin-QT is just fine for this purpose.  Windows and Linux
binaries can be obtained [here][00].

After installation, locate the bitcoind executable, place it on your execution
path and start it with the command:

		$ bitcoind -daemon -maxconnections=0

Note that in the absence of a blockchain the daemon starts very quickly and
uses practically no CPU once running.  Thus a low-powered computer such as a
netbook can serve quite nicely as an offline machine for signing transactions.

[00]: https://bitcoin.org/en/download

