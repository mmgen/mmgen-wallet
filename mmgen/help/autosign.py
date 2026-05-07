#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2026 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
help.autosign: autosign help notes for the MMGen Wallet suite
"""

def help(proto, cfg, *, asi):
	return f"""

                                   OPERATIONS

clean     - clean the removable device of unneeded files, removing only non-
            essential data
gen_key   - generate the wallet encryption key and copy it to the removable
            device mounted at mountpoint ‘{asi.mountpoint}’ (as currently
            configured)
setup     - full setup: run ‘gen_key’ and create temporary signing wallet(s)
            for all configured coins
xmr_setup - set up Monero temporary signing wallet(s).  Not required during
            normal operation: use ‘setup’ with --xmrwallets instead
macos_ramdisk_setup - set up the ramdisk used for storing the temporary signing
            wallet(s) (macOS only).  Required only when creating the wallet(s)
            manually, without ‘setup’
macos_ramdisk_delete - delete the macOS ramdisk
disable_swap - disable disk swap to prevent potentially sensitive data in
            volatile memory from being swapped to disk.  Applicable only when
            creating temporary signing wallet(s) manually, without ‘setup’
enable_swap - reenable disk swap.  For testing only, should not be invoked in
            a production environment
wait      - start in loop mode: wait-mount-sign-unmount-wait
wipe_key  - wipe the wallet encryption key on the removable device, making
            signing transactions or stealing the user’s seed impossible.
            The operation is intended as a ‘kill switch’ and thus performed
            without prompting
list_led  - list boards with tested LED signaling support
test_led  - test the current board for LED signaling support


                                  DESCRIPTION

This program is intended to be run on an offline signing computer, preferably
air-gapped and with no or disabled RF devices (e.g. wi-fi and bluetooth).
Memory, storage and CPU requirements for signing operations are modest, so an
old laptop is suitable for the job, or better yet, a Raspberry Pi or Pi clone
from among the list of supported devices (see LED SIGNALING SUPPORT below).
OS support is currently limited to Linux and macOS.

Before using the program, a removable device (typically a USB flash drive)
must first be prepared and the current signing session set up, both as
described below.

If run with no arguments, the program mounts the removable device, signs any
unsigned MMGen signables (transactions, message files, and/or XMR wallet
output files) on the device, unmounts the device and exits.

If invoked with ‘wait’, the program waits in a loop: mounting, signing and
unmounting every time the removable device is inserted.  Wait mode permits
“hands-free” operation, i.e. repeated signing of signables with no keyboard
input, by simply inserting the removable device and then removing it when the
program indicates that signing is complete (see LED SIGNALING SUPPORT below).

Signing is performed with a temporary session wallet written in volatile
memory in the directory ‘{asi.wallet_dir}’ (as currently configured).  The
wallet is encrypted with a random password saved in the file ‘autosign.key’
on the removable device.

By default, the session wallet is created from the user’s default MMGen
wallet, if it exists.  However, the user may optionally generate the session
wallet by interactively entering a seed phrase during session setup. Thus it
is possible to perform signing and other wallet operations with no seed data
ever written to disk, even in encrypted form (“wallet-less” operation).

Depending on the coin, signing is performed either internally by MMGen Wallet
or using an external backend, according to the table below.  Thus you must
install the corresponding backend executable, if any, for each coin you wish
to transact and start it with the listed command, if any, at the beginning of
each signing session.  It’s recommended to install the executables into
‘/usr/local/bin’.

  Coin          Backend           Executable        Command
  ----          -------           ----------        -------
  BTC           Bitcoin Core      bitcoind          bitcoind --listen=0 --daemon
  LTC           Litecoin Core     litecoind         litecoind --listen=0 --daemon
  BCH           Bitcoin Cash Node bitcoind-bchn*    bitcoind-bchn --daemon --listen=0 --rpcport=8432 --datadir=$HOME/.bitcoin-bchn
  XMR           Monero CLI Wallet monero-wallet-rpc -
  ETH,ETC,ERC20 none              -                 -
  RUNE          none              -                 -

  * Executable must be renamed from the default ‘bitcoind’


                             LED SIGNALING SUPPORT

On supported platforms (selected Orange Pi, Rock Pi, Banana Pi, Nano Pi and
Raspberry Pi boards), a flashing LED indicates whether signing is in progress
or the program is in standby mode, i.e. ready for device insertion or removal.
In the absence of LED support, the user must observe the signing progress
on-screen and wait for the “safe to extract” message to appear.

The operation ‘test_led’ tests the current installation for LED support, while
‘list_led’ displays a list of supported board/OS combinations.  Note that this
list is not exhaustive: signaling may work with other boards, especially those
produced by the listed manufacturers.  If ‘test_led’ reports that your board is
not supported, please submit an issue to the mmgen-wallet repository on Github
or via e-mail, including the board model, OS version and output of the
following shell command:

    ls -RH /sys/class/leds/{{*status*,*led*}}


                         PREPARING THE REMOVABLE DEVICE

Create a partition on the removable device with a filesystem labeled ‘MMGEN_TX’
and a user-writable root directory.  For interoperability between different
operating systems, it’s recommended to use the exFAT filesystem.

