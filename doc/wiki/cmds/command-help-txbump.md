```text
  MMGEN-TXBUMP: Create, and optionally send and sign, a replacement transaction
                on supporting networks
  USAGE:        mmgen-txbump [opts] [MMGen TX file] [seed source] ...
                mmgen-txbump [opts] [ADDR,AMT ... | DATA_SPEC] ADDR [MMGen TX file] [seed source] ...
  OPTIONS:
  -h, --help             Print this help message
      --longhelp         Print help message for long (global) options
  -a, --autosign         Bump the most recent transaction created and sent with
                         the --autosign option. The removable device is mounted
                         and unmounted automatically.  The transaction file
                         argument must be omitted.  Note that only sent trans-
                         actions may be bumped with this option.  To redo an
                         unsent --autosign transaction, first delete it using
                         ‘mmgen-txsend --abort’ and then create a new one
  -b, --brain-params l,p Use seed length 'l' and hash preset 'p' for
                         brainwallet input
  -c, --comment-file   f Source the transaction's comment from file 'f'
  -d, --outdir         d Specify an alternate directory 'd' for output
  -e, --echo-passphrase  Print passphrase to screen when typing it
  -f, --fee            f Transaction fee, as a decimal BTC amount or as
                         satoshis per byte (an integer followed by ‘s’).
                         See FEE SPECIFICATION below.
  -H, --hidden-incog-input-params f,o  Read hidden incognito data from file
                        'f' at offset 'o' (comma-separated)
  -i, --in-fmt         f Input is from wallet format 'f' (see FMT CODES below)
  -l, --seed-len       l Specify wallet seed length of 'l' bits. This option
                         is required only for brainwallet and incognito inputs
                         with non-standard (< 256-bit) seed lengths.
  -k, --keys-from-file f Provide additional keys for non-MMGen addresses
  -K, --keygen-backend n Use backend 'n' for public key generation.  Options
                         for BTC: 1:libsecp256k1 [default] 2:python-ecdsa
  -M, --mmgen-keys-from-file f Provide keys for MMGen addresses in a key-
                         address file (output of 'mmgen-keygen'). Permits
                         online signing without an MMGen seed source. The
                         key-address file is also used to verify MMGen-to-BTC
                         mappings, so the user should record its checksum.
  -o, --output-to-reduce o Deduct the fee from output 'o' (an integer, or 'c'
                         for the transaction's change output, if present)
  -O, --old-incog-fmt    Specify old-format incognito input
  -p, --hash-preset    p Use the scrypt hash parameters defined by preset 'p'
                         for password hashing (default: '3')
  -P, --passwd-file    f Get MMGen wallet passphrase from file 'f'
  -q, --quiet            Suppress warnings; overwrite files without prompting
  -s, --send             Sign and send the transaction (the default if seed
                         data is provided)
  -T, --txhex-idx N      Send only part ‘N’ of a multi-part transaction.
                         Indexing begins with one.
  -v, --verbose          Produce more verbose output
  -W, --allow-non-wallet-swap Allow signing of swap transactions that send funds
                         to non-wallet addresses
  -x, --proxy P          Fetch the swap quote via SOCKS5h proxy ‘P’ (host:port).
                         Use special value ‘env’ to honor *_PROXY environment
                         vars instead.
  -y, --yes              Answer 'yes' to prompts, suppress non-essential output
  -z, --show-hash-presets Show information on available hash presets


  With --autosign, the TX file argument is omitted, and the last submitted TX
  file on the removable device will be used.

  If no outputs are specified, the original outputs will be used for the
  replacement transaction, otherwise a new transaction will be created with the
  outputs listed on the command line.  The syntax for the output arguments is
  identical to that of ‘mmgen-txcreate’.

  The user should take care to select a fee sufficient to ensure the original
  transaction is replaced in the mempool.

  When bumping a swap transaction, the swap protocol’s quote server on the
  Internet must be reachable either directly or via the SOCKS5 proxy specified
  with the --proxy option.  To improve privacy, it’s recommended to proxy
  requests to the quote server via Tor or some other anonymity network.


                                 FEE SPECIFICATION

  Transaction fees, both on the command line and at the interactive prompt, may
  be specified as either absolute coin amounts, using a plain decimal number, or
  as satoshis per byte, using an integer followed by ‘s’, for satoshi.


  Transactions may contain both MMGen or non-MMGen input addresses.

  To sign non-MMGen inputs, a coin daemon wallet dump or flat key list is used
  as the key source (--keys-from-file option).

  To sign MMGen inputs, key data is generated from a seed as with the
  mmgen-addrgen and mmgen-keygen commands.  Alternatively, a key-address file
  may be used (--mmgen-keys-from-file option).

  Multiple wallets or other seed files can be listed on the command line in
  any order.  If the seeds required to sign the transaction’s inputs are not
  found in these files (or in the default wallet), the user will be prompted
  for seed data interactively.

  To prevent an attacker from crafting transactions with bogus MMGen-to-Bitcoin
  address mappings, all outputs to MMGen addresses are verified with a seed
  source.  Therefore, seed files or a key-address file for all MMGen outputs
  must also be supplied on the command line if the data can’t be found in the
  default wallet.

  Seed source files must have the canonical extensions listed in the 'FileExt'
  column below:


  FMT CODES:

    Format             FileExt   Valid codes
    ------             -------   -----------
    BIP39Mnemonic      .bip39    bip39
    Brainwallet        .mmbrain  mmbrain,brainwallet,brain,bw
    DieRollWallet      .b6d      b6d,die,dieroll
    IncogWallet        .mmincog  mmincog,incog,icg,i
    IncogWalletHex     .mmincox  mmincox,incox,incog_hex,ix,xi
    IncogWalletHidden  None      incog_hidden,hincog,ih,hi
    MMGenHexSeedFile   .mmhex    seedhex,hexseed,mmhex
    MMGenMnemonic      .mmwords  mmwords,words,mnemonic,mn,m
    MMGenSeedFile      .mmseed   mmseed,seed,s
    MMGenWallet        .mmdat    wallet,w
    PlainHexSeedFile   .hex      hex,rawhex,plainhex

  MMGEN-WALLET 16.0.0            September 2025                MMGEN-TXBUMP(1)
```
