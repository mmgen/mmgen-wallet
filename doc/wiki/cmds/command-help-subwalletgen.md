```text
  MMGEN-SUBWALLETGEN: Generate a subwallet from the default or specified MMGen wallet
  USAGE:              mmgen-subwalletgen [opts] [infile] <Subseed Index>
  OPTIONS:
  -h, --help            Print this help message
      --longhelp        Print help message for long (global) options
  -d, --outdir       d  Output files to directory 'd' instead of working dir
  -e, --echo-passphrase Echo passphrases and other user input to screen
  -i, --in-fmt       f  Input from wallet format 'f' (see FMT CODES below)
  -o, --out-fmt      f  Output to wallet format 'f' (see FMT CODES below)
  -H, --hidden-incog-input-params f,o  Read hidden incognito data from file
                        'f' at offset 'o' (comma-separated)
  -J, --hidden-incog-output-params f,o  Write hidden incognito data to file
                        'f' at offset 'o' (comma-separated). File 'f' will be
                        created if necessary and filled with random data.
  -O, --old-incog-fmt   Specify old-format incognito input
  -k, --keep-passphrase Reuse passphrase of input wallet for output wallet
  -K, --keep-hash-preset Reuse hash preset of input wallet for output wallet
  -l, --seed-len     l  Specify wallet seed length of 'l' bits.  This option
                        is required only for brainwallet and incognito inputs
                        with non-standard (< 256-bit) seed lengths.
  -L, --label        l  Specify a label 'l' for output wallet
  -m, --keep-label      Reuse label of input wallet for output wallet
  -p, --hash-preset  p  Use the scrypt hash parameters defined by preset 'p'
                        for password hashing (default: '3')
  -z, --show-hash-presets Show information on available hash presets
  -P, --passwd-file  f  Get wallet passphrase from file 'f'
  -N, --passwd-file-new-only Use passwd file only for new, not existing, wallet
  -q, --quiet           Produce quieter output; suppress some warnings
  -r, --usr-randchars n Get 'n' characters of additional randomness from user
                        (min=10, max=80, default=30)
  -S, --stdout          Write wallet data to stdout instead of file
  -v, --verbose         Produce more verbose output


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

  MMGEN-WALLET 16.0.0            September 2025           MMGEN-SUBWALLETGEN(1)
```
