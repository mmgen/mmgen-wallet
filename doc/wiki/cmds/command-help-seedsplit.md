```text
  MMGEN-SEEDSPLIT: Generate a seed share from the default or specified MMGen wallet
  USAGE:           mmgen-seedsplit [opts] [infile] [<Split ID String>:]<index>:<share count>
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
  -l, --seed-len     l  Specify wallet seed length of 'l' bits.  This option
                        is required only for brainwallet and incognito inputs
                        with non-standard (< 256-bit) seed lengths.
  -L, --label        l  Specify a label 'l' for output wallet
  -M, --master-share i  Use a master share with index 'i' (min:1, max:1024)
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


  COMMAND NOTES:

  This command generates shares one at a time.  Shares may be output to any
  MMGen wallet format, with one limitation: only one share in a given split may
  be in hidden incognito format, and it must be the master share in the case of
  a master-share split.

  If the command's optional first argument is omitted, the default wallet is
  used for the split.

  The last argument is a seed split specifier consisting of an optional split
  ID, a share index, and a share count, all separated by colons.  The split ID
  must be a valid UTF-8 string.  If omitted, the ID 'default' is used.  The
  share index (the index of the share being generated) must be in the range
  1-1024 and the share count (the total number of shares in the split)
  in the range 2-1024.

  Master Shares

  Each seed has a total of 1024 master shares, which can be used as the first
  shares in multiple splits if desired.  To generate a master share, use the
  --master-share (-M) option with an index in the range 1-1024 and omit
  the last argument.

  When creating and joining a split using a master share, ensure that the same
  master share index is used in all split and join commands.

  EXAMPLES:

    Split a BIP39 seed phrase into two BIP39 shares.  Rejoin the split:

      $ echo 'zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong' > sample.bip39

      $ mmgen-seedsplit -o bip39 sample.bip39 1:2
      BIP39 mnemonic data written to file '03BAE887-default-1of2[D51CB683][128].bip39'

      $ mmgen-seedsplit -o bip39 sample.bip39 2:2
      BIP39 mnemonic data written to file '03BAE887-default-2of2[67BFD36E][128].bip39'

      $ mmgen-seedjoin -o bip39 \
          '03BAE887-default-2of2[67BFD36E][128].bip39' \
          '03BAE887-default-1of2[D51CB683][128].bip39'
      BIP39 mnemonic data written to file '03BAE887[128].bip39'

      $ cat '03BAE887[128].bip39'
      zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong

    Create a 3-way default split of your default wallet, outputting all shares
    to default wallet format.  Rejoin the split:

      $ mmgen-seedsplit 1:3 # Step A
      $ mmgen-seedsplit 2:3 # Step B
      $ mmgen-seedsplit 3:3 # Step C
      $ mmgen-seedjoin <output_of_step_A> <output_of_step_B> <output_of_step_C>

    Create a 2-way split of your default wallet with ID string 'alice',
    outputting shares to MMGen native mnemonic format.  Rejoin the split:

      $ mmgen-seedsplit -o words alice:1:2 # Step D
      $ mmgen-seedsplit -o words alice:2:2 # Step E
      $ mmgen-seedjoin <output_of_step_D> <output_of_step_E>

    Create a 2-way split of your default wallet with ID string 'bob' using
    master share #7, outputting share #1 (the master share) to default wallet
    format and share #2 to BIP39 format.  Rejoin the split:

      $ mmgen-seedsplit -M7                   # Step X
      $ mmgen-seedsplit -M7 -o bip39 bob:2:2  # Step Y
      $ mmgen-seedjoin -M7 --id-str=bob <output_of_step_X> <output_of_step_Y>

    Create a 2-way split of your default wallet with ID string 'alice' using
    master share #7.  Rejoin the split using master share #7 generated in the
    previous example:

      $ mmgen-seedsplit -M7 -o bip39 alice:2:2 # Step Z
      $ mmgen-seedjoin -M7 --id-str=alice <output_of_step_X> <output_of_step_Z>

    Create a 2-way default split of your default wallet with an incognito-format
    master share hidden in file 'my.hincog' at offset 1325.  Rejoin the split:

      $ mmgen-seedsplit -M4 -o hincog -J my.hincog,1325 1:2 # Step M (share A)
      $ mmgen-seedsplit -M4 -o bip39 2:2                    # Step N (share B)
      $ mmgen-seedjoin -M4 -H my.hincog,1325 <output_of_step_N>

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

  MMGEN-WALLET 16.0.0            September 2025             MMGEN-SEEDSPLIT(1)
```
