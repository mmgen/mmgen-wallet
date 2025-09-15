```text
  MMGEN-XMRWALLET: Perform various Monero wallet and transacting operations for
                   addresses in an MMGen XMR key-address file
  USAGE:           mmgen-xmrwallet [opts] create | sync | list | view | listview | dump | restore [xmr_keyaddrfile] [wallets]
                   mmgen-xmrwallet [opts] label    [xmr_keyaddrfile] LABEL_SPEC
                   mmgen-xmrwallet [opts] new      [xmr_keyaddrfile] NEW_ADDRESS_SPEC
                   mmgen-xmrwallet [opts] transfer [xmr_keyaddrfile] TRANSFER_SPEC
                   mmgen-xmrwallet [opts] sweep | sweep_all [xmr_keyaddrfile] SWEEP_SPEC
                   mmgen-xmrwallet [opts] submit   [TX_file]
                   mmgen-xmrwallet [opts] relay    <TX_file>
                   mmgen-xmrwallet [opts] resubmit | abort (for use with --autosign only)
                   mmgen-xmrwallet [opts] txview | txlist [TX_file] ...
                   mmgen-xmrwallet [opts] export-outputs | export-outputs-sign | import-key-images [wallets]
  OPTIONS:
  -h, --help                       Print this help message
      --longhelp                   Print help message for long (global) options
  -a, --autosign                   Use appropriate outdir and other params for
                                   autosigning operations (implies --watch-only).
                                   When this option is in effect, filename argu-
                                   ments must be omitted, as files are located
                                   automatically.
  -f, --priority N                 Specify an integer priority ‘N’ for inclusion
                                   of a transaction in the blockchain (higher
                                   number means higher fee).  Valid parameters:
                                   1=low 2=normal 3=high 4=highest.  If option
                                   is omitted, the default priority will be used
  -F, --full-address               Print addresses in full instead of truncating
  -m, --autosign-mountpoint P      Specify the autosign mountpoint (defaults to
                                   ‘/mnt/mmgen_autosign’, implies --autosign)
  -b, --rescan-blockchain          Rescan the blockchain if wallet fails to sync
  -d, --outdir D                   Save transaction files to directory 'D'
                                   instead of the working directory
  -D, --daemon H:P                 Connect to the monerod at HOST:PORT
  -e, --skip-empty-accounts        Skip display of empty accounts in wallets
                                   where applicable
  -E, --skip-empty-addresses       Skip display of used empty addresses in
                                   wallets where applicable
  -k, --use-internal-keccak-module Force use of the internal keccak module
  -p, --hash-preset P              Use scrypt hash preset 'P' for password
                                   hashing (default: '3')
  -P, --rescan-spent               Perform a rescan of spent outputs.  Used only
                                   with the ‘export-outputs-sign’ operation
  -R, --tx-relay-daemon H:P[:H:P]  Relay transactions via a monerod specified by
                                   HOST:PORT[:PROXY_IP:PROXY_PORT]
  -r, --restore-height H           Scan from height 'H' when creating wallets.
                                   Use special value ‘current’ to create empty
                                   wallet at current blockchain height.
  -R, --no-relay                   Save transaction to file instead of relaying
  -s, --no-start-wallet-daemon     Don’t start the wallet daemon at startup
  -S, --no-stop-wallet-daemon      Don’t stop the wallet daemon at exit
  -W, --watch-only                 Create or operate on watch-only wallets
  -w, --wallet-dir D               Output or operate on wallets in directory 'D'
                                   instead of the working directory
  -U, --wallet-rpc-user user       Wallet RPC username (currently: 'monero')
  -P, --wallet-rpc-password pass   Wallet RPC password (currently: [scrubbed])


  Many operations take an optional ‘wallets’ argument: one or more address
  indexes (expressed as a comma-separated list and/or hyphenated range) in
  the default or specified key-address file, each corresponding to a Monero
  wallet with the same index.  If the argument is omitted, all wallets are
  operated upon.

  All operations except for ‘relay’ require a running Monero daemon (monerod).
  Unless --daemon is specified, the daemon is assumed to be listening on
  localhost at the default RPC port.

  If --tx-relay-daemon is specified, the monerod at HOST:PORT will be used to
  relay any created transactions.  PROXY_IP:PROXY_PORT, if specified, may point
  to a SOCKS proxy, in which case HOST may be a Tor onion address.

  All communications use the RPC protocol via SSL (HTTPS) or Tor.  RPC over
  plain HTTP is not supported.


                              SUPPORTED OPERATIONS

  create    - create wallets for all or specified addresses in key-address file
  sync      - sync wallets for all or specified addresses in key-address file
              and display a summary of accounts and balances
  list      - same as ‘sync’, but also list detailed address info for accounts
  view      - display a summary of accounts and balances in offline mode.  May
              be invoked without a running monerod
  listview  - same as ‘view’, but also list detailed address info for accounts
  label     - set a label for an address
  new       - create a new account in a wallet, or a new address in an account
  transfer  - transfer specified XMR amount from specified wallet:account to
              specified address
  sweep     - sweep funds in specified wallet:account to new address in same
              account, or new or specified account in another wallet
  sweep_all - same as above, but sweep balances of all addresses in the account
  relay     - relay a transaction from a transaction file created using ‘sweep’
              or ‘transfer’ with the --no-relay option
  submit    - submit an autosigned transaction to a wallet and the network
  resubmit  - resubmit most recently submitted autosigned transaction (other
              actions are required: see Exporting Outputs below)
  abort     - abort the current transaction created with --autosign.  The
              transaction may be signed or unsigned
  txview    - display detailed information about a transaction file or files
  txlist    - same as above, but display terse information in tabular format
  dump      - produce JSON dumps of wallet metadata (accounts, addresses and
              labels) for a list or range of wallets
  restore   - same as ‘create’, but additionally restore wallet metadata from
              the corresponding JSON dump files created with ‘dump’
  export-outputs      - export outputs of watch-only wallets for import into
                        their corresponding offline wallets
  export-outputs-sign - same as above, plus request offline wallet to create
                        signed key images for import by ‘import-key-images’
  import-key-images   - import key images signed by offline wallets into their
                        corresponding watch-only wallets


                             ‘LABEL’ OPERATION NOTES

  This operation takes a LABEL_SPEC arg with the following format:

      WALLET:ACCOUNT:ADDRESS,"label text"

  where WALLET is a wallet number, ACCOUNT an account index, and ADDRESS an
  address index.


                              ‘NEW’ OPERATION NOTES

  This operation takes a NEW_ADDRESS_SPEC arg with the following format:

      WALLET[:ACCOUNT][,"label text"]

  where WALLET is a wallet number and ACCOUNT an account index.  If ACCOUNT
  is omitted, a new account will be created in the wallet.  Otherwise a new
  address will be created in the specified account.  An optional label text
  may be appended to the spec following a comma.


                           ‘TRANSFER’ OPERATION NOTES

  The transfer operation takes a TRANSFER_SPEC arg with the following format:

      SOURCE:ACCOUNT:ADDRESS,AMOUNT

  where SOURCE is a wallet number, ACCOUNT the source account index, ADDRESS
  the destination Monero address and AMOUNT the XMR amount to be sent.


                      ‘SWEEP’ AND ‘SWEEP_ALL’ OPERATION NOTES

  The sweep and sweep_all operations take a SWEEP_SPEC arg with the following
  format:

      SOURCE:ACCOUNT[,DEST[:ACCOUNT]]

  where SOURCE and DEST are wallet numbers and ACCOUNT account indices for the
  respective wallets.

  If DEST is omitted, a new address will be created in ACCOUNT of SOURCE, and
  funds from ACCOUNT of SOURCE will be swept into it.

  If DEST is included without its related ACCOUNT, funds from ACCOUNT of SOURCE
  will be swept into a newly created account in DEST, or the last existing
  account of DEST, if requested by the user.

  If both account indices are included, funds from ACCOUNT of SOURCE will be
  swept into ACCOUNT of DEST.

  The user is prompted before addresses are created or funds transferred.

  With ‘sweep’, if the source account has more than one address with a balance,
  the balance of a single randomly chosen address will be swept.  To sweep the
  balances of all addresses in an account, use ‘sweep_all’.


                      ‘SUBMIT’ AND ‘RELAY’ OPERATION NOTES

  By default, transactions are relayed to a monerod running on localhost at the
  default RPC port.  To relay transactions to a remote or non-default monerod
  via optional SOCKS proxy, use the --tx-relay-daemon option described above.

  When ‘submit’ is used with --autosign, the transaction filename must be
  omitted.


                      ‘DUMP’ AND ‘RESTORE’ OPERATION NOTES

  These commands produce and read JSON wallet dump files with the same
  filenames as their source wallets, plus a .dump extension.

  It’s highly advisable to make regular dumps of your Monero wallets and back
  up the dump files, which can be used to easily regenerate the wallets using
  the ‘restore’ operation, should the need arise.  For watch-only autosigning
  wallets, creating the dumps is as easy as executing ‘mmgen-xmrwallet
  --autosign dump’ from your wallet directory.  The dump files are formatted
  JSON and thus suitable for efficient incremental backup using git.


                      ‘TXVIEW’ AND ‘TXLIST’ OPERATION NOTES

  Transactions are displayed in chronological order based on submit time or
  creation time.  With --autosign, submitted transactions on the removable
  device are displayed.


                                SECURITY WARNING

  If you have an existing MMGen Monero hot wallet setup, you’re strongly
  advised to migrate to offline autosigning to avoid further exposing your
  private keys on your network-connected machine.  See OFFLINE AUTOSIGNING
  and ‘Replacing Existing Hot Wallets with Watch-Only Wallets’ below.


                                    EXAMPLES

  Note that the transacting examples in this section apply for a hot wallet
  setup, which is now deprecated.  See OFFLINE AUTOSIGNING below.

  Generate an XMR key-address file with 5 addresses from your default wallet:
  $ mmgen-keygen --coin=xmr 1-5

  Create 3 Monero wallets from the key-address file:
  $ mmgen-xmrwallet create *.akeys.mmenc 1-3

  After updating the blockchain, sync wallets 1 and 2:
  $ mmgen-xmrwallet sync *.akeys.mmenc 1,2

  Sweep all funds from account #0 of wallet 1 to a new address:
  $ mmgen-xmrwallet sweep *.akeys.mmenc 1:0

  Same as above, but use a TX relay on the Tor network:
  $ mmgen-xmrwallet --tx-relay-daemon=abcdefghijklmnop.onion:127.0.0.1:9050 sweep *.akeys.mmenc 1:0

  Sweep all funds from account #0 of wallet 1 to wallet 2:
  $ mmgen-xmrwallet sweep *.akeys.mmenc 1:0,2

  Send 0.1 XMR from account #0 of wallet 2 to an external address:
  $ mmgen-xmrwallet transfer *.akeys.mmenc 2:0:<monero address>,0.1

  Sweep all funds from account #0 of wallet 2 to a new address, saving the
  transaction to a file:
  $ mmgen-xmrwallet --no-relay sweep *.akeys.mmenc 2:0

  Relay the created sweep transaction via a host on the Tor network:
  $ mmgen-xmrwallet --tx-relay-daemon=abcdefghijklmnop.onion:127.0.0.1:9050 relay *XMR*.sigtx

  Create a new account in wallet 2:
  $ mmgen-xmrwallet new *.akeys.mmenc 2

  Create a new address in account 1 of wallet 2, with label:
  $ mmgen-xmrwallet new *.akeys.mmenc 2:1,"from ABC exchange"

  View all the XMR transaction files in the current directory, sending output
  to pager:
  $ mmgen-xmrwallet --pager txview *XMR*.sigtx


                               OFFLINE AUTOSIGNING

                                    Tutorial

  Master the basic concepts of the MMGen wallet system and the processes of
  wallet creation, conversion and backup described in the Getting Started
  guide.  Optionally create a default MMGen wallet on your offline machine
  using ‘mmgen-walletgen’.  If you choose not to do this, you’ll be prompted
  for a seed phrase at the start of each signing session.

  Familiarize yourself with the autosigning setup process as described in
  ‘mmgen-autosign --help’.  Prepare your removable device and set up the
  mountpoints on your offline and online machines according to the instructions
  therein.  Install ‘monero-wallet-rpc’ on your offline machine and the Monero
  CLI wallet and daemon binaries on your online machine.

  On the offline machine, insert the removable device and execute:

  $ mmgen-autosign --xmrwallets=1-2,7 setup

  This will create 3 Monero signing wallets with indexes 1, 2 and 7 and primary
  addresses matching your seed’s Monero addresses with the same indexes.  (Note
  that these particular indexes are arbitrary, for purposes of illustration
  only.  Feel free to choose your own list and/or range – or perhaps just the
  number ‘1’ if one wallet is all you require).

  These signing wallets are written to volatile memory and exist only for the
  duration of the signing session, just like the temporary MMGen signing wallet
  they’re generated from (see ‘mmgen-autosign --help’).

  A viewkey-address file for the 3 addresses will also be written to the
  removable device.  The data in this file will be used to create and access
  watch-only wallets on your online machine that match the signing wallets
  you’ve just created.

  When the setup operation completes, extract the removable device and restart
  the autosign script in wait mode:

  $ mmgen-autosign --coins=xmr --stealth-led wait

  Your only further physical interaction with the offline signing machine now
  (assuming everything goes as planned) will be inserting and extracting the
  removable device on it.  And this is the whole point of autosigning: to make
  cold signing as convenient as possible, almost like transacting with a hot
  wallet.

  If your signing machine is an SoC with MMGen Wallet LED support (see
  ‘mmgen-autosign --help’), a quickly flashing LED will indicate that signing
  is in progress, a slowly flashing LED an error condition, and no LED that the
  program is idle and waiting for device insertion.

  On your online machine, start monerod, wait until it’s fully synced with the
  network, insert the removable device and execute:

  $ mmgen-xmrwallet --autosign --restore-height=current create

  This will create 3 watch-only wallets matching your 3 offline signing wallets
  and write them to the current directory (an alternate wallet directory may be
  specified with the --wallet-dir option).

  Note that --restore-height=current is required to prevent a time-consuming
  full sync of the wallets from the Genesis block, a meaningless waste of time
  in this case since the wallets contain no funds.

  Also make note of the --autosign option, a requirement for ALL autosigning
  operations with ‘mmgen-xmrwallet’.

  Now list your newly created wallets:

  $ mmgen-xmrwallet --autosign list

  Note that you can also use the ‘sync’ operation here, which produces more
  abbreviated output than ‘list’.

  Send some XMR (preferably a tiny amount) to the primary address of wallet #7.
  Once the transaction has confirmed, invoke ‘sync’ or ‘list’ again to verify
  the funds have arrived.

  Since offline wallet #7 has no knowledge of the funds received by its online
  counterpart, we need to update its state.  Export the outputs of watch-only
  wallet #7 as follows:

  $ mmgen-xmrwallet --autosign export-outputs 7

  The outputs are now saved to the removable device and will be imported into
  offline wallet #7 when you sign your first transaction.

  Now you’re ready to begin transacting.  Let’s start by sweeping your funds in
  wallet #7’s primary address (account 0) to a new address in the same account:

  $ mmgen-xmrwallet --autosign sweep 7:0

  This operation creates an unsigned sweep transaction and saves it to the
  removable device.

  Now extract the removable device and insert it on the offline machine.  Wait
  for the quick LED flashing to stop (or the blue ‘safe to extract’ message, in
  the absence of LED support), signalling that signing is complete.

  Note that the offline wallet has performed two operations in one go here:
  an import of wallet outputs from the previous step and the signing of your
  just-created sweep transaction.

  Extract the removable device, insert it on your online machine and submit the
  signed sweep transaction to the watch-only wallet, which will broadcast it to
  the network:

  $ mmgen-xmrwallet --autosign submit

  Note that you may also relay the transaction to a remote daemon, optionally
  via a Tor proxy, using the --tx-relay-daemon option documented above.

  Once your transaction has confirmed, invoke ‘list’ or ‘sync’ to view your
  wallets’ balances.

  Congratulations, you’ve performed your first autosigned Monero transaction!

  For other examples, consult the EXAMPLES section above, noting the following
  differences that apply to autosigning:

    1) The --autosign option must always be included.
    2) The key-address file argument must always be omitted.
    3) The ‘relay’ operation is replaced by ‘submit’, with TX filename omitted.
    4) Always remember to sign your transactions after a ‘sweep’ or ‘transfer’
       operation.
    5) Always remember to export a wallet’s outputs when it has received funds
       from an outside source.


                                Exporting Outputs

  Exporting outputs from a watch-only wallet is generally required in only
  three cases:

    a) at the start of each signing session (after ‘mmgen-autosign setup’);
    b) after the wallet has received funds from an outside source or another
       wallet; and
    c) after performing a ‘resubmit’ operation.

  You might also need to do it, however, if an offline wallet is unable to sign
  a transaction due to missing outputs.

  At the start of a new signing session, you must export outputs from ALL
  wallets you intend to transact with.  This is necessary because the offline
  signing wallets have just been created and know nothing about the state of
  their online counterparts.

  Export outputs from a wallet as follows (for all wallets, omit the index):

  $ mmgen-xmrwallet --autosign export-outputs <wallet index>

  Then insert the removable device on the offline machine.  This will import
  the outputs into the corresponding signing wallet(s) (and optionally redo any
  failed transaction signing operation).

  Following a ‘resubmit’, use the ‘export-outputs-sign’ operation instead, and
  add the --rescan-spent option:

  $ mmgen-xmrwallet --autosign --rescan-spent export-outputs-sign <wallet index>

  Here the offline signing wallet(s) will also create signed key images. Insert
  the removable device on your online machine and import the signed key images
  into your online wallet as follows:

  $ mmgen-xmrwallet --autosign import-key-images

  Usually, this is all that is required.  However, if your wallet continues to
  show an incorrect balance after the import operation, you’ll need to re-run
  ‘export-outputs-sign’ with the --rescan-blockchain option, followed by another
  offline signing and online key image import.  Note that blockchain rescans can
  take a long time, so patience is required here.


             Replacing Existing Hot Wallets with Watch-Only Wallets

  If you have an existing MMGen Monero hot wallet setup, you can migrate to
  offline transaction signing by ‘cloning’ your existing hot wallets as
  watch-only ones via the ‘dump’ and ‘restore’ operations described below.

  For additional security, it’s also wise to create new watch-only wallets that
  have never had keys exposed on an online machine and gradually transfer all
  funds from your ‘cloned’ wallets to them.  The creation of new wallets is
  explained in the Tutorial above.

  Start the cloning process by making dump files of your hot wallets’ metadata
  (accounts, subaddresses and labels).  ‘cd’ to the wallet directory (or use
  --wallet-dir) and execute:

  $ mmgen-xmrwallet dump /path/to/key-address-file.akeys{.mmenc}

  If you’ve been transacting with the wallets, you know where their key-address
  file is along with its encryption password, if any.  Supply an additional
  index range and/or list at the end of the command line if the key-address
  file contains more wallets than exist on disk or there are wallets you wish
  to ignore.

  Do a directory listing to verify that the dump files are present alongside
  their source wallet files ending with ‘MoneroWallet’.  Then execute:

  $ mmgen-xmrwallet --watch-only restore /path/to/key-address-file.akeys{.mmenc}

  This will create watch-only wallets that “mirror” the old hot wallets and
  populate them with the metadata saved in the dump files.

  Note that watch-only wallet filenames end with ‘MoneroWatchOnlyWallet’.  Your
  old hot wallets will be ignored from here on.  Eventually, you’ll want to
  destroy them.

  Your new wallets must now be synced with the blockchain.  Begin by starting
  monerod and synchronizing with the network.

  Mount ‘/mnt/mmgen_autosign’ and locate the file in the ‘xmr’ directory with
  the .vkeys extension, which contains the passwords you’ll need to log into
  the wallets.  This is a plain text file viewable with ‘cat’, ‘less’ or your
  favorite text editor.

  Then log into each watch-only wallet in turn as follows:

  $ monero-wallet-cli --wallet <wallet filename>

  Upon login, each wallet will begin syncing, a process which can take more
  than an hour depending on your hardware.  Note, however, that the process
  is interruptible: you may exit ‘monero-wallet-cli’ at any point, log back
  in again and resume where you left off.

  Once your watch-only wallets are synced, you need to export their outputs:

  $ mmgen-xmrwallet --autosign export-outputs-sign

  Now insert the removable device on the offline machine and wait until the LED
  stops flashing (or ‘safe to extract’).  The wallet outputs are now imported
  into the signing wallets and corresponding signed key images have been
  written to the removable device.

  Insert the removable device on your online machine and import the key images
  into your watch-only wallets:

  $ mmgen-xmrwallet --autosign import-key-images

  Congratulations, your watch-only wallets are now complete and you may begin
  transacting!  First perform a ‘sync’ or ‘list’ to ensure that your balances
  are correct.  Then you might try sweeping some funds as described in the
  Tutorial above.

  Once you’ve gained proficiency with the autosigning process and feel ready
  to delete your old hot wallets, make sure to do so securely using ‘shred’,
  ‘wipe’ or some other secure deletion utility.

  MMGEN-WALLET 16.0.0            September 2025             MMGEN-XMRWALLET(1)
```