On both the offline and online machines, create the mountpoint ‘{asi.mountpoint}’
(as currently configured) and, for Linux, the following entry in ‘/etc/fstab’:

    LABEL=MMGEN_TX {asi.mountpoint} auto noauto,user 0 0

If your Linux distribution mounts volumes automatically, it’s advisable to
disable that functionality.


                         SETTING UP A SIGNING SESSION

Invoke ‘mmgen-autosign setup’ with the removable device inserted.  This will
create the temporary session wallet from the user’s default MMGen wallet (if
it exists) or, optionally, a seed phrase.  In addition, the session wallet
password is created and written to the removable device.  Additional options
may be required.  See OPTIONS above and EXAMPLES below.


                       ALTERNATIVE (MANUAL) SESSION SETUP

Alternatively, the password and temporary wallet may be created separately by
first invoking ‘mmgen-autosign gen_key’ and then creating and encrypting the
wallet using the -P (--passwd-file) option:

    $ mmgen-walletconv -iwords -d{asi.wallet_dir} -p1 -N -P{asi.mountpoint}/autosign.key -Lfoo

Note that the hash preset must be ‘1’.  To use a wallet file as the source
instead of an MMGen seed phrase, omit the ‘-i’ option and add the wallet
file path to the end of the command line.  Multiple session wallets may
be created in this way (note, however, that for XMR operations only one
session wallet is supported).


                           XMR SIGNING SESSION SETUP

To set up an XMR signing session, run ‘setup’ with the --xmrwallets option,
supplying an integer, range, or comma-separated list of integers as the
option’s parameter.  Each integer in the list or range represents a wallet
number.  For each wallet number, the program generates a Monero address and
creates a temporary session Monero signing wallet in volatile memory under
‘{asi.wallet_dir}’ with this number and base address.  In addition, data is
written to the removable device which will allow the online installation to
create a watch-only wallet matching the session signing wallet when the user
runs ‘mmgen-addrimport --coin=xmr’ on the online machine with the removable
device inserted (type ‘mmgen-addrimport --coin=xmr --help’ for details).

The use of multiple Monero wallets can help protect against certain known
deanonymization attacks such as the Janus attack.  However, since wallet
creation and online syncing of multiple wallets, as well as switching among
them during the signing process, are all time-consuming, it’s recommended to
limit the number of wallets created.  First-time users are thus advised to
begin with ‘--xmrwallets=1’.  More wallets may be added in later signing
sessions if necessary.  See EXAMPLES below.


                               SECURITY NOTE

By placing the session wallet and password on separate devices, this program
creates a two-factor authentication setup whereby an attacker must gain
physical control of both the removable device and signing machine in order to
sign transactions or steal the user’s seed.  It’s therefore recommended to
always keep the removable device secure, separated from the signing machine
and hidden (in your pocket, for example) when not transacting.  In addition,
it’s good practice to lock the signing machine’s screen when unattended.

For Monero, passwords for the watch-only wallets are also stored on the
removable device, meaning that a local attacker must gain access to the latter
not only to sign transactions but also to observe the user’s XMR balances and
transaction history (a remote attacker could possibly observe these, but
extracting the removable device when it’s not in use makes such an attack
less feasible).

As a last resort, cutting power to the signing machine will destroy the
volatile memory where the session wallets reside and prevent a signing or
seed-stealing attack, even if the attacker has gained control of the removable
device.

Always remember to power off the signing machine when your signing session
is over.

After each signing operation, this program displays a summary showing each
transaction’s non-wallet destination address(es) and amount(s).  As an extra
security measure, it’s a good idea to compare these with the address(es) and
amount(s) displayed by your online installation. A discrepancy would indicate
that your online setup has been compromised.


                                    EXAMPLES

Set up a signing session:
$ mmgen-autosign setup

Start the Bitcoin Core daemon:
$ bitcoind --daemon --listen=0

Start the signing loop (BTC-only signing):
$ mmgen-autosign wait # exit loop with Ctrl-C

Set up a signing session with one XMR wallet:
$ mmgen-autosign --xmrwallets=1 setup

In a later signing session, add two more XMR wallets:
$ mmgen-autosign --xmrwallets=1-3 setup

Start the Litecoin Core daemon:
$ litecoind --daemon --listen=0

Start the signing loop (BTC, LTC and XMR signing):
$ mmgen-autosign --coins=btc,ltc,xmr wait

Set up a signing session with 3 XMR wallets, prompting for a 12-word BIP39 seed phrase:
$ mmgen-autosign --xmrwallets=2,5,8 --mnemonic-fmt=bip39 --seed-len=128 setup

Start the signing loop in stealth LED mode with full TX summary (LTC, RUNE and XMR signing):
$ mmgen-autosign --coins=ltc,rune,xmr --stealth-led --full-summary wait

Generate a list of 10 LTC Bech32 addresses using your session wallet:
$ mount /mnt/mmgen_autosign
$ mmgen-addrgen -P /mnt/mmgen_autosign/autosign.key --coin=ltc --type=B /dev/shm/autosign/*.mmdat 1-10
"""
