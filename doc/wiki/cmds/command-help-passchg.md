```text
  MMGEN-PASSCHG: Change the passphrase, hash preset or label of the default or specified MMGen wallet
  USAGE:         mmgen-passchg [opts] [infile]
  OPTIONS:
  -h, --help            Print this help message
      --longhelp        Print help message for long (global) options
  -d, --outdir       d  Output files to directory 'd' instead of working dir
  -e, --echo-passphrase Echo passphrases and other user input to screen
  -f, --force-update    Force update of wallet even if nothing has changed
  -i, --in-fmt       f  Input from wallet format 'f' (see FMT CODES below)
  -H, --hidden-incog-input-params f,o  Read hidden incognito data from file
                        'f' at offset 'o' (comma-separated)
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


  PASSPHRASE NOTE:

  For passphrases all combinations of whitespace are equal, and leading and
  trailing space are ignored.  This permits reading passphrase or brainwallet
  data from a multi-line file with free spacing and indentation.


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

  MMGEN-WALLET 16.0.0            September 2025               MMGEN-PASSCHG(1)
```
