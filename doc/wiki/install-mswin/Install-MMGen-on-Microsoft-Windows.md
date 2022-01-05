## Introduction

MMGen is supported on Microsoft Windows via [MSYS2][mh], which provides a
Unix-like command-line environment within Windows.  Windows 7 and later versions
are supported.

MSYS2 is the successor project to MinGW-64 and the earlier MSYS, bringing many
improvements such as package management and support for Python 3.  The MSYS2
project page is located [here][mp] and its wiki [here][mw].

*Note: an [older version][ov] of MMGen can be run under MinGW-64 and MSYS, but
its use is deprecated.  Installation instructions for MMGen under MinGW-64 and
MSYS are archived [here][di] for historical interest only.*

Before you get started, just a reminder that MMGen must be installed on two
computers, one online and one offline, if you want to use it securely.  All
operations involving private data—wallet generation, address generation and
transaction signing—are handled offline, while the online installation takes
care of tracking balances and creating and sending transactions.

This means that once you’ve finished the install process, the computer you’ve
designated for offline use must be taken offline **permanently.** Furthermore,
its wi-fi and bluetooth interfaces should be disabled as well to safeguard
against the possibility of private data leakage.

With some extra steps, it’s possible to perform the installation on a machine
that’s *already* offline.  These steps will be additionally outlined in
sections entitled **Offline install.**  When doing an online install you may
skip over these sections.

### 1. Install MSYS2

Download the MSYS2 executable installer for your architecture from the [MSYS2
homepage][mh], but ignore the installation instructions there.

Run the installer, accepting all defaults.  At the end of the installation,
uncheck “Run MSYS2 now” and click Finish.

### 2. Set up PowerShell as your MSYS2 terminal

MMGen is incompatible with the terminal provided by the MSYS2 project.  However,
it works just fine with Windows’ native PowerShell.

Drag or copy a PowerShell icon to the desktop, rename it to “MSYS2”, then right
click the icon and select Properties.  After the existing path in the Target
text window, append a space followed by the text `C:\\msys64\usr\bin\bash.exe
--login`

Save your changes and double click the icon to launch your MSYS2-enabled
PowerShell.  From now on, all your work will be done in this terminal.

Note that the root of your MSYS2 installation is located in `C:\\msys64`, so the
following commands, for example:

		$ ls /etc              # the path as seen within MSYS2
		$ ls 'C:\\msys64\etc'  # the path as seen by Windows

will produce a listing of the same directory.

### 3. Upgrade MSYS2

#### Online users:

> Optionally edit your mirror lists as described in **Offline install** below.

> Update the package database and core system packages:

		$ pacman -Syu

> Exit and restart the terminal.  If you’re using modified mirror lists, they
> may have been overwritten by the update operation, in which case you should
> restore them from your modified versions.

> Now complete upgrading the system:

		$ pacman -Su

#### Offline install:

> You must now download the required database and package files from the
> Internet on your online computer and copy them to your offline box.  A USB
> flash drive works ideally for this.

> The mirror list files located in the directory `/etc/pacman.d` specify the
> servers to download packages from.

> The server that’s listed first in these files is the one that will used by
> default, so you may wish to edit them and place the server you wish to use
> first in the list.  For this you may use a text editor such as Notepad:

		$ notepad /etc/pacman.d/mirrorlist.msys
		... repeat for remaining mirrorlist files ...

> You need to update your database files as well.  The database files and their
> associated signature files can be listed by issuing the following command:

		$ ls /var/lib/pacman/sync

> Download up-to-date versions of these files from a fast MSYS2 mirror:

>> <https://mirror.yandex.ru/mirrors/msys2/msys/x86_64/msys.db>  
>> <https://mirror.yandex.ru/mirrors/msys2/msys/x86_64/msys.db.sig>  
>> <https://mirror.yandex.ru/mirrors/msys2/mingw/x86_64/mingw64.db>  
>> <https://mirror.yandex.ru/mirrors/msys2/mingw/x86_64/mingw64.db.sig>  
>> <https://mirror.yandex.ru/mirrors/msys2/mingw/i686/mingw32.db>  
>> <https://mirror.yandex.ru/mirrors/msys2/mingw/i686/mingw32.db.sig>  
>> <https://mirror.yandex.ru/mirrors/msys2/mingw/clang64/clang64.db>  
>> <https://mirror.yandex.ru/mirrors/msys2/mingw/clang64/clang64.db.sig>  
>> <https://mirror.yandex.ru/mirrors/msys2/mingw/ucrt64/ucrt64.db>  
>> <https://mirror.yandex.ru/mirrors/msys2/mingw/ucrt64/ucrt64.db.sig>

