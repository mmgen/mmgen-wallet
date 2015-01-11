#### Perform the following steps on both your online and offline computers:

Install the pip Python installer:

		$ sudo apt-get install python-pip

Install required Python modules:

		$ sudo pip install ecdsa scrypt pycrypto bitcoin-python pexpect

Install MMGen:

		$ git clone https://github.com/mmgen/mmgen.git
		$ cd mmgen; sudo ./setup.py install

Install vanitygen (optional but recommended):

		$ git clone https://github.com/samr7/vanitygen.git
		(build and put the "keyconv" executable in your path)

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
