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
sections entitled “Offline users”.  When doing an online install you may skip
over these sections.

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

> Optionally download and edit your mirror lists as described in **Offline
> users** below.

> Update the package database and core system packages:

		$ pacman -Syu

> Exit and restart the terminal.  If you’re using custom mirror lists, they were
> overwritten by the update operation, so you must restore them from your
> modified versions.

> Now complete updating the packages:

		$ pacman -Su

#### Offline users:

> You must now download the required database and package files from the
> Internet on your online computer and copy them to your offline box.  A USB
> flash drive works ideally for this.

> It’s highly recommended to update the mirror list files located in the
> directory `/etc/pacman.d`, as these lists allow you to specify the servers
> you’ll be downloading from.  To view the contents of these files, issue the
> following commands in your terminal:

		$ cat /etc/pacman.d/mirrorlist.msys
		$ cat /etc/pacman.d/mirrorlist.mingw64
		$ cat /etc/pacman.d/mirrorlist.mingw32

> Note that the first-listed server is the one used by default.  On your online
> computer, download more recent versions of these files from the MSYS2 Github
> repository:

>> <https://raw.githubusercontent.com/msys2/MSYS2-packages/master/pacman-mirrors/mirrorlist.msys>  
>> <https://raw.githubusercontent.com/msys2/MSYS2-packages/master/pacman-mirrors/mirrorlist.mingw64>  
>> <https://raw.githubusercontent.com/msys2/MSYS2-packages/master/pacman-mirrors/mirrorlist.mingw32>

> Optionally edit the files using a text editor such as Notepad, placing the
> server you wish to use first in the list.  Security-conscious users will
> prefer the HTTPS servers.  The yandex mirror seems to be the fastest as of
> this writing.  Now transfer the mirror files to your offline computer,
> replacing the old ones at `C:\\msys64\etc\pacman.d`.  You can check that the
> files have indeed been replaced by reissuing the `cat` commands above.

> You need to update your database files as well.  The database files and their
> associated signature files can be listed by issuing the following command:

		$ ls /var/lib/pacman/sync

> Download up-to-date versions of these files from the MSYS2 project site:

>> <https://downloads.sourceforge.net/project/msys2/REPOS/MSYS2/x86_64/msys.db>  
>> <https://downloads.sourceforge.net/project/msys2/REPOS/MSYS2/x86_64/msys.db.sig>  
>> <https://downloads.sourceforge.net/project/msys2/REPOS/MINGW/x86_64/mingw64.db>  
>> <https://downloads.sourceforge.net/project/msys2/REPOS/MINGW/x86_64/mingw64.db.sig>  
>> <https://downloads.sourceforge.net/project/msys2/REPOS/MINGW/i686/mingw32.db>  
>> <https://downloads.sourceforge.net/project/msys2/REPOS/MINGW/i686/mingw32.db.sig>

> Copy the files to your offline machine as you did with the mirror files, replacing
> the originals at `C:\msys64\var\lib\pacman\sync`.

> Now issue the following command:

		$ pacman -Sup

> This will produce a list of download URLs.  If you add `> urls.txt` to the end
> of this command, its output will be saved in the file `urls.txt`, which you
> can then copy to your online machine.  (This redirection trick works for most
> shell commands, by the way.)  On your online machine, download the files
> listed in `urls.txt`.  Transfer the downloaded files to your offline machine,
> copying them to the package cache directory `C:\msys64\var\cache\pacman\pkg`.

> Now issue the following command to perform the initial upgrade:

		$ pacman -Su

> When the process is finished, close your terminal window as requested and
> reopen another one.  Your mirror lists may have been overwritten by the
> upgrade operation, in which case you should restore them from your modified
> versions.

> Now reissue the `pacman -Sup` command, which will generate a much longer list
> of URLs this time.  Download and copy the listed files to the package cache
> directory just as you did with the previous list.  Invoke `pacman -Su` once
> again to complete your system upgrade. 

### 4. Install MSYS2 MMGen dependencies

Now that your system’s fully up to date, you’re ready to install the packages
specifically required by MMGen.

#### Offline users:

> The command `pacman -S <pgknames>` installs the requested MSYS2 packages,
> while `pacman -Sp <pgknames>` prints a list of download URLs for the packages
> and their dependencies.  So before running the command shown below, you’ll
> first need to issue it with `-Sp` instead of `-S` to produce a URL list.
> Download these URLs on your online machine and copy the downloaded files to
> the package cache directory of your offline machine just as you did with the
> system upgrade.

Install the packages and their dependencies:

	$ pacman -S tar git nano vim autoconf automake-wrapper autogen \
		mingw64/mingw-w64-x86_64-libtool \
		mingw64/mingw-w64-x86_64-pcre \
		mingw64/mingw-w64-x86_64-make \
		mingw64/mingw-w64-x86_64-python3-cryptography \
		mingw64/mingw-w64-x86_64-python3-six \
		mingw64/mingw-w64-x86_64-python3-pexpect \
		mingw64/mingw-w64-x86_64-python3-gmpy2 \
		mingw64/mingw-w64-x86_64-libsodium \
		mingw64/mingw-w64-x86_64-python3-pynacl \
		mingw64/mingw-w64-x86_64-python3-pip \
		mingw64/mingw-w64-x86_64-gcc

