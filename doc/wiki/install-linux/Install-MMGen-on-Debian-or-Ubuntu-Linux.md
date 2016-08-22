#### Perform the following steps on both your online and offline computers:

Install required Debian/Ubuntu packages:

		$ sudo apt-get install python-pip python-dev python-pexpect python-ecdsa python-scrypt libssl-dev git

Install the Python Cryptography Toolkit:

		$ sudo pip install pycrypto

Install the secp256k1 library

		$ git clone https://github.com/bitcoin-core/secp256k1.git
		$ cd secp256k1
		$ ./autogen.sh
		$ ./configure
		$ make
		$ sudo make install

Install MMGen:

		$ git clone https://github.com/mmgen/mmgen.git
		$ cd mmgen; sudo ./setup.py install

Install vanitygen (optional):

		$ sudo apt-get install libpcre3-dev
		$ git clone https://github.com/samr7/vanitygen.git
		$ cd vanitygen; make
		(copy the "keyconv" executable to your execution path)

Install bitcoind:

> To install prebuilt binaries, click [here][01].  To install from source,
> click [here][02].

**NB:** If your offline machine is already disconnected from the Internet,
do the following:

> From your online machine, download the 'python-pip' package from Debian or
> Ubuntu and the Python packages from pypi.python.org/pypi/&lt;packagename&gt;.
> Transfer these files and the git repositories you've cloned to your offline
> computer using a USB stick or other means at your disposal.  Now install
> 'python-pip' with 'sudo dpkg -i', unpack each Python module and install it
> using 'sudo ./setup.py install', and install MMGen and vanitygen from the
> copied git repositories as described above.

Congratulations, your installation is now complete!  Now proceed to [**Getting
Started with MMGen**][gs].

[01]: Install-Bitcoind
[02]: Install-Bitcoind-from-Source-on-Debian-or-Ubuntu-Linux
[gs]: Getting-Started-with-MMGen
[03]: https://pypi.python.org/packages/source/p/pexpect/pexpect-3.1.tar.gz
