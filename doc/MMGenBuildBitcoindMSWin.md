MMGen = Multi-Mode GENerator
============================
##### a Bitcoin cold storage solution for the command line

Build Bitcoind on Microsoft Windows
-----------------------------------

#### Build the Berkeley Database (v5.0):

Grab the [v5.0 tarball][01], or browse the [download page][02] for different
versions.  Unpack the archive to `C:\` and execute the following from your MSYS
shell:

		$ cd /c/db-5.0.32/build_unix
		$ ../dist/configure --enable-mingw --enable-cxx --disable-replication

Edit the source file `db.h` in the `build_unix` directory, moving to line 113
and replacing the statement `typedef pthread_t db_threadid_t;` with `typedef
u_int32_t db_threadid_t;`.

Since the script creates the file, this must be done **after** the configure
script is run.  Now execute:

		$ make
		$ make install

#### Install the MASM assembler (optional but recommended):

Get the file [MASMsetup.exe][03] from the Microsoft website.  With a tool
like 7zip, open the cab file inside and the file inside it, which begins with
`FL_ml_exe`.  Copy this file to your path, renaming it to `ml.exe`.

#### Build the Boost libraries:

Browse the [download page][06], or get the [tarball][04] from sourceforge.
Unpack `boost_1_55_0.tar.gz` to `C:\`, and type the following from your DOS
prompt:

		cd \boost_1_55_0
		boostrap.bat
		bjam toolset=gcc link=static threading=single --build-type=minimal stage --with-system --with-filesystem --with-program_options --with-chrono --with-test
		bjam toolset=gcc link=static threading=multi --build-type=minimal stage --with-thread

These commands build just the few libraries we need, avoiding the time-consuming
process of building the whole boost package.

#### Build Bitcoind:

Download Sipa's watchonly bitcoind [tarball][05] from GitHub and unzip it
to `C:\`.

From the MSYS prompt:

		$ cd /c/bitcoin-watchonly

Add the following lines to the end of `src/leveldb/build_detect_platform`:

		$ echo "DIRS=$DIRS" >> $OUTPUT
		$ echo "PORT_FILE=$PORT_FILE" >> $OUTPUT

Make the following changes to `src/leveldb/Makefile`:

> After the line `include build_config.mk` add the following line:

			SOURCES=$(shell for i in $(DIRS); do echo $$i/*.cc; done)

> Change the line `LIBOBJECTS = $(SOURCES:.cc=.o)`
> to read         `LIBOBJECTS = $(SOURCES:.cc=.o) $(PORT_FILE:.cc=.o)`

> Change the line `all: $(SHARED) $(LIBRARY)`
> to read         `all: $(LIBRARY)`

For each of the following files:

		src/rpcdump.cpp
		src/rpcnet.cpp
		src/rpcwallet.cpp
		src/wallet.cpp
		src/walletdb.cpp

add the line `#include <winsock2.h>` at the beginning, before the first
`#include` statement.

In the following files:

		src/leveldb/db/db_test.cc
		src/leveldb/db/db_bench.cc
		src/leveldb/db/autocompact_test.cc
		src/leveldb/db/leveldb_main.cc

delete everything from `int main(int argc,..` to the end of the file.

Do the following file-copying operations (needs to be done just once):

		$ cp /mingw/bin/autoreconf-2.68 /mingw/bin/autoreconf
		$ cp /mingw/bin/autoconf-2.68 /mingw/bin/autoconf
		$ cp /mingw/bin/automake-1.11 /mingw/bin/automake
		$ cp /mingw/bin/aclocal-1.11 /mingw/bin/aclocal

Generate the `configure` script:

		$ sh autogen.sh

Edit the just-created `configure` script:

> After the line:

			LIBS="$LIBS $BOOST_LIBS $BOOST_CHRONO_LIB"

> add the line:

			CPPFLAGS="$CPPFLAGS $BOOST_CPPFLAGS"

Export variables for `configure` to pass to the preprocessor and linker:

		$ export CPPFLAGS="-I/usr/local/BerkeleyDB.5.0/include -I/usr/local/ssl/include"
		$ export LDFLAGS="-static -L/usr/local/BerkeleyDB.5.0/lib -L/usr/local/ssl/lib"
		$ export BOOST_ROOT=/c/boost_1_55_0

Run `configure` and then `make`:

		$ ./configure --without-qt --with-incompatible-bdb
		$ make src/bitcoind.exe

Strip the executable (`strip src/bitcoind.exe`), copy it to your path and test
by running `bitcoind`.  You may need to supply an argument to the `-datadir`
option so the daemon can find your wallet and configuration file.

[01]: http://download.oracle.com/berkeley-db/db-5.0.32.tar.gz
[02]: http://www.oracle.com/technetwork/database/database-technologies/berkeleydb/downloads/index-082944.html
[03]: http://www.microsoft.com/en-gb/download/details.aspx?id=12654
[04]: http://sourceforge.net/projects/boost/files/boost/1.55.0/boost_1_55_0.tar.gz/download
[05]: https://codeload.github.com/sipa/bitcoin/zip/watchonly
[06]: http://www.boost.org/users/download/
