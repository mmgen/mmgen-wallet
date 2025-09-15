```text
  MMGEN-AUTOSIGN: Auto-sign MMGen transactions, message files and XMR wallet output files
  USAGE:          mmgen-autosign [opts] [operation]
  OPTIONS:
  -h, --help            Print this help message
      --longhelp        Print help message for long (global) options
  -c, --coins c         Coins to sign for (comma-separated list)
  -I, --no-insert-check Don’t check for device insertion
  -k, --keys-from-file F Use wif keys listed in file ‘F’ for signing non-MMGen
                        inputs. The file may be MMGen encrypted if desired. The
                        ‘setup’ operation creates a temporary encrypted copy of
                        the file in volatile memory for use during the signing
                        session, thus permitting the deletion of the original
                        file for increased security.
  -l, --seed-len N      Specify wallet seed length of ‘N’ bits (for setup only)
  -L, --led             Use status LED to signal standby, busy and error
  -m, --mountpoint M    Specify an alternate mountpoint 'M'
                        (default: '/mnt/mmgen_autosign')
  -M, --mnemonic-fmt F  During setup, prompt for mnemonic seed phrase of format
                        'F' (choices: 'mmgen','bip39'; default: 'mmgen')
  -n, --no-summary      Don’t print a transaction summary
  -r, --macos-ramdisk-size S  Set the size (in MB) of the ramdisk used to store
                        the offline signing wallet(s) on macOS machines.  By
                        default, a runtime-calculated value will be used. This
                        option is of interest only for setups with unusually
                        large Monero wallets
  -s, --stealth-led     Stealth LED mode - signal busy and error only, and only
                        after successful authorization.
  -S, --full-summary    Print a full summary of each signed transaction after
                        each autosign run. The default list of non-MMGen outputs
                        will not be printed.
  -q, --quiet           Produce quieter output
  -v, --verbose         Produce more verbose output
  -w, --wallet-dir D    Specify an alternate wallet dir
                        (default: '/dev/shm/autosign')
  -W, --allow-non-wallet-swap Allow signing of swap transactions that send funds
                        to non-wallet addresses
  -x, --xmrwallets L    Range or list of wallets to be used for XMR autosigning


                                 OPERATIONS

  clean     - clean the removable device of unneeded files, removing only non-
              essential data
  gen_key   - generate the wallet encryption key and copy it to the removable
              device mounted at mountpoint ‘/mnt/mmgen_autosign’ (as currently
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


                                 USAGE NOTES

  If no operation is specified, this program mounts a removable device
  (typically a USB flash drive) containing unsigned MMGen transactions, message
  files, and/or XMR wallet output files, signs them, unmounts the removable
  device and exits.

  If invoked with ‘wait’, the program waits in a loop, mounting the removable
  device, performing signing operations and unmounting the device every time it
  is inserted.

  On supported platforms (currently Orange Pi, Rock Pi and Raspberry Pi boards),
  the status LED indicates whether the program is busy or in standby mode, i.e.
  ready for device insertion or removal.

  The removable device must have a partition with a filesystem labeled MMGEN_TX
  and a user-writable root directory.  For interoperability between OS-es, it’s
  recommended to use the exFAT file system.

  On both the signing and online machines the mountpoint ‘/mnt/mmgen_autosign’
  (as currently configured) must exist.  Linux (not macOS) machines must have
  an ‘/etc/fstab’ with the following entry:

      LABEL=MMGEN_TX /mnt/mmgen_autosign auto noauto,user 0 0

  Signing is performed with a temporary wallet created in volatile memory in
  the directory ‘/dev/shm/autosign’ (as currently configured).  The wallet is
  encrypted with a 32-byte password saved in the file ‘autosign.key’ in the
  root of the removable device’s filesystem.

  The password and temporary wallet may be created in one operation by invoking
  ‘mmgen-autosign setup’ with the removable device inserted.  In this case, the
  temporary wallet is created from the user’s default wallet, if it exists and
  the user so desires.  If not, the user is prompted to enter a seed phrase.

  Alternatively, the password and temporary wallet may be created separately by
  first invoking ‘mmgen-autosign gen_key’ and then creating and encrypting the
  wallet using the -P (--passwd-file) option:

      $ mmgen-walletconv -iwords -d/dev/shm/autosign -p1 -N -P/mnt/mmgen_autosign/autosign.key -Lfoo

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

  MMGEN-WALLET 16.0.0            September 2025              MMGEN-AUTOSIGN(1)
```
