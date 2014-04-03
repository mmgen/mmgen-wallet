MMGen = Multi-Mode GENerator
============================
##### a Bitcoin cold storage solution for the command line

Build Bitcoind on Microsoft Windows
-----------------------------------

##### Note: If during the compilation process you get "Missing Disk" pop-up error messages and have a card reader installed, you should temporarily disconnect your card reader.

##### Note: The following instructions assume you'll be unpacking all archives to `C:\`, the root directory on most Windows installations.  If you choose to unpack to another location, the `cd` commands must be adjusted accordingly.

#### 1. Build OpenSSL

Note: Skip this step if you already built OpenSSL in Step 2 of [**Install MMGen
and Its Dependencies**][07].

Grab the [latest tarball][06] from the [openssl.org download page][05] and unpack
it. At the MSYS prompt, run:

		$ cd /c/openssl-1.0.1f
		$ ./config --openssldir=/usr
		$ make
		$ make install

#### 2. Build the Berkeley Database (v5.0):

Grab the [v5.0 tarball][01], or browse the [download page][02] for other
versions (avoid v4.8, which has issues with Windows; versions newer than 5.0
may work, but they're untested by the author).  Unpack the archive and run
the following at the MSYS prompt:

		$ cd /c/db-5.0.32/build_unix
		$ ../dist/configure --enable-mingw --enable-cxx --disable-replication --prefix=/usr

Edit the source file `db.h` in the `build_unix` directory, move to line 116 and
change:

		typedef pthread_t db_threadid_t;

to:

		typedef u_int32_t db_threadid_t;

**Note:** since `db.h` is created by `configure`, this must be done **after**
`configure` is run.

Now run `make` and `make install`.

#### 3. Install the MASM assembler (optional but recommended):

Get the file [MASMsetup.exe][03] from the Microsoft website.  With a tool
like 7zip, open the cab file inside and the file inside it, which begins with
`FL_ml_exe*`.  Copy this file to your path, renaming it to `ml.exe`.

#### 4. Build the Boost libraries:

Get the boost [tarball][04] from sourceforge and unpack it.  At the DOS prompt,
run:

		cd \boost_1_55_0
		boostrap.bat
		bjam toolset=gcc link=static threading=single --build-type=minimal stage --with-system --with-filesystem --with-program_options --with-chrono --with-test
		bjam toolset=gcc link=static threading=multi --build-type=minimal stage --with-thread

These commands build just the few libraries you need, saving you from the
time-consuming process of compiling the whole boost package.

#### 5. Build Bitcoind:

Download Sipa's watchonly bitcoind [zip archive][05] (commit a13f1e8 [[check][]])
from GitHub and unpack it.  At the MSYS prompt, run:

		$ cd /c/bitcoin-watchonly

Make the following edits to `src/leveldb/Makefile`:

> After the the statement `include build_config.mk`, add the following line:

			SOURCES=$(shell echo db/*.cc util/*.cc table/*.cc)

> Change the line:

			LIBOBJECTS = $(SOURCES:.cc=.o)

> to read:

			LIBOBJECTS = $(SOURCES:.cc=.o) port/port_win.o

> Change the line:

			all: $(SHARED) $(LIBRARY)

> to read:

			all: $(LIBRARY)

Edit the following files,

		src/rpcdump.cpp
		src/rpcnet.cpp
		src/rpcwallet.cpp
		src/wallet.cpp
		src/walletdb.cpp

adding the statement `#include <winsock2.h>` near the top of each file, above
the first `#include` statement.

At the MSYS prompt, run the following file-copying commands (this needs to be
done just once):

		$ cp /mingw/bin/autoreconf-2.68 /mingw/bin/autoreconf
		$ cp /mingw/bin/autoconf-2.68 /mingw/bin/autoconf
		$ cp /mingw/bin/automake-1.11 /mingw/bin/automake
		$ cp /mingw/bin/aclocal-1.11 /mingw/bin/aclocal
		$ cp /bin/true.exe /bin/hexdump.exe

Generate the `configure` script:

		$ sh autogen.sh

Edit the just-created `configure` script, adding the line:

		CPPFLAGS="$CPPFLAGS $BOOST_CPPFLAGS"

after the line:

		LIBS="$LIBS $BOOST_LIBS $BOOST_CHRONO_LIB"

From the prompt, run `configure` and `make` with the arguments provided below:

		$ ./configure --without-qt --with-incompatible-bdb CPPFLAGS=-I/usr/include LDFLAGS="-static -L/usr/lib -Wl,--allow-multiple-definition" BOOST_ROOT=/c/boost_1_55_0
		$ make src/bitcoind.exe

Strip the executable (`strip src/bitcoind.exe`), copy it to your path and test
that the command `bitcoind` works.  You may want to use the `-datadir` option to
point to the location where you plan to put your `bitcoin.conf` file, wallet and
blockchain.

[01]: http://download.oracle.com/berkeley-db/db-5.0.32.tar.gz
[02]: http://www.oracle.com/technetwork/database/database-technologies/berkeleydb/downloads/index-082944.html
[03]: http://www.microsoft.com/en-gb/download/details.aspx?id=12654
[04]: http://sourceforge.net/projects/boost/files/boost/1.55.0/boost_1_55_0.tar.gz/download
[05]: https://codeload.github.com/sipa/bitcoin/zip/watchonly
[06]: http://www.boost.org/users/download/
[check]: https://github.com/sipa/bitcoin/tree/watchonly
[07]: MMGenInstallDependenciesMSWin.md
