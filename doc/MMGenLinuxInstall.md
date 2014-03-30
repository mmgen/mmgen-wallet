MMGen = Multi-Mode GENerator
----------------------------
##### a Bitcoin cold storage solution for the command line

### Download/Install on Debian/Ubuntu Linux:

**Perform the following steps on both your online and offline
computers:**

Install the pip Python installer:

		$ sudo apt-get install python-pip

Install required Python modules:

		$ sudo pip install ecdsa scrypt pycrypto bitcoin-python

Install MMGen:

		$ git clone https://github.com/mmgen/mmgen.git
		$ cd mmgen; sudo ./setup.py install

Install vanitygen (optional but recommended):

		$ git clone https://github.com/samr7/vanitygen.git
		(build and put the 'keyconv' executable in your path)

At this point you can begin trying out MMgen, creating a test wallet
and generating keys as described in **Using MMGen** below.  To be
able to track addresses and create and sign transactions, however,
you'll need to have bitcoin daemons installed on your online and
offline machines.

**Bitcoind installation**

The bitcoin daemon on the **offline machine** is used solely for
signing transactions and is therefore run without a blockchain.
The version bundled with the prebuilt Bitcoin-QT is just fine for this
purpose.  It can be obtained here:

		https://bitcoin.org/en/download

After installation, locate the bitcoind executable and start it up:

		$ bitcoind -daemon -maxconnections=0

Note that in the absence of a blockchain the daemon starts very quickly
and uses practically no CPU once running.
Thus a low-powered computer such as a netbook can serve quite nicely
as an offline signing machine.

On the **online machine**, the bitcoin daemon is used for tracking
addresses and requires a full, updated blockchain.  For
this a more powerful computer is needed, especially when importing
addresses.  Plenty of free disk space is also required to accomodate
the rapidly-growing blockchain (20GB in size at the time of writing).

The standard bitcoin daemon at present lacks the watch-only address
support we need, so we must get and compile the special watch-only
enabled version created by Bitcoin core developer Pieter Wuille, aka
sipa.  If you have the necessary dependencies installed, this process
is surprisingly painless.

		$ curl -O https://codeload.github.com/sipa/bitcoin/zip/watchonly
		$ unzip watchonly
		$ cd bitcoin-watchonly
		$ ./autogen.sh
		$ ./configure
		$ make -j4
		(You may have to install the libboost-all-dev package for the build to succeed)

With your online machine connected to the Internet, start the freshly
compiled daemon and let it synchronize the blockchain, **taking care
to move any existing wallet.dat out of harm's way** beforehand.
The daemon will create a new wallet upon startup, which you'll use
as your **tracking wallet**.

Congratulations!  Your MMGen installation is now complete.
