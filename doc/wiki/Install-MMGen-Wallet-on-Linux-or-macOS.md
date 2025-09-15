*NOTE: the instructions on this page are for a Bitcoin-only setup.  For
altcoin support, additional installation steps are required.  See*
[**Altcoin and Forkcoin Support**][af] *for more information.*

### Perform the following steps on both your online and offline computers:

For computers with no Internet connection, see **Note for offline machines** below.

### Install required packages from your distribution:

#### Debian/Ubuntu:

```text
$ sudo apt-get install curl git gcc libtool make autoconf e2fsprogs libgmp-dev libssl-dev libpcre2-dev libmpfr-dev libmpc-dev python3-dev python3-pip libsecp256k1-dev
```

#### Arch Linux:

```text
$ sudo pacman -S curl git gcc libtool make autoconf automake autogen pcre python-pip libsecp256k1
```

#### macOS:

```text
$ brew install python bash autoconf coreutils gcc libmpc libtool readline secp256k1
```

On RISC-V machines, you may additionally need to install the `libffi-dev` package and [Rust][rs]

You may wish to use a [virtual environment][vv] to keep your MMGen Wallet
installation isolated from the rest of your Python packages.

If you choose not to use a virtual environment, then you may need to add
`--break-system-packages` to the `pip install` command line, depending on your
Python and OS versions.  Note that this will not in fact break any system
packages, as pip installs all packages under the user’s home directory when
invoked as user.

### Upgrade the Python build tools:

```text
$ python3 -m pip install --upgrade pip setuptools build wheel
```

### Install MMGen Wallet:

#### Stable version:

```text
$ python3 -m pip install mmgen-wallet
```

#### Development version:

**Note:** While the development version is always tested on Linux before being
pushed to the public repository, security vulnerabilities are more likely to be
present in new code than in a stable release.  In addition, new code may require
dependencies or installation steps not yet covered in the documentation.

If not running in a virtual environment, make sure that `~/.local/bin` is in
`PATH`.  Existing MMGen Wallet users should delete any old installations under
`/usr` or `/usr/local`.

```text
$ git clone https://github.com/mmgen/mmgen-wallet.git
$ cd mmgen-wallet
$ python3 -m build --no-isolation
$ python3 -m pip install --upgrade dist/*.whl # see 'Install Note' below
$ cd ..
```

**Install Note:** When upgrading from previous versions, the `--force` and
`--no-deps` options also come in handy on occasion.

Install your coin daemon(s).  To install prebuilt binaries, go [here][01].  To
install from source, go [here][02].

If you plan to run the test suite, additional installation steps are required.
Refer to the [Test Suite][ts] wiki page for details.

#### Note for offline machines:

The computer you’ve designated for offline use must be connected to the
Internet to retrieve and install the above packages as described above.  This
is normally not a problem, as you can simply take it offline permanently after
the install is done, preferably removing or disabling its network interfaces.

However, if your machine is already offline and you wish to leave it that way,
or if it lacks a network interface entirely, then you’ll need to take the
following steps:

> If your offline and offline computers have the same architecture, then
> download the Debian/Ubuntu packages and their dependencies on the online
> one using `apt-get download`.  Otherwise, retrieve the packages manually
> from `packages.debian.org` or `packages.ubuntu.com`.
>
> Download the Python build tools using `python3 -m pip download`.
>
> Transfer the downloaded files to your offline computer using a USB stick or
> other removable medium.  Install the Debian/Ubuntu packages with `sudo dpkg
> -i` and the Python packages with `python3 -m pip install`.

Congratulations, your installation is now complete!  You can now proceed to
[**Getting Started with MMGen Wallet**][gs].

[01]: Install-Bitcoind.md
[02]: Install-Bitcoind-from-Source-on-Linux.md
[ts]: Test-Suite.md
[gs]: Getting-Started-with-MMGen-Wallet.md
[pi]: https://pypi.org
[af]: Altcoin-and-Forkcoin-Support.md
[ec]: https://github.com/bitcoin-core/secp256k1.git
[vv]: https://docs.python.org/3/library/venv.html
[rs]: https://rustup.rs
