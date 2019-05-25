#### Perform the following steps on both your online and offline computers:

> Install required Debian/Ubuntu packages:

	$ sudo apt-get install autoconf git libgmp-dev libssl-dev libtool wipe
	$ sudo apt-get install python3-dev python3-ecdsa python3-pexpect python3-setuptools python3-cryptography python3-nacl python3-pip python3-gmpy2

> Using the [pip3][P] installer, install the Python scrypt library (optional for Python >= v3.6):

	$ sudo -H pip3 install scrypt

> Install the secp256k1 library:

	$ git clone https://github.com/bitcoin-core/secp256k1.git
	$ cd secp256k1
	$ ./autogen.sh
	$ ./configure
	$ make
	$ sudo make install
	$ sudo ldconfig
	$ cd ..

> Install MMGen:

	$ git clone https://github.com/mmgen/mmgen.git
	$ cd mmgen
	$ git checkout stable_linux
	$ sudo ./setup.py install
	$ cd ..

> Install the bitcoind daemon(s):

> To install prebuilt binaries, go [here][01].  To install from source, go
> [here][02].

#### *Note for offline machines:*

> Naturally, your offline machine must be connected to the Internet to retrieve
> and install the above packages as described above.  This is normally not a
> problem, as you can simply take the machine offline permanently after the
> install is done, preferably removing or disabling its network interfaces.

> However, if your machine is already offline and you wish to leave it that way,
> or if it lacks a network interface entirely, then you'll need to take roughly
> the following steps:

>> From your online machine, download the Debian/Ubuntu packages and their
>> dependencies manually from packages.debian.org or packages.ubuntu.com, and
>> the Python packages from pypi.python.org/pypi/&lt;packagename&gt;.  Transfer
>> these files and the cloned Git repositories to your offline computer using a
>> USB stick or other storage medium.  Install the Debian/Ubuntu packages with
>> 'sudo dpkg -i', unpack each Python module and install it using 'sudo
>> ./setup.py install', and install MMGen and the secp256k1 library from the
>> copied Git repositories as described above.

Congratulations, your installation is now complete!  Now proceed to [**Getting
Started with MMGen**][gs].

[01]: Install-Bitcoind
[02]: Install-Bitcoind-from-Source-on-Debian-or-Ubuntu-Linux
[gs]: Getting-Started-with-MMGen
[03]: https://pypi.python.org/packages/source/p/pexpect/pexpect-3.1.tar.gz
[P]: https://pypi.org/project/pip
