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
computers, one online and one offline, to be used securely.  All operations
involving private data—wallet generation, address generation and transaction
signing—are handled offline, while the online installation takes care of
tracking balances and creating and sending transactions.

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
> reopen another one.  Your mirror lists were overwritten by the upgrade
> operation, so you must restore them from your modified versions.

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

	$ pacman -S tar git nano vim \
		mingw64/mingw-w64-x86_64-python3-cryptography \
		mingw64/mingw-w64-x86_64-python3-six \
		mingw64/mingw-w64-x86_64-python3-pexpect \
		mingw64/mingw-w64-x86_64-python3-gmpy2 \
		mingw64/mingw-w64-x86_64-libsodium \
		mingw64/mingw-w64-x86_64-python3-pynacl \
		mingw64/mingw-w64-x86_64-python3-pip

### 5. Set your PATH environmental variable

Open your shell’s runtime configuration file in a text editor:

	$ nano ~/.bashrc

Add the following line to the end of the file, save and exit:

	export PATH="/mingw64/bin:$PATH:/c/Program Files/Bitcoin/daemon:/c/Program Files/Litecoin/daemon:/c/Program Files/Bitcoin-abc/daemon"

Close and reopen the terminal window to update your working environment.

### 6. Install the remaining MMGen dependencies

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

### 7. Install MMGen

Now you’re ready to install MMGen itself.  On your online machine, clone the
repository:

	$ git clone https://github.com/mmgen/mmgen
	Cloning into ’mmgen’...

If you’re doing an offline install, you can then copy the cloned mmgen directory
to your offline machine.

Enter the directory and install:

	$ cd mmgen
	$ git checkout stable_msys2
	$ ./setup.py install

### 8. Install and launch your coin daemons

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
your executable path, preferably `C:\\msys64\usr\local\bin`.  If the target
directory doesn’t exist yet, create it in your terminal like this:

	$ mkdir -p /usr/local/bin

Typically you’ll wish to launch Parity as follows:

	$ parity.exe --jsonrpc-apis=all

More information on Parity’s command-line options can be found [here][pl].

### 9. You’re done!

Congratulations, your installation is now complete, and you can proceed to
[**Getting Started with MMGen**][gs]. Before doing so, however, you might want
to acquaint yourself with some caveats regarding running MMGen on
Microsoft Windows:

 + [Autosigning][X] is not supported on Windows and is not likely to be in the
   future. 
 + [Monero wallet creation/syncing][M] support is also lacking due to password
   file descriptor issues with `monero-wallet-cli`.
 + Due to unpredictable behavior of MSYS2's Python `getpass()` implementation,
   passwords containing non-ASCII characters should be entered using the
   `--echo-passphrase` option or via a password file.  Otherwise, these
   symbols might end up being silently ignored.  
   If you have an all-ASCII wallet password and wish to silence the annoying
   warning you’re getting before every password prompt, set `mswin_pw_warning`
   to `false` in `mmgen.cfg`.  
   If you *really* don't want to have your passwords echoed, you may test whether
   `getpass()` is reading your non-ASCII input correctly by running the script
   `test/misc/password_entry.py`.  If the script reads back the characters
   exactly as you entered them, then you’re probably safe and can go ahead and
   disable the warning.
 + Though MSYS2 support is well tested and considered stable, it’s a new feature
   and other glitches might remain.  If you think you've found a bug, don't
   hesistate to file an issue at <https://github.com/mmgen/mmgen/issues>.


[mh]: https://www.msys2.org
[mp]: https://sourceforge.net/projects/msys2
[mw]: https://github.com/msys2/msys2/wiki
[ov]: https://github.com/mmgen/mmgen/releases/tag/v0.9.8
[di]: Deprecated-MSWin-Installation
[ib]: Install-Bitcoind
[gs]: Getting-Started-with-MMGen
[pg]: https://github.com/paritytech/parity-ethereum/releases
[pl]: Altcoin-and-Forkcoin-Support#a_par
[X]:  autosign-[MMGen-command-help]
[M]:  Altcoin-and-Forkcoin-Support#a_xmr
