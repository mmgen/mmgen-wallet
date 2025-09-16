## Table of Contents

#### [Introduction](#a_i)

#### [Install MSYS2 and MMGen Wallet](#a_m)
* [1. Install MSYS2](#a_ms)
* [2. Upgrade MSYS2](#a_ug)
	* [Online install](#a_ug1)
	* [Offline install](#a_ug2)
* [3. Install MMGen Wallet’s MSYS2 dependencies](#a_md)
	* [Offline install](#a_md1)
* [4. Set up your shell environment](#a_ev)
* [5. Choose your Python environment](#a_pev)
* [6. Install required Python packages](#a_pp)
* [7. Clone and copy the secp256k1 library (offline install only)](#a_se)
* [8. Install MMGen Wallet](#a_mm)
	* [Stable version](#a_mms)
	* [Development version](#a_mmd)
* [9. Install and launch your coin daemons](#a_cd)
* [10. You’re done!](#a_do)

#### [Keeping your installation up to date](#a_u)
* [Upgrading MSYS2](#a_us)
* [Upgrading MMGen Wallet](#a_um)
	* [Upgrade to latest stable version](#a_ums)
	* [Upgrade to latest development version](#a_umd)

## <a id="a_i">Introduction</a>

MMGen Wallet is supported on Microsoft Windows via [MSYS2][mh], which provides a
Unix-like command-line environment within Windows.  Windows 8.1 and later
versions are supported.

MSYS2 is the successor project to MinGW-64 and the earlier MSYS, bringing many
improvements such as package management and support for Python 3.  The MSYS2
project page is located [here][mp] and its wiki [here][mw].

Before you get started, just a reminder that MMGen Wallet must be installed on
two computers, one online and one offline.  All operations involving private
data—wallet generation, address generation and transaction signing—are handled
offline, while the online machine takes care of tracking balances and creating
and sending transactions.

This means that once you’ve finished the install process, the computer you’ve
designated for offline use must be taken offline **permanently.** Furthermore,
its wifi and bluetooth interfaces must be disabled as well to safeguard against
private data leakage.

With some extra steps, it’s possible to perform the installation on a machine
that’s *already* offline.  These steps will be additionally outlined in
sections entitled **Offline install.**  When doing an online install you will
ignore these sections.

## <a id="a_m">Install MSYS2 and MMGen Wallet</a>

### <a id="a_ms">1. Install MSYS2</a>

Download the MSYS2 executable installer for your architecture from the [MSYS2
homepage][mh], but ignore the installation instructions there.

Run the installer, accepting all defaults.  When installation completes,
uncheck ‘Run MSYS2 now’ and click ‘Finish’.  From the Start menu, drag the
‘MSYS2 UCRT64’ icon to the desktop.  You will use it to launch all MSYS2
terminal sessions from now on.  Double-click the icon to launch the terminal.

Note that the root of your MSYS2 installation is located in `C:\\msys64`, so the
following commands, for example, will produce a listing of the same directory:

```text
$ ls /etc              # the path as seen within MSYS2
$ ls 'C:\\msys64\etc'  # the path as seen by Windows
```

### <a id="a_ug">2. Upgrade MSYS2</a>

#### <a id="a_ug1">Online install:</a>

> Update the package database and core system packages:
>
> ```text
> $ pacman -Syu
> ```
>
> Exit and restart the MSYS2 terminal.  Complete upgrading the system:
>
> ```text
> $ pacman -Su
> ```

#### <a id="a_ug2">Offline install:</a>

> You must now download the required database and package files on your online
> computer and then copy them to your offline box.  A USB flash drive works
> ideally for this.
>
> Begin by updating the pacman database.  The database files and their
> associated signatures can be listed by issuing the following command:
>
> ```text
> $ ls /var/lib/pacman/sync
> ```
>
> Download up-to-date versions of these files from the primary MSYS2 mirror:
>
>> <https://mirror.msys2.org/msys/x86_64/msys.db>  
>> <https://mirror.msys2.org/msys/x86_64/msys.db.sig>  
>> <https://mirror.msys2.org/mingw/mingw64/mingw64.db>  
>> <https://mirror.msys2.org/mingw/mingw64/mingw64.db.sig>  
>> <https://mirror.msys2.org/mingw/mingw32/mingw32.db>  
>> <https://mirror.msys2.org/mingw/mingw32/mingw32.db.sig>  
>> <https://mirror.msys2.org/mingw/clang64/clang64.db>  
>> <https://mirror.msys2.org/mingw/clang64/clang64.db.sig>  
>> <https://mirror.msys2.org/mingw/clangarm64/clangarm64.db>  
>> <https://mirror.msys2.org/mingw/clangarm64/clangarm64.db.sig>  
>> <https://mirror.msys2.org/mingw/ucrt64/ucrt64.db>  
>> <https://mirror.msys2.org/mingw/ucrt64/ucrt64.db.sig>
>
> Copy the files to your offline machine, replacing the originals at
> `C:\msys64\var\lib\pacman\sync`.
>
> Now issue the following command:
>
> ```text
> $ pacman -Sup > urls.txt
> ```
>
> This command may cause your MSYS2 terminal window to close.  If so, just
> reopen another one.
>
> The command's output is now saved in the file `urls.txt` (this redirection
> trick using `>` works for most shell commands, by the way).  Copy `urls.txt`
> to your online machine and download the URLs listed in it.
>
> Create a new folder on your offline machine:
>
> ```text
> $ mkdir packages1
> ```
>
> Transfer the downloaded package files to the offline machine and place them in
> this folder.
>
> Now issue the following command to install the packages:
>
> ```text
> $ pacman -U packages1/*
> ```
>
> When the process is finished, close your terminal window and reopen another
> one.
>
> Now reissue the `pacman -Sup` command, which may or may not generate another
> list of URLs.  If it does, repeat the same download/copy/install procedure
> with the new URLs, only with a new `packages2` directory instead of
> `packages1`.
>
> Your system upgrade is now complete.

### <a id="a_md">3. Install MMGen Wallet’s MSYS2 dependencies</a>

Now you’re ready to install the packages specifically required by MMGen.

#### <a id="a_md1">Offline install:</a>

> As you’ve probably noticed by now, the command `pacman -S <pgknames>`
> downloads and installs MSYS2 packages and their dependencies, while `pacman
> -Sp <pgknames>` prints a list of download URLs for those same packages and
> dependencies.  Accordingly, you must issue the command below with `-Sp`
> instead of `-S` to produce a URL list.  Then repeat the above
> download/copy/install steps once again with the new URLs, downloading into
> a new directory, say `packages3`.

Install the MMGen Wallet dependencies:

```text
pacman -S tar git vim autoconf automake-wrapper autogen libtool cygrunsrv \
	mingw-w64-ucrt-x86_64-python-build \
	mingw-w64-ucrt-x86_64-python-wheel \
	mingw-w64-ucrt-x86_64-python-pip \
	mingw-w64-ucrt-x86_64-libltdl \
	mingw-w64-ucrt-x86_64-gcc \
	mingw-w64-ucrt-x86_64-make \
	mingw-w64-ucrt-x86_64-pcre \
	mingw-w64-ucrt-x86_64-libsodium \
	mingw-w64-ucrt-x86_64-python-pynacl \
	mingw-w64-ucrt-x86_64-python-cryptography \
	mingw-w64-ucrt-x86_64-python-pycryptodome \
	mingw-w64-ucrt-x86_64-python-six \
	mingw-w64-ucrt-x86_64-python-pexpect \
	mingw-w64-ucrt-x86_64-python-gmpy2 \
	mingw-w64-ucrt-x86_64-python-pysocks \
	mingw-w64-ucrt-x86_64-python-requests \
	mingw-w64-ucrt-x86_64-python-aiohttp \
	mingw-w64-ucrt-x86_64-python-pyreadline3 \
	mingw-w64-ucrt-x86_64-python-lxml
```

### <a id="a_ev">4. Set up your shell environment</a>

Create the `/usr/local/bin` directory.  This is where you’ll place various
binaries required by MMGen:

```text
$ mkdir -p /usr/local/bin  # seen by Windows as 'C:\\msys64\usr\local\bin'
```

Open your shell’s runtime configuration file in a text editor:

```text
$ nano ~/.bashrc
```

Add the following lines to the end of the file (if this is a Bitcoin-only
installation, you may omit the non-Bitcoin components of `daemon_paths`):

```bash
win_home="/${HOMEDRIVE/:}${HOMEPATH//\\//}"
daemon_paths="/c/Program Files/Bitcoin/daemon:/c/Program Files/Litecoin/daemon:/c/Program Files/Bitcoin-Cash-Node/daemon:/c/Program Files/Geth"
export PATH="$win_home/.local/bin:$PATH:$daemon_paths"
export PYTHONUTF8=1
```

Save and exit.  Close and reopen the terminal window to update your working
environment.

### <a id="a_pev">5. Choose your Python environment</a>

If you have other Python packages installed under MSYS2, then you may wish to
use a [virtual environment][vv] to keep your MMGen Wallet installation isolated
from them.

If you choose not to use a virtual environment, then you should add `--user` to
the command line every time you run `pip install` as directed below.  This will
prevent pip from installing packages in the system directory.

### <a id="a_pp">6. Install required Python packages</a>

On your online machine:

```text
$ python3 -m pip download ecdsa
$ python3 -m pip download --no-binary :all: scrypt==0.8.27 aiohttp==3.12.9

```

Copy the downloaded files to your offline machine (if applicable) and install:

```text
$ python3 -m pip install ecdsa-*.whl
$ python3 -m pip install --no-build-isolation scrypt*gz
$ python3 -m pip install --no-build-isolation aiohtt* multidic* yarl* aiohap* aiosig* attrs* frozenlist* idna* propcache*
```

### <a id="a_se">7. Clone and copy the secp256k1 library (offline install only)</a>

On your online machine, clone the secp256k1 repository from Github:

```text
$ git clone https://github.com/bitcoin-core/secp256k1.git
```

On your offline machine, create a magic location and copy the cloned secp256k1
directory to it:

```text
$ mkdir -p ~/.cache/mmgen                # the magic location
$ cp -a /path/to/secp256k1/repo/secp256k1 ~/.cache/mmgen
$ ls ~/.cache/mmgen/secp256k1/autogen.sh # check that files were correctly copied
```

### <a id="a_mm">8. Install MMGen Wallet</a>

Now you’re ready to install MMGen Wallet itself.

#### <a id="a_mms">Stable version:</a>

Online install:

> ```text
> $ python3 -m pip install mmgen-wallet
> ```

Offline install:

> ```text
> $ python3 -m pip download mmgen-wallet
> ```
>
> Copy the downloaded tar.gz archive to your offline machine.
>
> ```text
> $ python3 -m pip install --no-build-isolation mmgen-wallet.*tar.gz
> ```

#### <a id="a_mmd">Development version:</a>

*Bear in mind that security vulnerabilities are more likely to be present in
development code than in a stable release.  In addition, while the tip of
`master` is always tested on Linux before being pushed to the public repository,
it’s not guaranteed to run or even install on MSYS2.  Installation or runtime
issues may also arise due to missing dependencies or installation steps not yet
covered in the documentation.*

On your online machine, clone the MMGen Wallet repository:

```text
$ git clone https://github.com/mmgen/mmgen-wallet
Cloning into ’mmgen-wallet’...
```

Offline install:

> Copy the cloned mmgen-wallet directory to your offline machine.

Enter the repo directory, build and install:

```text
$ cd mmgen-wallet
$ python3 -m build --no-isolation
$ python3 -m pip install dist/*.whl
```

The `--force` and `--no-deps` options to `pip install` also come in handy on
occasion.

Note that MMGen Wallet has a test suite.  Refer to the [Test Suite][ts] wiki
page for details.

### <a id="a_cd">9. Install and launch your coin daemons</a>

At this point your installation will be able to generate wallets, along with
keys and addresses for all supported coins.  However, if you intend to do any
transacting, as you probably do, you’ll need to install and launch a coin daemon
or daemons.  MMGen Wallet has full transaction support for BTC, BCH, LTC, ETH,
ETC and ERC20 tokens.

Go to the [**Install Bitcoind and other supported coin daemons**][ib] wiki page
and follow the instructions for your coins of choice.  You can skip the parts
about adding to the Windows path, since your `PATH` variable was taken care of
in [Step 4](#a_ev).  Note that the daemons must be installed on both your
online and offline machines.

To transact ETH, ETC or ERC20 tokens you’ll need the latest Geth or Parity (for
Ethereum Classic) binary.  See the [**Altcoin-and-Forkcoin-Support**][pl] page
for information on downloading and launching these daemons.  The `parity.exe`
and `ethkey.exe` binaries should be copied to `/usr/local/bin`.  For Geth,
download and run the Windows installer and add `/c/Program Files/Geth` to the
end of the `PATH` variable in your `~/.bashrc` file:

Please note that Ethereum daemons perform rather poorly under Windows due to
threading limitations.  Unless you have very fast hardware, transacting and
syncing the blockchain will be painfully slow.

### <a id="a_do">10. You’re done!</a>

Congratulations, your installation is now complete, and you can proceed to
[**Getting Started with MMGen Wallet**][gs].  Note that all features supported
by MMGen Wallet on Linux and macOS, except for [autosigning][ax], are now
supported on MSYS2 too.  Please be aware of the following, however:

+ Non-ASCII filenames cannot be used with the `mmgen-xmrwallet` utility.  This
  is an issue with the Monero wallet RPC daemon rather than MMGen.

+ The Bitcoin Cash Node daemon cannot handle non-ASCII pathnames.  This is an
  issue with the Bitcoin Cash Node implementation for Windows, not MMGen.

## <a id="a_u">Keeping your installation up to date</a>

### <a id="a_us">Upgrading MSYS2</a>

You should periodically upgrade your MSYS2 installation, especially when [new
releases][mh] appear.  The most reliable way to check your current MSYS2 version
is to examine the date on the installation binary, which you’ve hopefully saved
somewhere.

To perform the upgrade, just repeat [Step 2](#a_ug) of this guide.

Note that [Step 3](#a_md) need not be performed, as the MMGen dependencies
are already in `pacman`’s database.

### <a id="a_um">Upgrading MMGen Wallet</a>

You should periodically upgrade your MMGen Wallet installation from one of its
public repositories, especially when [new releases][mr] appear.  You can check
your currently installed version by executing `mmgen-tool --version`.

#### <a id="a_ums">Upgrade to latest stable version:</a>

Online upgrade:

> ```text
> $ python3 -m pip install --upgrade mmgen-wallet
> ```

Offline upgrade:

> On your online machine:
>
> ```text
> $ python3 -m pip download mmgen-wallet
> ```
>
> Copy the downloaded tar.gz archive to your offline machine and execute:
>
> ```text
> $ python3 -m pip install --no-build-isolation mmgen-wallet.*tar.gz
> ```

#### <a id="a_umd">Upgrade to latest development version:</a>

Enter the MMGen Wallet repository root on your online computer and issue the
following commands:

Online upgrade:

> ```text
> $ git checkout master
> $ git pull
> $ rm -rf dist build *.egg-info
> $ python3 -m build --no-isolation
> $ python3 -m pip install dist/*.whl
> ```

Offline upgrade:

> After the `git pull` step above, copy the updated repository to your offline
> machine, `cd` to the root of the copied repository and perform the remaining
> steps.

[mh]: https://www.msys2.org
[mp]: https://sourceforge.net/projects/msys2
[mw]: https://github.com/msys2/msys2/wiki
[ov]: ../../../../releases/tag/v0.9.8
[sd]: https://download.sysinternals.com/files/SDelete.zip
[mr]: ../../../../releases
[di]: Deprecated-MSWin-Installation.md
[ib]: Install-Bitcoind.md
[gs]: Getting-Started-with-MMGen-Wallet.md
[pl]: Altcoin-and-Forkcoin-Support.md#a_ed
[ax]: cmds/command-help-autosign.md
[mc]: Altcoin-and-Forkcoin-Support.md#a_xmr
[ts]: Test-Suite.md
[vv]: https://docs.python.org/3/library/venv.html