> Copy the files to your offline machine, replacing the originals at
> `C:\msys64\var\lib\pacman\sync`.

> Now issue the following command:

		$ pacman -Sup > urls.txt

> This command may cause your MSYS terminal window to close.  If so, just
> reopen another one.

> The command's output is now saved in the file `urls.txt` (this redirection
> trick using '>' works for most shell commands, by the way).  Copy `urls.txt`
> to your online machine and download the URLs listed in it.

> Create a new folder on your offline machine:

		$ mkdir packages1

Transfer the downloaded package files to the offline machine and place them in
this folder.

> Now issue the following command to install the packages:

		$ pacman -U packages1/*

> When the process is finished, close your terminal window and reopen another
> one.

> Now reissue the `pacman -Sup` command, which will generate a much longer list
> of URLs this time.  Repeat the same download/copy/install procedure with the
> new URLs, only using a new `packages2` directory instead of `packages1`.

> Your system upgrade is now complete.

### 4. Install MSYS2 MMGen dependencies

Now that your system’s fully up to date, you’re ready to install the packages
specifically required by MMGen.

#### Offline install:

> As you’ve probably noticed by now, the command `pacman -S <pgknames>`
> installs MSYS2 packages and their dependencies, while `pacman -Sp
> <pgknames>` prints a list of download URLs for the same packages and
> dependencies.  So before running the command shown below, you must first
> issue it with `-Sp` instead of `-S` to produce a URL list. Then repeat the
> above download/copy/install steps once again with the new URLs, replacing
> `packages2` with `packages3`.

Install the MMGen requirements and their dependencies:

	$ pacman -S tar git vim autoconf automake-wrapper autogen libtool \
		mingw64/mingw-w64-x86_64-python-build \
		mingw64/mingw-w64-x86_64-python-wheel \
		mingw64/mingw-w64-x86_64-python-pip \
		mingw64/mingw-w64-x86_64-libltdl \
		mingw64/mingw-w64-x86_64-gcc \
		mingw64/mingw-w64-x86_64-make \
		mingw64/mingw-w64-x86_64-pcre \
		mingw64/mingw-w64-x86_64-libsodium \
		mingw64/mingw-w64-x86_64-python-cryptography \
		mingw64/mingw-w64-x86_64-python-six \
		mingw64/mingw-w64-x86_64-python-pexpect \
		mingw64/mingw-w64-x86_64-python-gmpy2 \
		mingw64/mingw-w64-x86_64-python-pynacl \
		mingw64/mingw-w64-x86_64-python-pysocks \
		mingw64/mingw-w64-x86_64-python-requests

### 5. Set up your environment

Create the `/usr/local/bin` directory.  This is where you’ll place various
binaries required by MMGen:

	$ mkdir -p /usr/local/bin  # seen by Windows as C:\\msys64\usr\local\bin

Open your shell’s runtime configuration file in a text editor:

	$ notepad ~/.bashrc

Add the following two lines to the end of the file (if this is a Bitcoin-only
installation, you may omit the Litecoin and Bitcoin Cash Node components of the
path):

	export PATH="/mingw64/bin:$PATH:/c/Program Files/Bitcoin/daemon:/c/Program Files/Litecoin/daemon:/c/Program Files/Bitcoin-Cash-Node/daemon"
	export PYTHONUTF8=1

Save and exit.  Close and reopen the terminal window to update your working
environment.

### 6. Install the Python ECDSA library (offline install only)

On your online machine:

	$ pip3 download ecdsa

Copy the downloaded file to your offline machine and install:

	$ pip3 install --user ecdsa-*.whl

### 7. Install the standalone scrypt package (required for strong password hashing)

Thanks to a faulty implementation of the `scrypt` function included in Python’s
`hashlib`, the standalone `scrypt` module is required for stronger-than-default
password hashing, i.e. hash presets greater than `3`.  Installing the package is
therefore highly recommended.

On your online machine, download the tar archive:

	$ pip3 download --no-deps scrypt==0.8.13

On your offline machine, unpack and enter the archive:

	$ tar fax scrypt-0.8.13.tar.gz
	$ cd scrypt-0.8.13

Open the file `setup.py` in your text editor.  Right before the line beginning
with:

	scrypt_module = Extension(

add the following line (with no indentation):

	includes = ['/mingw64/include']

Also change the line:

	libraries = ['libcrypto_static']

to read:

	libraries = ['libcrypto']

Save the file and exit the editor.  Now build and install:

	$ python3 setup.py build --compiler=mingw32
	$ python3 setup.py install

### 8. Clone and copy the secp256k1 library (offline install only)

On your online machine, clone the secp256k1 repository from Github:

	$ git clone https://github.com/bitcoin-core/secp256k1.git

On your offline machine, create a magic location and copy the cloned secp256k1
directory into it:

	$ mkdir -p ~/.cache/mmgen
	$ cp -a /path/to/secp256k1/repo/secp256k1 ~/.cache/mmgen
	$ ls ~/.cache/mmgen/secp256k1/autogen.sh # check that the location is correct

### 9. Install MMGen

Now you’re ready to install MMGen itself.  On your online machine, clone the
repository:

	$ git clone https://github.com/mmgen/mmgen
	Cloning into ’mmgen’...

If you’re doing an offline install, then copy the cloned mmgen directory to
your offline machine.

Enter the repo directory and build:

	$ cd mmgen
	$ git checkout stable_msys2 # See 'Note' below
	$ python3 -m build --no-isolation

Exit the repo directory and install:

	$ cd ..
	$ python3 -m pip install --upgrade mmgen/dist/*.whl

**Note:** if you want to use features that have appeared since the latest
`stable_msys2` release, then you can omit the `git checkout` step and remain on
the `master` branch.  Please bear in mind, however, that security
vulnerabilities are more likely to be present in new code than in a stable
release.  In addition, while the tip of `master` is always tested on Linux
before being pushed to the public repository, it’s not guaranteed to install or
run on MSYS2.  Installation or runtime issues may also arise due to missing
dependencies or installation steps not yet covered in the documentation.

### 10. Install Python Ethereum dependencies (Ethereum users only)

If you’ll be using MMGen with Ethereum, then you must install a few
dependencies.  From the MMGen repository root, type the following:

	$ pip3 install --no-deps --user -r eth-requirements.txt

For an offline install, do this instead:

	$ pip3 download --no-deps -r eth-requirements.txt

Then transfer the downloaded files to your offline machine, `cd` to the
directory containing the files and install them as follows:

	$ pip3 install --no-deps --user *.whl

### 11. Install and launch your coin daemons

At this point your MMGen installation will be able to generate wallets, along
with keys and addresses for all supported coins.  However, if you intend to do
any transacting, as you probably do, you’ll need to install and launch a coin
daemon or daemons.  MMGen has full transaction support for BTC, BCH, LTC, ETH,
ETC and ERC20 tokens.

Go to the [**Install Bitcoind and other supported coin daemons**][ib] wiki page
and follow the instructions for your coins of choice.  You can skip the parts
about adding to the Windows path, since your `PATH` variable was taken care of
in Step 5.  Note that the daemons must be installed on both your online and
offline machines.

To transact ETH, ETC or ERC20 tokens you’ll need the latest OpenEthereum binary
build for Windows from the [OpenEthereum Github repository][og].  OpenEthereum,
unlike the other coin daemons, is installed on the online machine only.  Copy
the `openethereum.exe` and `ethkey.exe` binaries to `/usr/local/bin`.  Please
note that OpenEthereum performs very poorly under Windows due to threading
limitations.  Unless you have very fast hardware, transacting and syncing the
blockchain could be painfully slow.

Typically you’ll wish to launch OpenEthereum as follows:

	$ openethereum.exe --jsonrpc-apis=all

More information on OpenEthereum’s command-line options can be found [here][pl].

### 12. You’re done!

Congratulations, your installation is now complete, and you can proceed to
[**Getting Started with MMGen**][gs].  Note that all features supported by
MMGen on Linux, except for [autosigning][ax], are now supported on MSYS2 too.
Please be aware of the following, however:

+ Non-ASCII filenames cannot be used with the Monero wallet syncing tool.  This
  is an issue with the Monero wallet RPC daemon rather than MMGen.

+ The Bitcoin Cash Node daemon cannot handle non-ASCII pathnames.  This is an
  issue with the Bitcoin Cash Node implementation for Windows, not MMGen.

[mh]: https://www.msys2.org
[mp]: https://sourceforge.net/projects/msys2
[mw]: https://github.com/msys2/msys2/wiki
[ov]: https://github.com/mmgen/mmgen/releases/tag/v0.9.8
[sd]: https://download.sysinternals.com/files/SDelete.zip
[og]: https://github.com/openethereum/openethereum/releases
[di]: Deprecated-MSWin-Installation
[ib]: Install-Bitcoind
[gs]: Getting-Started-with-MMGen
[pl]: Altcoin-and-Forkcoin-Support#a_oe
[ax]: autosign-[MMGen-command-help]
[mc]: Altcoin-and-Forkcoin-Support#a_xmr
