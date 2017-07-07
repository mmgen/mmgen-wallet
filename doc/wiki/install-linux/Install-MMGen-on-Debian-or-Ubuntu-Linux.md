#### Perform the following steps on both your online and offline computers:

Install required Debian/Ubuntu packages:

		$ sudo apt-get install python-pip python-dev python-pexpect python-ecdsa python-scrypt libssl-dev git autoconf libtool wipe python-setuptools

Install the Python Cryptography Toolkit:

		$ sudo -H pip install pycrypto

Install the secp256k1 library:

		$ git clone https://github.com/bitcoin-core/secp256k1.git
		$ cd secp256k1
		$ ./autogen.sh
		$ ./configure
		$ make
		$ sudo make install
		$ sudo ldconfig
		$ cd ..

Install MMGen:

		$ git clone https://github.com/mmgen/mmgen.git
		$ cd mmgen
		$ git checkout -b stable stable_linux
		$ sudo ./setup.py install
		$ cd ..

Install vanitygen (optional):

		$ sudo apt-get install libpcre3-dev
		$ git clone https://github.com/samr7/vanitygen.git
		$ cd vanitygen; make
		(copy the "keyconv" executable to your execution path)
		$ cd ..

Install bitcoind:

> To install prebuilt binaries, click [here][01].  To install from source,
> click [here][02].

**NB:** Naturally, your offline machine must be connected to the Internet to
retrieve and install the above packages as described above.  If your offline
machine is already offline and you wish to leave it that way, then you'll be
forced to take roughly the following steps:

> From your online machine, download the Debian/Ubuntu packages and their
> dependencies manually from packages.debian.org or packages.ubuntu.com, and the
> Python packages from pypi.python.org/pypi/&lt;packagename&gt;.  Transfer these
> files and the git repositories you've cloned to your offline computer using a
> USB stick or other means at your disposal.  Install the Debian/Ubuntu packages
> with 'sudo dpkg -i', unpack each Python module and install it using 'sudo
> ./setup.py install', and install MMGen and the secp256k1 library from the
> copied git repositories as described above.

Congratulations, your installation is now complete!  Now proceed to [**Getting
Started with MMGen**][gs].

[01]: Install-Bitcoind
[02]: Install-Bitcoind-from-Source-on-Debian-or-Ubuntu-Linux
[gs]: Getting-Started-with-MMGen
[03]: https://pypi.python.org/packages/source/p/pexpect/pexpect-3.1.tar.gz
