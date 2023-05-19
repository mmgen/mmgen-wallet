*NOTE: the instructions on this page are for a Bitcoin-only setup.  For
altcoin support, additional installation steps are required.  See*
[**Altcoin and Forkcoin Support**][af] *for more information.*

### Perform the following steps on both your online and offline computers:

For computers with no Internet connection, see **Note for offline machines** below.

#### Install required packages:

##### Debian/Ubuntu:

```text
$ sudo apt-get install curl git gcc libtool make autoconf libgmp-dev libssl-dev libpcre3-dev libmpfr-dev libmpc-dev python3-dev python3-pip
```

##### Arch Linux:

```text
$ sudo pacman -S curl git gcc libtool make autoconf automake autogen pcre python-pip
```

#### Upgrade the build tools:

```text
$ python3 -m pip install --user --upgrade pip setuptools build wheel
```

If you get an ‘externally-managed-environment’ error (with Debian bookworm,
for example), add --break-system-packages to the command line.  Note that this
will not in fact break any system packages, as pip installs all packages under
the user’s home directory when --user is in effect.

#### Install MMGen:

Make sure that `~/.local/bin` is in `PATH`.  Existing MMGen users should delete
any old installations under `/usr` or `/usr/local`.

```text
$ git clone https://github.com/mmgen/mmgen.git
$ cd mmgen
$ git checkout stable_linux # see 'Note' below
$ python3 -m build --no-isolation
$ python3 -m pip install --user --upgrade dist/*.whl # see 'Install Note' below
$ cd ..
```

**Note:** if you want to use features that have appeared since the latest
`stable_linux` release, then you can omit the `git checkout` step and remain on
the `master` branch.  Please bear in mind, however, that while the tip of
`master` is always tested on Linux before being pushed to the public repository,
security vulnerabilities are more likely to be present in new code than in a
stable release.  In addition, new code may require dependencies or installation
steps not yet covered in the documentation.

**Install Note:** The `--force` and `--no-deps` options also come in handy
on occasion.

If you plan to run the test suite, additional installation steps are required.
Refer to the [Test Suite][ts] wiki page for details.

Install your coin daemon(s).  To install prebuilt binaries, go [here][01].  To
install from source, go [here][02].

##### Note for offline machines:

The computer you’ve designated for offline use must be connected to the
Internet to retrieve and install the above packages as described above.  This
is normally not a problem, as you can simply take it offline permanently after
the install is done, preferably removing or disabling its network interfaces.

However, if your machine is already offline and you wish to leave it that way,
or if it lacks a network interface entirely, then you’ll need to take roughly
the following steps:

> If your offline and offline computers have the same architecture, then
> download the Debian/Ubuntu packages and their dependencies on the online
> one using `apt-get download`.  Otherwise, retrieve the packages manually
> from `packages.debian.org` or `packages.ubuntu.com`.
>
> Download any required Python packages using `python3 -m pip download`, or
> manually from [pypi.org][pi] if your online and offline computers have
> different architecture.
>
> Transfer the downloaded files and cloned Git repositories to your offline
> computer using a USB stick or other removable medium.  Install the
> Debian/Ubuntu packages with `sudo dpkg -i` and the Python packages with
> `python3 -m pip install --user`.
>
> Clone the [secp256k1][ec] repository and copy it to `~/.cache/mmgen`
> directory on the offline machine (or copy it from your online machine’s
> `~/.cache/mmgen`).  Copy the MMGen repository to the offline machine and
> install MMGen as described above.  If your online and offline machines have
> different architecture, make sure to clean up any build/dist files in the
> repositories before installing (in `secp256k1` this is accomplished by `make
> clean`).

Congratulations, your installation is now complete!  You can now proceed to
[**Getting Started with MMGen**][gs].

[01]: Install-Bitcoind
[02]: Install-Bitcoind-from-Source-on-Debian-or-Ubuntu-Linux
[ts]: Test-Suite
[gs]: Getting-Started-with-MMGen
[pi]: https://pypi.org
[af]: Altcoin-and-Forkcoin-Support
[ec]: https://github.com/bitcoin-core/secp256k1.git