### 5. Set up your environment

Create the `/usr/local/bin` directory.  This is where you’ll place various
binaries required by MMGen:

	$ mkdir -p /usr/local/bin  # seen by Windows as C:\\msys64\usr\local\bin

Open your shell’s runtime configuration file in a text editor:

	$ nano ~/.bashrc

Add the following two lines to the end of the file, save and exit:

	export PATH="/mingw64/bin:$PATH:/c/Program Files/Bitcoin/daemon:/c/Program Files/Litecoin/daemon:/c/Program Files/Bitcoin-abc/daemon"
	export PYTHONUTF8=1

Close and reopen the terminal window to update your working environment.

### 6. Install MMGen dependencies not provided by MSYS2

Three of MMGen’s Python dependencies, `ecdsa`, `py_ecc` and `mypy_extensions`,
are not provided by MSYS2.  If you’re online, you can install them using the pip
package installer as follows:

	$ pip3 install --no-deps ecdsa==0.13 py_ecc==1.6.0 mypy_extensions==0.4.1

For an offline install, first download the packages on your online machine like
this:

	$ pip3 download --no-deps ecdsa==0.13 py_ecc==1.6.0 mypy_extensions==0.4.1

Then transfer the `*.whl` files to your offline machine, `cd` to the directory
containing the files and install them as follows:

	$ pip3 install --no-deps *.whl

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

### 8. Install the secp256k1 library

On your online machine, clone the repository:

	$ git clone https://github.com/bitcoin-core/secp256k1.git

If you’re doing an offline install, copy the cloned secp256k1 directory
to your offline machine.

Enter the directory, configure, build and install:

	$ cd secp256k1
	$ libtoolize
	$ ./autogen.sh
	$ ./configure
	$ mingw32-make.exe install MAKE=mingw32-make LIBTOOL=$(which libtool) 

### 9. Install the sdelete utility (required for secure wallet deletion)

Grab the latest SDelete [zip archive][sd], and unzip and copy `sdelete.exe` to
`/usr/local/bin`.  You must run the program once manually to accept the license
agreement.  Failing to do this will cause some scripts to hang, so you should do
it now.

### 10. Install MMGen

Now you’re ready to install MMGen itself.  On your online machine, clone the
repository:

	$ git clone https://github.com/mmgen/mmgen
	Cloning into ’mmgen’...

If you’re doing an offline install, you can then copy the cloned mmgen directory
to your offline machine.

Enter the directory and install:

	$ cd mmgen
	$ git checkout stable_msys2 # See 'Note' below
	$ ./setup.py install

**Note:** if you want to use features that have appeared since the latest
`stable_msys2` release, then you can omit the `git checkout` step and remain on
the `master` branch.  But please be aware that security vulnerabilities are more
likely to be present in new code than in a stable release.  In addition, while
the tip of `master` is always tested on Linux before being pushed to the public
repository, it’s not guaranteed to install or run on MSYS2.  Installation or
runtime issues may also arise due to missing dependencies or installation steps
not yet covered in the documentation.

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

To transact ETH, ETC or ERC20 tokens you’ll need the latest Windows `parity.exe`
binary from the [Parity Github repository][pg].  Parity, unlike the other coin
daemons, needs to be installed on the online machine only.  Copy the binary to
your executable path, preferably `/usr/local/bin`.

Typically you’ll wish to launch Parity as follows:

	$ parity.exe --jsonrpc-apis=all

More information on Parity’s command-line options can be found [here][pl].

### 12. You’re done!

Congratulations, your installation is now complete, and you can proceed to
[**Getting Started with MMGen**][gs].  Note that all features supported by
MMGen on Linux, except for [autosigning][ax], are now supported on MSYS2 too.
Please be aware of the following, however:

+ Non-ASCII filenames cannot be used with the Monero wallet syncing tool.  This
  appears to be an issue with the Monero wallet RPC daemon rather than MMGen.

[mh]: https://www.msys2.org
[mp]: https://sourceforge.net/projects/msys2
[mw]: https://github.com/msys2/msys2/wiki
[ov]: https://github.com/mmgen/mmgen/releases/tag/v0.9.8
[sd]: https://download.sysinternals.com/files/SDelete.zip
[pg]: https://github.com/paritytech/parity-ethereum/releases
[di]: Deprecated-MSWin-Installation
[ib]: Install-Bitcoind
[gs]: Getting-Started-with-MMGen
[pl]: Altcoin-and-Forkcoin-Support#a_par
[ax]: autosign-[MMGen-command-help]
[mc]: Altcoin-and-Forkcoin-Support#a_xmr
