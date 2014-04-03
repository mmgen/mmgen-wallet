MMGen = Multi-Mode GENerator
============================
##### a Bitcoin cold storage solution for the command line

Install MMGen and Its Dependencies on Microsoft Windows
-------------------------------------------------------

##### Note: The following instructions assume you'll be unpacking all archives to `C:\`, the root directory on most Windows installations.  If you choose to unpack to another location, the `cd` commands must be adjusted accordingly.

#### 1. Install the Python interpreter:

Grab the [Windows 32-bit installer][09] and run it, accepting the defaults.
Add the Python base and Scripts directories to your [path][08], e.g.
`C:\Python27;C:\Python27\Scripts`.

#### 2. Build OpenSSL:

Grab the [latest tarball][06] from the [openssl.org download page][05] and unpack
it. At the MSYS prompt, run:

		$ cd /c/openssl-1.0.1f
		$ ./config --openssldir=/usr
		$ make
		$ make install

#### 3. Build the Scrypt Python module:

Grab the [latest tarball][07] from python.org and unpack it. At the MSYS prompt,
run:

		$ cd /c/scrypt-0.6.1

Open `setup.py` in your text editor and make the following changes:

> Change the line:

			library_dirs = ['c:\OpenSSL-Win32\lib\MinGW']

> to read:

			library_dirs = ['c:\msys\lib','c:\WINDOWS\system32']

> Change the line:

			includes = ['c:\OpenSSL-Win32\include']

> to read:

			includes = ['c:\msys\include']

Save the file. At the MSYS prompt, run:

		$ python setup.py build --compiler=mingw32

Ignore the warning messages at the end and run:

		$ python setup.py install

#### 4. Install the Pycrypto Python module:

Source code is available from the [Pycrypto home page][00], but it appears to
build only with MS Visual Studio, not MinGW.  Until this situation is fixed,
you can install the precompiled binaries available from [Voidspace][01].
Download and run the [Windows installer][02], accepting the defaults.

#### 5. Install the ecdsa Python module:

Grab the [tarball][03] and unpack it.  At the MSYS prompt, run:

		$ cd /c/ecdsa-0.11
		$ python setup.py install

#### 6. Install the bitcoin-python Python module:

Grab the [tarball][04] and unpack it.  At the MSYS prompt, run:

		$ cd /c/bitcoin-python-0.3
		$ cp -a src/bitcoinrpc /c/Python27/Lib/site-packages

This is a workaround for a dependency issue with the package's setup script.
If your Python is installed in a different location, you'll have to adjust the
destination path accordingly.

#### 7. Install MMGen:

Get the [zip archive][10] from GitHub and unpack it.  At the MSYS prompt, run:

		$ cd /c/mmgen-master
		$ sudo ./setup.py install

Type:

		$ echo $PATH

The `C:\Python27;C:\Python27\Scripts` you added to your path in Step 1 of this
page should be included in your PATH variable.  If not, then exit MSYS and open
a new MSYS window to update your path.

The MMGen commands beginning with `mmgen-` will now be available (type
`mmgen-<TAB>` to test) and you may begin experimenting with MMGen as described
in the first two steps of [Getting Started with MMGen][13].

[00]: https://www.dlitz.net/software/pycrypto/
[01]: http://www.voidspace.org.uk/python/modules.shtml#pycrypto
[02]: http://www.voidspace.org.uk/downloads/pycrypto26/pycrypto-2.6.win32-py2.7.exe)
[03]: https://pypi.python.org/pypi/ecdsa
[04]: https://pypi.python.org/pypi/bitcoin-python/0.3
[09]: https://www.python.org/ftp/python/2.7.6/python-2.7.6.msi
[08]: MMGenEditPathMSWin.md
[07]: https://pypi.python.org/pypi/scrypt/
[06]: http://www.openssl.org/source/openssl-1.0.1f.tar.gz
[05]: http://www.openssl.org/source/
[10]: https://github.com/mmgen/mmgen/archive/master.zip
[11]: http://slproweb.com/download/Win32OpenSSL-1_0_1f.exe
[12]: http://www.openssl.org/related/binaries.html
[13]: MMGenGettingStarted.md
