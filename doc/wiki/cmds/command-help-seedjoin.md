```text
  MMGEN-SEEDJOIN: Regenerate an MMGen deterministic wallet from seed shares
                  created by 'mmgen-seedsplit'
  USAGE:          mmgen-seedjoin [options] share1 share2 [...shareN]
  OPTIONS:
  -h, --help            Print this help message
      --longhelp        Print help message for long (global) options
  -d, --outdir       d  Output file to directory 'd' instead of working dir
  -e, --echo-passphrase Echo passphrases and other user input to screen
  -i, --id-str       s  ID String of split (required for master share join only)
  -H, --hidden-incog-input-params f,o  Read hidden incognito data from file
                        'f' at offset 'o' (comma-separated).  NOTE: only the
                        first share may be in hidden incognito format!
  -J, --hidden-incog-output-params f,o  Write hidden incognito data to file
                        'f' at offset 'o' (comma-separated). File 'f' will be
                        created if necessary and filled with random data.
  -o, --out-fmt      f  Output to wallet format 'f' (see FMT CODES below)
  -O, --old-incog-fmt   Specify old-format incognito input
  -L, --label        l  Specify a label 'l' for output wallet
  -M, --master-share i  Use a master share with index 'i' (min:1, max:1024)
  -p, --hash-preset  p  Use the scrypt hash parameters defined by preset 'p'
                        for password hashing (default: '3')
  -z, --show-hash-presets Show information on available hash presets
  -P, --passwd-file  f  Get wallet passphrase from file 'f'
  -q, --quiet           Produce quieter output; suppress some warnings
  -r, --usr-randchars n Get 'n' characters of additional randomness from user
                        (min=10, max=80, default=30)
  -S, --stdout          Write wallet data to stdout instead of file
  -v, --verbose         Produce more verbose output


  COMMAND NOTES:

  When joining with a master share, the master share must be listed first.
  The remaining shares may be listed in any order.

  The --id-str option is required only for master share joins.  For ordinary
  joins it will be ignored.

  For usage examples, see the help screen for the 'mmgen-seedsplit' command.

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

  MMGEN-WALLET 16.0.0            September 2025              MMGEN-SEEDJOIN(1)
```
