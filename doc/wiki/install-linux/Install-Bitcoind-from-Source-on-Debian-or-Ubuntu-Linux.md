***Note for Raspbian and Armbian users: Compiling the Bitcoin or Litecoin daemon
may fail on a RPi or RPi clone due to insufficient memory.  Fortunately, ARM
binaries are available for Bitcoin Core, Bitcoin ABC and Litecoin.  See the
[binary installation page][01] for details.***

### Install dependencies:

> Make sure the required boost library development packages are installed:

	sudo apt-get install libboost-system-dev libboost-filesystem-dev libboost-program-options-dev libboost-chrono-dev libboost-test-dev libboost-thread-dev

> You’ll also need the following standard dependencies, if they’re not already on
> your system:

	sudo apt-get install build-essential libtool autotools-dev autoconf pkg-config libssl-dev libdb-dev libdb++-dev libevent-dev

### Compile and install Bitcoin Core:

> Clone the Bitcoin Core repository from Github:

	$ git clone https://github.com/bitcoin/bitcoin.git
	$ cd bitcoin

> Configure and build:

	$ git tag # look for your desired version in the tag list
	$ git checkout <version>
	$ ./autogen.sh
	$ ./configure --without-gui --with-incompatible-bdb
	$ make -j4

> The '-j4' option will speed the build process up by using 4 cores of a 4-core
> processor, if you have them.  If overheating issues are a problem for your CPU
> or you’re short on memory, you may want to omit the option or reduce the
> number of cores used.

> For more detailed build information, consult the file [doc/build-unix.md][bu]
> in the bitcoin source repository.

> Your freshly compiled bitcoind daemon is now in the src/ directory.  Install
> it, along with the 'bitcoin-cli' utility, into your executable path:

	$ cd src
	$ sudo install -sv bitcoind bitcoin-cli /usr/local/bin

### Compile and install Bitcoin ABC (optional):

> *Consider Bitcoin ABC to be experimental software.  The author of the MMGen
> project has only partially reviewed its codebase and makes no guarantees
> regarding its safety or reliability.*

> If you want to transact BCH, also known as “Bitcoin Cash” or “Bcash”, then
> first clone the Bitcoin ABC repository:

	$ git clone https://github.com/Bitcoin-ABC/bitcoin-abc
	$ cd bitcoin-abc

> Then configure and build using the same configure and build steps as with
> Bitcoin Core above.

> The resulting executable is also named 'bitcoind', so you must install it
> under a different name to avoid overwriting your Core daemon:

	$ cd src
	$ sudo install -sv bitcoind /usr/local/bin/bitcoind-abc

> From now on, you’ll invoke the daemon as 'bitcoind-abc' instead of 'bitcoind'.

### Compile and install Litecoin Core (optional):

> Clone the Litecoin Core repository:

	$ git clone https://github.com/litecoin-project/litecoin.git
	$ cd litecoin

> Configure and build using the configure and build steps for Bitcoin Core,
> and then install as follows:

	$ cd src
	$ sudo install -sv litecoind litecoin-cli /usr/local/bin

Refer to [Run][02] on the binary installation page for instructions on running
your coin daemon(s).

Alternatively, you may download and use the node start and stop scripts from the
MMGenLive project, which simplify starting and stopping multiple daemons on the
same machine:

	$ curl -O 'https://raw.githubusercontent.com/mmgen/MMGenLive/master/home.mmgen/bin/mmlive-node-{start,stop}'
	$ sudo install -v mmlive-node-{start,stop} /usr/local/bin

[01]: Install-Bitcoind
[02]: Install-Bitcoind#a_r
[bu]: https://github.com/bitcoin/bitcoin/blob/master/doc/build-unix.md
