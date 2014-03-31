MMGen = Multi-Mode GENerator
============================
##### a Bitcoin cold storage solution for the command line

Install MMGen and Its Dependencies on Microsoft Windows
-------------------------------------------------------

#### Install the Python interpreter:

Grab the [Windows 32-bit
installer](https://www.python.org/ftp/python/2.7.6/python-2.7.6.msi)
and run it, accepting the defaults.  Make sure the Python base directory is in
your [path](MMGenEditPathMSWin.md).

#### Build the Scrypt Python module:

Grab the [latest tarball](https://pypi.python.org/pypi/scrypt/)
from python.org.  Unpack to `C:\`, start the DOS prompt and run:

		cd \scrypt-0.6.1
		python setup.py build --compiler=mingw32
		python setup.py install

#### Build OpenSSL:

Grab the [latest tarball](http://www.openssl.org/source/openssl-1.0.1f.tar.gz)
from the [openssl.org download page](http://www.openssl.org/source/).  Unpack
to `C:\`, start your MSYS shell and run:

		$ cd /c/openssl-1.0.1f
		$ ./config
		$ make
		$ make install

#### Install the Pycrypto Python module:

Source code is available from the
[Pycrypto home page](https://www.dlitz.net/software/pycrypto/),
but it appears to build only with MS Visual Studio, not MinGW.
Until this situation is fixed, you can install the precompiled binaries
available from
[Voidspace](http://www.voidspace.org.uk/python/modules.shtml#pycrypto).
Download and run the
[Windows installer](http://www.voidspace.org.uk/downloads/pycrypto26/pycrypto-2.6.win32-py2.7.exe),
accepting the defaults.

#### Install the ecdsa Python module:

Grab the [tarball](https://pypi.python.org/pypi/ecdsa), unpack it, `cd` to the
archive root and run `python setup.py install`.

#### Install the bitcoin-python Python module:

Grab the [tarball](https://pypi.python.org/pypi/bitcoin-python/0.3),
unpack it, start your MSYS shell, `cd` to the archive root and run the command:

		$ cp -a src/bitcoinrpc /c/Python27/Lib/site-packages

This is a workaround for the standard setup command, which fails here
due to a dependency problem.  If your Python is installed in a different
location, you'll have to adjust the destination path accordingly.
