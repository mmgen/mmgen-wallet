***Warning: though the MMGen installation process on Windows has become easier,
it still requires patience, and the user experience is less than optimal.
You're urged to use the prebuilt [MMGenLive][20] USB image instead.  It's now
the preferred way for all non-Linux users to run MMGen.***

### 1. Create the build directory:

Enter your MSYS environment, create the directory `/build` and move to it.
This is where you'll be unpacking and building archives:

		$ mkdir /build
		$ cd /build

If the machine you're installing on is online, you can download the various
tarballs and zipped archives you need from the Internet exactly as described in
the instructions below.  If you're offline, you'll need to download them first
on another machine and then transfer them to the install computer using a USB
stick, for example.

In either case, you'll probably be downloading the archives to a folder
somewhere outside the root of your MSYS filesystem.  To access it within MSYS,
use `/c/` for drive `C:`, `/d/` for drive `D:` and so forth.  A full path to an
archive would thus look something like this:
`/c/my_downloaded_archives/archive_name.tar.gz`.

### 2. Build OpenSSL:

Grab the v1.0.x [tarball][06] from openssl.org, unpack and build:

		$ tar -xzf <path to openssl archive>/openssl-1.0.2j.tar.gz
		$ cd openssl-1.0.2j
		$ ./Configure mingw64 --openssldir=/usr
		$ make
		$ make install

### 3. Build the Scrypt Python module:

The latest scrypt tarball available from [Python][07] at this writing
(scrypt-0.8.0.tar.gz) has missing files and doesn't build, so grab the latest
[zipfile][07z] from the scrypt source repository, unzip and build:

		$ cd /build
		$ unzip <path to scrypt archive>/91d194b6a6bd.zip
		$ cd mhallin-py-scrypt-91d194b6a6bd

Open the file `setup.py` in your text editor. Change the line reading

		from setuptools import setup, Extension

to read

		from distutils.core import setup, Extension

