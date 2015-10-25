#### Perform the following steps on both your online and offline computers:

Install the pip Python installer:

		$ sudo apt-get install python-pip python-dev

Install required Python modules:

		$ sudo pip install ecdsa scrypt pycrypto bitcoin-python

Install the pexpect Python module:

		$ sudo pip install pexpect

		Note: pexpect v4.0.1 (the latest version as of this writing) is
		BROKEN and will cause errors when running the test suite!
		If this is the version you just installed on your system (examine the
		output of 'pip freeze' to find out), then you must downgrade.  Note
		that newer versions may be broken as well.  Version 3.1 is known to work
		and can be found [here][03].  First, uninstall the broken pexpect:

		$ sudo pip uninstall pexpect

		Then download and unpack the v3.1 tarball, cd to the archive root and
		run 'sudo python setup.py install' to install it.

Install MMGen:

		$ git clone https://github.com/mmgen/mmgen.git
		$ cd mmgen; sudo ./setup.py install

Install vanitygen (optional but recommended):

		$ sudo apt-get install libpcre3-dev
		$ git clone https://github.com/samr7/vanitygen.git
		$ cd vanitygen; make
		(copy the "keyconv" executable to your path)

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
