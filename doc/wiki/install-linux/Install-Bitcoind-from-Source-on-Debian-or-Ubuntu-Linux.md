***Note for Raspbian and Armbian users: Compiling the bitcoin daemon will
probably fail on a RPi or RPi clone due to insufficient memory.  Fortunately,
ARM binaries are available for both Bitcoin Core and Bitcoin ABC.  See the
[binary installation page][01] for details.***

### Install dependencies:

> Make sure the required boost library development packages are installed:

		sudo apt-get install libboost-system-dev libboost-filesystem-dev libboost-program-options-dev libboost-chrono-dev libboost-test-dev libboost-thread-dev

> You'll also need the following standard dependencies, if they're not already on
> your system:

		sudo apt-get install build-essential libtool autotools-dev autoconf pkg-config libssl-dev libdb-dev libdb++-dev libevent-dev

### Compile and install Bitcoin Core:

> Clone the Bitcoin Core repository from Github, configure, and build:

		$ git clone https://github.com/bitcoin/bitcoin.git
		$ cd bitcoin
		$ ./autogen.sh
		$ ./configure --without-gui --with-incompatible-bdb
		$ make -j4

> The '-j4' option will speed the build process up by using 4 cores of a 4-core
> processor, if you have them.  If overheating issues are a problem for your CPU
> or you're short on memory, you may want to omit it or use '-j2'.

> For more detailed build information, consult the file [doc/build-unix.md][bu]
> in the bitcoin source repository.

> Your freshly compiled bitcoind daemon is now in the src/ directory.  Install
> it, along with the 'bitcoin-cli' utility, into your executable path:

		$ cd src
		$ strip bitcoind bitcoin-cli
		$ sudo cp bitcoind /usr/local/bin
		$ sudo cp bitcoin-cli /usr/local/bin

### Compile and install Bitcoin ABC (optional):

> *Regard Bitcoin ABC as experimental software.  The author of the MMGen project
> has only partially reviewed its codebase and makes no guarantees regarding its
> safety or reliability.*

> If you want to transact BCH, also known as “Bitcoin Cash” or “Bcash”, then
> clone the Bitcoin ABC repository, and configure and build exactly as you did
> with Bitcoin Core above:

		$ git clone https://github.com/Bitcoin-ABC/bitcoin-abc
		$ cd bitcoin-abc
		$ ./autogen.sh
		$ ./configure --without-gui --with-incompatible-bdb
		$ make -j4

> The resulting executable is also named 'bitcoind', so you must install it
> under a different name to avoid overwriting your Core daemon:

		$ cd src
		$ strip bitcoind bitcoin-cli
		$ sudo cp bitcoind /usr/local/bin/bitcoind-abc

> From now on, you'll invoke the daemon as 'bitcoind-abc' instead of 'bitcoind'.
> Or alternatively, to simplify the starting and stopping of two daemons on the
> same machine, download and use the node start and stop scripts from the
> MMGenLive project:

		$ curl -O 'https://raw.githubusercontent.com/mmgen/MMGenLive/master/home.mmgen/bin/mmlive-node-{start,stop}'
		$ sudo install mmlive-node-{start,stop} /usr/local/bin

Refer to **Run:** on the [binary installation page][01] for instructions on
running your freshly compiled bitcoin daemon(s).

[01]: Install-Bitcoind
[dl]: https://bitcoin.org/en/download
[gs]: Getting-Started-with-MMGen
[bu]: https://github.com/bitcoin/bitcoin/blob/master/doc/build-unix.md