Right before the line beginning with

		scrypt_module = Extension(

add the following lines (with no indentation):

		library_dirs = [r'c:\mingw64\x86_64-w4-mingw32\lib','/msys/lib']
		includes = [r'c:\msys\include']

Save `setup.py`, build and install:

		$ python setup.py build --compiler=mingw32
		$ python setup.py install

Now, to solve a problem with the interpreter not finding the scrypt extension
module, we have to do this little fixup:

		$ cd /mingw/opt/lib/python2.7/site-packages
		$ unzip scrypt*.egg

### 4. Build the pycrypto Python module:

Download the latest pycrypto [tarball][02] from the Python website and unpack it:

		$ cd /build
		$ tar -xzf <path to pycrypto archive>/pycrypto-2.6.1.tar.gz
		$ cd pycrypto-2.6.1

Open the file `setup.py` in your text editor. Remove *exactly* four spaces at
the beginning of this line:

		self.__remove_extensions(["CryptoPublicKey._fastmath"])

to move it one level of indentation to the left.  Save the file and exit the
editor.  Now build and install:

		$ python setup.py build --compiler=mingw32
		$ python setup.py install

### 5. Install the ecdsa Python module:

Grab the latest python-ecdsa [tarball][03], unpack and build:

		$ cd /build
		$ tar -xzf <path to ecdsa archive>/ecdsa-0.13.tar.gz
		$ cd ecdsa-0.13
		$ python setup.py install

### 6. Install the colorama Python module:

Grab the latest colorama [tarball][14], unpack and build:

		$ cd /build
		$ tar -xzf <path to colorama archive>/colorama-0.3.7.tar.gz
		$ cd colorama-0.3.7
		$ python setup.py install

### 7. Install the pexpect Python module (needed for test suite):

Grab the latest pexpect [tarball][15], unpack and build:

		$ cd /build
		$ tar -xzf <path to pexpect archive>/pexpect-4.2.1.tar.gz
		$ cd pexpect-4.2.1
		$ python setup.py install

### 8. Install sdelete utility (needed for secure wallet deletion):

Grab the latest SDelete [zip archive][16], unzip and copy `sdelete.exe` to
your execution path (`c:\windows`, for example).

### 9. Build libsecp256k1:

Libsecp256k1 requires GNU autotools to build, and they're not included in the
MinGW-64 distribution for some reason, so you'll have to retrieve and unpack
them yourself. You'll need these archives:

> * [autoconf][31]
> * [automake][32]
> * [libtool][33]

Unpack them in your /mingw directory and fix up some filenames:

		$ cd /mingw
		$ tar -xzf <path to>/autoconf2.5-2.68-1-mingw32-bin.tar.lzma
		$ tar -xzf <path to>/automake1.11-1.11.1-1-mingw32-bin.tar.lzma
		$ tar -xzf <path to>/libtool-2.4-1-mingw32-bin.tar.lzma
		$ cd bin
		$ cp autoconf-* autoconf
		$ cp automake-* automake
		$ cp aclocal-* aclocal
		$ cp autoreconf-* autoreconf

Now get the latest libsecp256k1 [zip archive][11] from GitHub, unpack, build and
install:

		$ cd /build
		$ unzip.exe <path to libsecp256k1 archive>/master.zip
		$ cd secp256k1-master
		$ ./autogen.sh
		$ ./configure
		$ make
		$ make install

### 10. Install MMGen:

Get the [zip archive][10] of the latest stable version from GitHub, unpack and install:

		$ cd /build
		$ unzip.exe <path to mmgen archive>/stable_mswin.zip
		$ cd mmgen-stable_mswin
		$ python setup.py build --compiler=mingw32
		$ sudo ./setup.py install

If you wish, you may run the MMGen test suite to make sure your installation's
working:

		$ test/test.py -s

[02]: https://pypi.python.org/packages/60/db/645aa9af249f059cc3a368b118de33889219e0362141e75d4eaf6f80f163/pycrypto-2.6.1.tar.gz#md5=55a61a054aa66812daf5161a0d5d7eda
[03]: https://pypi.python.org/packages/f9/e5/99ebb176e47f150ac115ffeda5fedb6a3dbb3c00c74a59fd84ddf12f5857/ecdsa-0.13.tar.gz#md5=1f60eda9cb5c46722856db41a3ae6670
[06]: https://www.openssl.org/source/openssl-1.0.2j.tar.gz
[07]: https://pypi.python.org/pypi/scrypt/
[07z]: https://bitbucket.org/mhallin/py-scrypt/get/91d194b6a6bd.zip
[10]: https://github.com/mmgen/mmgen/archive/stable_mswin.zip
[14]: https://pypi.python.org/packages/f0/d0/21c6449df0ca9da74859edc40208b3a57df9aca7323118c913e58d442030/colorama-0.3.7.tar.gz#md5=349d2b02618d3d39e5c6aede36fe3c1a
[15]: https://pypi.python.org/packages/e8/13/d0b0599099d6cd23663043a2a0bb7c61e58c6ba359b2656e6fb000ef5b98/pexpect-4.2.1.tar.gz#md5=3694410001a99dff83f0b500a1ca1c95
[16]: https://download.sysinternals.com/files/SDelete.zip
[20]: https://github.com/mmgen/MMGenLive
[11]: https://github.com/bitcoin-core/secp256k1/archive/master.zip
[31]: https://sourceforge.net/projects/mingw/files/MinGW/Extension/autoconf/autoconf2.5/autoconf2.5-2.68-1/autoconf2.5-2.68-1-mingw32-bin.tar.lzma
[32]: https://sourceforge.net/projects/mingw/files/MinGW/Extension/automake/automake1.11/automake1.11-1.11.1-1/automake1.11-1.11.1-1-mingw32-bin.tar.lzma
[33]: https://sourceforge.net/projects/mingw/files/MinGW/Extension/libtool/libtool-2.4-1/libtool-2.4-1-mingw32-bin.tar.lzma
