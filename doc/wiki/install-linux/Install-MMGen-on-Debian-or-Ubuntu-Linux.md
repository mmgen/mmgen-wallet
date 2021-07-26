#### Perform the following steps on both your online and offline computers:

Install required Debian/Ubuntu packages:

	$ sudo apt-get install autoconf git libgmp-dev libssl-dev libpcre3-dev libtool wipe curl
	$ sudo apt-get install python3-dev python3-ecdsa python3-pexpect python3-setuptools python3-cryptography python3-nacl python3-pip python3-gmpy2 python3-sha3 python3-requests python3-aiohttp python3-socks

Using the [pip3][P] installer, install the scrypt Python package:

	$ sudo -H pip3 install scrypt

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
	$ git checkout stable_linux # see 'Note' below
	$ ./setup.py build
	$ sudo ./setup.py install # see 'Testing Note' below
	$ cd ..

**Note:** if you want to use features that have appeared since the latest
`stable_linux` release, then you can omit the `git checkout` step and remain on
the `master` branch.  Please bear in mind, however, that while the tip of
`master` is always tested on Linux before being pushed to the public repository,
security vulnerabilities are more likely to be present in new code than in a
stable release.  In addition, new code may require dependencies or installation
steps not yet covered in the documentation.

**Testing Note:** MMGen may be tested in place prior to installation.  Refer to
the [Test Suite][ts] wiki page for details.

Install your coin daemon(s).  To install prebuilt binaries, go [here][01].  To
install from source, go [here][02].

#### *Note for offline machines:*

> Your offline machine must be connected to the Internet to retrieve and install
> the above packages as described above.  This is normally not a problem, as you
> can simply take the machine offline permanently after the install is done,
> preferably removing or disabling its network interfaces.

> However, if your machine is already offline and you wish to leave it that way,
> or if it lacks a network interface entirely, then you’ll need to take roughly
> the following steps:

>> If your offline and offline machines have the same architecture, then you can
>> download the Debian/Ubuntu packages and their dependencies on your online
>> machine using `apt-get download`.  Otherwise, you must retrieve the packages
>> manually from `packages.debian.org` or `packages.ubuntu.com`.
>>
>> Download any required Python packages using `pip3 download`.
>>
>> Transfer the downloaded files and cloned Git repositories to your offline
>> computer using a USB stick or other removable medium.  Install the
>> Debian/Ubuntu packages with `sudo dpkg -i` and the Python packages with `pip3
>> install`.  Install MMGen and the secp256k1 library from the copied Git
>> repositories as described above.

Congratulations, your installation is now complete!  You can now proceed to
[**Getting Started with MMGen**][gs].

[01]: Install-Bitcoind
[02]: Install-Bitcoind-from-Source-on-Debian-or-Ubuntu-Linux
[ts]: Test-Suite
[gs]: Getting-Started-with-MMGen
[03]: https://pypi.python.org/packages/source/p/pexpect/pexpect-3.1.tar.gz
[P]: https://pypi.org/project/pip
