***Note for Raspbian and Armbian users: Compiling the Bitcoin or Litecoin daemon
may fail on a RPi or RPi clone due to insufficient memory.  Fortunately, ARM
binaries are available for Bitcoin Core, Bitcoin ABC and Litecoin.  See the
[binary installation page][01] for details.***

### Install dependencies:

> Make sure the required development packages are installed:

Debian/Ubuntu:

```text
sudo apt-get install build-essential libtool autotools-dev autoconf pkg-config libssl-dev libdb-dev libdb++-dev libevent-dev libboost-system-dev libboost-filesystem-dev libboost-program-options-dev libboost-chrono-dev libboost-test-dev libboost-thread-dev
```

ArchLinux:

```text
pacman --sync --needed autoconf automake boost gcc git libevent libtool make pkgconf python sqlite
```

### Compile and install Bitcoin Core:

> Clone the Bitcoin Core repository from Github:

```text
$ git clone https://github.com/bitcoin/bitcoin.git
$ cd bitcoin
```

> Configure and build:

```text
$ git tag # look for your desired version in the tag list
$ git checkout <version>
$ ./autogen.sh
$ ./configure --without-gui --with-incompatible-bdb
$ make -j4
```

> The '-j4' option will speed the build process up by using 4 cores of a 4-core
> processor, if you have them.  If overheating issues are a problem for your CPU
> or you’re short on memory, you may want to omit the option or reduce the
> number of cores used.

> For more detailed build information, consult the file [doc/build-unix.md][bu]
> in the bitcoin source repository.

> Your freshly compiled bitcoind daemon is now in the src/ directory.  Install
> it, along with the 'bitcoin-cli' utility, into your executable path:

```text
$ cd src
$ sudo install -sv bitcoind bitcoin-cli /usr/local/bin
```

### Compile and install Bitcoin Cash Node (optional):

> If you want to transact BCH, also known as “Bitcoin Cash Node”, then first
> clone the Bitcoin Cash Node repository:

```text
$ git clone https://github.com/bitcoin-cash-node/bitcoin-cash-node
$ cd bitcoin-cash-node
```

> Then configure and build using the same configure and build steps as with
> Bitcoin Core above.

> The resulting executable is also named 'bitcoind', so you must install it
> under a different name to avoid overwriting your Core daemon:

```text
$ cd src
$ sudo install -sv bitcoind /usr/local/bin/bitcoind-bchn
```

> From now on, you’ll invoke the daemon as 'bitcoind-bchn' instead of 'bitcoind'.

### Compile and install Litecoin Core (optional):

> Clone the Litecoin Core repository:

```text
$ git clone https://github.com/litecoin-project/litecoin.git
$ cd litecoin
```

> Configure and build using the configure and build steps for Bitcoin Core,
> and then install as follows:

```text
$ cd src
$ sudo install -sv litecoind litecoin-cli /usr/local/bin
```

Refer to [Run][02] on the binary installation page for instructions on running
your coin daemon(s).

Alternatively, you may download and use the node start and stop scripts from the
MMGenLive project, which simplify starting and stopping multiple daemons on the
same machine:

```text
$ curl -O 'https://raw.githubusercontent.com/mmgen/MMGenLive/master/home.mmgen/bin/mmlive-node-{start,stop}'
$ sudo install -v mmlive-node-{start,stop} /usr/local/bin
```

[01]: Install-Bitcoind.md
[02]: Install-Bitcoind.md#a_r
[bu]: https://github.com/bitcoin/bitcoin/blob/master/doc/build-unix.md
[bcha]: https://github.com/Bitcoin-ABC/bitcoin-abc
