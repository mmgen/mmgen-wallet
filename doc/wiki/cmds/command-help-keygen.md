```text
  MMGEN-KEYGEN: Generate a range or list of secret keys from an MMGen wallet,
                 mnemonic, seed or brainwallet
  USAGE:        mmgen-keygen [opts] [seed source] <index list or range(s)>
  OPTIONS:
  -h, --help            Print this help message
      --longhelp        Print help message for long (global) options
  -A, --no-addresses    Print only secret keys, no addresses
  -c, --print-checksum  Print address list checksum and exit
  -d, --outdir       d  Output files to directory 'd' instead of working dir
  -e, --echo-passphrase Echo passphrase or mnemonic to screen upon entry
  -i, --in-fmt       f  Input is from wallet format 'f' (see FMT CODES below)
  -H, --hidden-incog-input-params f,o  Read hidden incognito data from file
                        'f' at offset 'o' (comma-separated)
  -O, --old-incog-fmt   Specify old-format incognito input
  -k, --use-internal-keccak-module Force use of the internal keccak module
  -K, --keygen-backend n Use backend 'n' for public key generation.  Options
                        for BTC: 1:libsecp256k1 [default] 2:python-ecdsa
  -l, --seed-len     l  Specify wallet seed length of 'l' bits.  This option
                        is required only for brainwallet and incognito inputs
                        with non-standard (< 256-bit) seed lengths.
  -p, --hash-preset  p  Use the scrypt hash parameters defined by preset 'p'
                        for password hashing (default: '3')
  -z, --show-hash-presets Show information on available hash presets
  -P, --passwd-file  f  Get wallet passphrase from file 'f'
  -q, --quiet           Produce quieter output; suppress some warnings
  -r, --usr-randchars n Get 'n' characters of additional randomness from user
                        (min=10, max=80, default=30)
  -S, --stdout          Print keys to stdout
  -t, --type t          Choose address type. Options: see ADDRESS TYPES below
                        (default: 'L' or 'legacy')
  -U, --subwallet    U  Generate keys for subwallet 'U' (see SUBWALLETS
                        below)
  -V, --viewkeys        Print viewkeys, omitting secret keys
  -v, --verbose         Produce more verbose output
  -x, --b16             Print secret keys in hexadecimal too


                             NOTES FOR THIS COMMAND

  Address indexes are given as a comma-separated list and/or hyphen-separated
  range(s).

  By default, both addresses and secret keys are generated.

  If available, the libsecp256k1 library will be used for address generation.


                        NOTES FOR ALL GENERATOR COMMANDS

  SUBWALLETS:

  Subwallets (subseeds) are specified by a ‘Subseed Index’ consisting of:

    a) an integer in the range 1-1000000, plus
    b) an optional single letter, ‘L’ or ‘S’

  The letter designates the length of the subseed.  If omitted, ‘L’ is assumed.

  Long (‘L’) subseeds are the same length as their parent wallet’s seed
  (typically 256 bits), while short (‘S’) subseeds are always 128-bit.
  The long and short subseeds for a given index are derived independently,
  so both may be used.

  MMGen Wallet has no notion of ‘depth’, and to an outside observer subwallets
  are identical to ordinary wallets.  This is a feature rather than a bug, as
  it denies an attacker any way of knowing whether a given wallet has a parent.

  Since subwallets are just wallets, they may be used to generate other
  subwallets, leading to hierarchies of arbitrary depth.  However, this is
  inadvisable in practice for two reasons:  Firstly, it creates accounting
  complexity, requiring the user to independently keep track of a derivation
  tree.  More importantly, however, it leads to the danger of Seed ID
  collisions between subseeds at different levels of the hierarchy, as
  MMGen checks and avoids ID collisions only among sibling subseeds.

  An exception to this caveat would be a multi-user setup where sibling
  subwallets are distributed to different users as their default wallets.
  Since the subseeds derived from these subwallets are private to each user,
  Seed ID collisions among them doesn’t present a problem.

  A safe rule of thumb, therefore, is for *each user* to derive all of his/her
  subwallets from a single parent.  This leaves each user with a total of two
  million subwallets, which should be enough for most practical purposes.

  PASSPHRASE NOTE:

  For passphrases all combinations of whitespace are equal, and leading and
  trailing space are ignored.  This permits reading passphrase or brainwallet
  data from a multi-line file with free spacing and indentation.

  BRAINWALLET NOTE:

  To thwart dictionary attacks, it’s recommended to use a strong hash preset
  with brainwallets.  For a brainwallet passphrase to generate the correct
  seed, the same seed length and hash preset parameters must always be used.


  ADDRESS TYPES:

    Code Type           Description
    ---- ----           -----------
    ‘L’  legacy       - Legacy uncompressed address
    ‘C’  compressed   - Compressed P2PKH address
    ‘S’  segwit       - Segwit P2SH-P2WPKH address
    ‘B’  bech32       - Native Segwit (Bech32) address
    ‘X’  bech32x      - Cross-chain Bech32 address
    ‘E’  ethereum     - Ethereum address
    ‘Z’  zcash_z      - Zcash z-address
    ‘M’  monero       - Monero address


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

  MMGEN-WALLET 16.0.0            September 2025                MMGEN-KEYGEN(1)
```
