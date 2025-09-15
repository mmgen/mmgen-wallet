```text
  MMGEN-PASSGEN: Generate a range or list of passwords from an MMGen wallet,
                 mnemonic, seed or brainwallet for the given ID string
  USAGE:         mmgen-passgen [opts] [seed source] <ID string> <index list or range(s)>
  OPTIONS:
  -h, --help            Print this help message
      --longhelp        Print help message for long (global) options
  -d, --outdir       d  Output files to directory 'd' instead of working dir
  -e, --echo-passphrase Echo passphrase or mnemonic to screen upon entry
  -f, --passwd-fmt   f  Generate passwords of format 'f'.  Default: b58.
                        See PASSWORD FORMATS below
  -i, --in-fmt       f  Input is from wallet format 'f' (see FMT CODES below)
  -H, --hidden-incog-input-params f,o  Read hidden incognito data from file
                        'f' at offset 'o' (comma-separated)
  -O, --old-incog-fmt   Specify old-format incognito input
  -L, --passwd-len   l  Specify length of generated passwords.  For defaults,
                        see PASSWORD FORMATS below.  An argument of 'h' will
                        generate passwords of half the default length.
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
  -S, --stdout          Print passwords to stdout
  -v, --verbose         Produce more verbose output


                             NOTES FOR THIS COMMAND

  ID string must be a valid UTF-8 string not longer than 256 characters and
  not containing the symbols ' ", ":", "/", "\'.

  Password indexes are given as a comma-separated list and/or hyphen-separated
  range(s).

  Changing either the password format (base32,base58) or length alters the seed
  and thus generates a completely new set of passwords.

  PASSWORD FORMATS:

    Code       Description                Min Len  Max Len  Default Len
    b32      - base32 password            10       42       24
    b58      - base58 password            8        36       20
    bip39    - BIP39 mnemonic             12       24       24
    xmrseed  - Monero new-style mnemonic  25       25       25
    hex      - hexadecimal password       32       64       64

  EXAMPLES:

    Generate ten base58 passwords of length 20 for Alice's email account:
    mmgen-passgen alice@nowhere.com 1-10

    Generate ten base58 passwords of length 16 for Alice's email account:
    mmgen-passgen --passwd-len=16 alice@nowhere.com 1-10

    Generate ten base32 passwords of length 24 for Alice's email account:
    mmgen-passgen --passwd-fmt=b32 alice@nowhere.com 1-10

    Generate three BIP39 mnemonic seed phrases of length 24 for Alice's
    Trezor device:
    mmgen-passgen --passwd-fmt=bip39 mytrezor 1-3

    All passwords are cryptographically unlinkable with each other, including
    passwords with the same format but different length, so Alice needn't worry
    about inadvertent reuse of private data.


                        NOTES FOR ALL GENERATOR COMMANDS

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

  MMGEN-WALLET 16.0.0            September 2025               MMGEN-PASSGEN(1)
```
