## Introduction

In addition to low-level subsystems, the suite tests the overall operation of
MMGen’s commands by running them interactively as a user would.  Thus the test
suite is useful not only for ensuring the MMGen system is correctly installed
and working on your platform but also for learning how it works.

BTC-only testing requires only Bitcoin Core to be installed.  Altcoin testing
requires various helper programs and libraries.  Installation instructions for
these are provided below.  Non-standard RPC ports and data directories are
always used, so there’s no need to stop your running node or nodes.

On Linux/x86\_64 with a reasonably fast processor, the full suite should run in
under 15 minutes when invoked with the `-F` option.  Execution times on other
platforms may be much slower.

## Quick start

### Container setup (if applicable)

The test suite requires the `/dev/loopX` devices to exist and be enabled.  If
you’re running in an LXC container, note that only privileged containers allow
loop devices.  You may enable them in the config file as follows:

	lxc.cgroup2.devices.allow = b 7:0 rwm # /dev/loop0
	lxc.cgroup2.devices.allow = b 7:1 rwm # /dev/loop1
	lxc.cgroup2.devices.allow = b 7:2 rwm # /dev/loop2

Every time the container is started, you may need to create the files afresh:

	# mknod /dev/loop0 b 7 0
	# mknod /dev/loop1 b 7 1
	# mknod /dev/loop2 b 7 2

### BTC-only testing

Clone the Bitcoin Core repo somewhere on your system:

	$ git clone https://github.com/bitcoin/bitcoin

Install the Bitcoin Core daemon [(source)][sd] [(binaries)][bd].

Point the test suite to your copy of the Bitcoin Core repo:

	$ export CORE_REPO_ROOT=/path/to/bitcoin/core/repo

Install Pycoin:

	$ python3 -m pip install --user pycoin

CD to the MMGen repository root and build without installing:

	$ cd path/to/mmgen/repo
	$ python3 setup.py build_ext --inplace

Run the following if upgrading from a previous version of MMGen:

	$ test/test.py clean

Run the test suite in fast mode, skipping altcoin tests:

	$ test/test-release.sh -F noalt

### Complete testing (BTC plus all supported altcoins)

Complete the BTC-only installation steps above, without running the test.

Make sure the [Bitcoin Cash Node][cnd], [Litecoin][ld] and [Monero][md]
daemons are installed on your system.

Install [OpenEthereum, Parity, Geth, the Ethereum dependencies][oe] and
optionally the [Solidity compiler][sc] as described on the
Altcoin-and-Forkcoin-Support page.

In addition, you must install the following helper programs and libraries (MSYS2
users can omit Zcash-Mini and leave out `sudo` in commands):

#### SSH daemon setup (MSYS2 only)

The XMR test sets up a local SOCKS proxy to test transaction relaying.  This
requires the SSH daemon to be set up and running.  On MSYS2 systems, SSHD
is not configured by default, but it may be easily set up with the following
steps:

Open PowerShell as administrator, and at the DOS prompt, execute:

	system32> net user administrator /active:yes
	system32> C:\\msys64\usr\bin\bash.exe --login

Now, at the MSYS2 prompt, cd to the MMGen repository root and run the setup
script:

	$ scripts/msys2-sshd-setup.sh

The daemon should now start automatically every time the system is booted. It
may also be started and stopped manually at the DOS or MSYS2 prompt as follows
(PowerShell must be running with admin privileges):

	# net start msys2_sshd
	# net stop msys2_sshd

#### MoneroPy

	$ git clone https://github.com/bigreddmachine/MoneroPy
	$ cd MoneroPy
	$ python3 setup.py install --user
	$ cd ..

#### Vanitygen PlusPlus (forked from Vanitygen Plus)

    $ git clone https://github.com/10gic/vanitygen-plusplus
	$ cd vanitygen-plusplus
	$ git checkout -b vanitygen-plus e7858035d092  # rewind to fork commit
	$ make keyconv # ‘mingw32-make.exe keyconv’ for MSYS2
	$ sudo install --strip keyconv /usr/local/bin  # ‘keyconv.exe’ for MSYS2
	$ cd ..

#### Zcash-Mini

	$ sudo apt-get install golang  # skip this if Go is already installed
    $ git clone https://github.com/FiloSottile/zcash-mini
    $ cd zcash-mini
	$ go mod init zcash-mini
	$ go mod tidy
	$ go build -mod=mod # or just ’go build’
	$ sudo install --strip ./zcash-mini /usr/local/bin
	$ cd ..

#### Ethkey

On Arch Linux systems, ethkey is included in the OpenEthereum package:

	$ pacman -S openethereum

For other systems, you may have to build ethkey from source:

	$ sudo apt-get install rustc  # skip this if Rust is already installed
	$ git clone https://github.com/openethereum/openethereum
	$ cd openethereum
	$ git checkout v2.6.6 # this version builds on ARM boards - your mileage may vary
	$ cargo build -p ethkey-cli --release
	$ sudo install --strip ./target/release/ethkey /usr/local/bin
	$ cd ..

#### Monero note

The Monero test (`test/test-release.sh xmr`) creates a private network and
mines coins, so is therefore non-deterministic and prone to random failures.
If you experience such a failure, just restart the test.

### Run the tests

Now you can run the test suite for all coins:

	$ test/test-release.sh -F

## Overview of the individual tests

`test/test-release.sh` is just a simple shell script that invokes the test
scripts with various options and arguments to ensure complete coverage of
MMGen’s functionality.  Launch the script with the `-t` option to view the
invocations without running them.

The test scripts themselves are all located in the `test/` directory and bear
the `.py` extension.  They may be run individually if desired.  Options and
arguments required by the tests are described in detail on their help screens.

High-level testing of the MMGen system is performed by `test/test.py`, which
uses the `pexpect` library to simulate interactive operation of MMGen user
commands.  Running `test/test.py` with the `-e` option will display the
commands’ output on the screen as they’re being run.

| Test                  | What it tests                                        |
|:----------------------|:-----------------------------------------------------|
| `test/colortest.py`   | terminfo parsing; terminal colors                    |
| `test/gentest.py`     | key/address generation - profiling and data validity |
| `test/hashfunc.py`    | native SHA2 and Keccak implementations               |
| `test/objtest.py`     | MMGen data objects - creation and error handling     |
| `test/objattrtest.py` | MMGen data objects - immutable attributes            |
| `test/scrambletest.py`| HMAC scramble strings used in key/password derivation|
| `test/test.py`        | overall operation of MMGen commands                  |
| `test/tooltest.py`    | the `mmgen-tool` utility - overall operation         |
| `test/tooltest2.py`   | the `mmgen-tool` utility - data validity             |
| `test/unit_tests.py`  | low-level subsystems                                 |

[sd]: Install-Bitcoind-from-Source-on-Debian-or-Ubuntu-Linux
[bd]: Install-Bitcoind
[md]: https://getmonero.org/downloads/#linux
[ad]: https://download.bitcoinabc.org/
[cnd]: https://bitcoincashnode.org/
[ld]: https://download.litecoin.org/litecoin-0.17.1/
[oe]: Altcoin-and-Forkcoin-Support#a_oe
[sc]: Altcoin-and-Forkcoin-Support#a_dt
