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


                               USAGE NOTES

If no operation is specified, this program mounts a removable device
(typically a USB flash drive) containing unsigned MMGen transactions, message
files, and/or XMR wallet output files, signs them, unmounts the removable
device and exits.

If invoked with ‘wait’, the program waits in a loop, mounting the removable
device, performing signing operations and unmounting the device every time it
is inserted.

The removable device must have a partition with a filesystem labeled MMGEN_TX
and a user-writable root directory.  For interoperability between OS-es, it’s
recommended to use the exFAT file system.

On both the signing and online machines the mountpoint ‘{asi.mountpoint}’
(as currently configured) must exist.  Linux (not macOS) machines must have
an ‘/etc/fstab’ with the following entry:

    LABEL=MMGEN_TX {asi.mountpoint} auto noauto,user 0 0

Signing is performed with a temporary wallet created in volatile memory in
the directory ‘{asi.wallet_dir}’ (as currently configured).  The wallet is
encrypted with a 32-byte password saved in the file ‘autosign.key’ in the
root of the removable device’s filesystem.


                             LED SIGNALING SUPPORT

On supported platforms (selected Orange Pi, Rock Pi, Banana Pi, Nano Pi and
Raspberry Pi boards), a flashing LED indicates whether signing is in progress
or the program is in standby mode, i.e. ready for device insertion or removal.

The operation ‘test_led’ tests the current installation for LED support, while
‘list_led’ displays a list of supported board/OS combinations.  Note that this
list is not exhaustive: signaling may work with other boards, especially those
produced by the listed manufacturers.  If ‘test_led’ reports that your board is
not supported, please submit an issue to the mmgen-wallet repository on Github
or via e-mail, including the board model, OS version and output of the
following shell command:

    ls -RH /sys/class/leds/{{*status*,*led*}}

In the absence of LED support, the user must observe the signing progress
on-screen and wait for the “safe to extract” message to appear.


The password and temporary wallet may be created in one operation by invoking
‘mmgen-autosign setup’ with the removable device inserted.  In this case, the
temporary wallet is created from the user’s default wallet, if it exists and
the user so desires.  If not, the user is prompted to enter a seed phrase.

Alternatively, the password and temporary wallet may be created separately by
first invoking ‘mmgen-autosign gen_key’ and then creating and encrypting the
wallet using the -P (--passwd-file) option:

    $ mmgen-walletconv -iwords -d{asi.wallet_dir} -p1 -N -P{asi.mountpoint}/autosign.key -Lfoo

Note that the hash preset must be ‘1’.  To use a wallet file as the source
instead of an MMGen seed phrase, omit the ‘-i’ option and add the wallet
file path to the end of the command line.  Multiple temporary wallets may
be created in this way and used for signing (note, however, that for XMR
operations only one wallet is supported).

Autosigning is currently supported on Linux and macOS only.


                               SECURITY NOTE

By placing wallet and password on separate devices, this program creates
a two-factor authentication setup whereby an attacker must gain physical
control of both the removable device and signing machine in order to sign
transactions.  It’s therefore recommended to always keep the removable device
secure, separated from the signing machine and hidden (in your pocket, for
example) when not transacting.  In addition, since login access on the
signing machine is required to steal the user’s seed, it’s good practice
to lock the signing machine’s screen once the setup process is complete.

As a last resort, cutting power to the signing machine will destroy the
volatile memory where the temporary wallet resides and foil any attack,
even if you’ve lost control of the removable device.

Always remember to power off the signing machine when your signing session
is over.
"""
