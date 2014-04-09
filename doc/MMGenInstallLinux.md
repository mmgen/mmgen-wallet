MMGen = Multi-Mode GENerator
============================
##### a Bitcoin cold storage solution for the command line

Install MMGen on Debian/Ubuntu Linux
------------------------------------

**Perform the following steps on both your online and offline computers:**

Install the pip Python installer:

		$ sudo apt-get install python-pip

Install required Python modules:

		$ sudo pip install ecdsa scrypt pycrypto bitcoin-python

Install MMGen:

		$ git clone https://github.com/mmgen/mmgen.git
		$ cd mmgen; sudo ./setup.py install

Install vanitygen (optional but recommended):

		$ git clone https://github.com/samr7/vanitygen.git
		(build and put the "keyconv" executable in your path)

At this point you can begin trying out MMgen, creating a test wallet and
generating keys as described in **Using MMGen** below.  To be able to track
addresses and create and sign transactions, however, you'll need to have
bitcoin daemons installed on your online and offline machines.

#### Install the offline bitcoind:

Instructions [here][01].

#### Install the online bitcoind:

The bitcoin daemon on the **online machine**, a.k.a. the "watch-only" bitcoind,
is used for tracking addresses and requires the full blockchain.  For this, a
more powerful computer is desirable.  In particular, importing addresses is
especially CPU-intensive.  You'll also need plenty of free disk space for the
rapidly-growing blockchain (~20GB at the time of writing).

The standard bitcoin daemon at present lacks the watch-only address support we
need, so you'll have to get and compile a patched version by Bitcoin core
developer Pieter Wuille, aka Sipa.  Fortunately, it builds out of the box
when the proper dependencies are installed.

The boost development packages are the dependencies you're most likely to be
missing.  Check that the following are on your system (package names may vary;
the version should be 1.48 or greater):

		libboost-system-dev
		libboost-filesystem-dev
		libboost-program-options-dev
		libboost-chrono-dev
		libboost-test-dev
		libboost-thread-dev

Download the bitcoin-watchonly [zip archive][00] (commit #a13f1e8 [[check][]])
from GitHub, configure, and build:

		$ unzip watchonly.zip
		$ cd bitcoin-watchonly
		$ ./autogen.sh
		$ ./configure (add --with-incompatible-bdb if libdb version > 4.8)
		$ make -j4 src/bitcoind

With your online machine connected to the Internet, start the freshly compiled
daemon and let it synchronize the blockchain, taking care to **move any
existing wallet.dat out of harm's way** beforehand.  You'll use the new wallet
created by the daemon upon startup as your **tracking wallet**.

Congratulations!  Your MMGen installation is now complete.

[00]: https://codeload.github.com/sipa/bitcoin/zip/watchonly
[01]: MMGenInstallOfflineBitcoind.md
[check]: https://github.com/sipa/bitcoin/tree/watchonly
