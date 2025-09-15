# Detailed usage information for `mmgen-tool` commands

## Table of Contents
* [General string conversion and hashing utilities](#a_1)
* [Cryptocoin key/address utilities](#a_2)
* [Seed phrase utilities](#a_3)
* [Utilities for viewing/checking MMGen address and transaction files](#a_4)
* [File encryption and decryption](#a_5)
* [File utilities](#a_6)
* [Key, address or subseed generation from an MMGen wallet](#a_7)
* [Tracking-wallet commands using the JSON-RPC interface](#a_8)

## <a id="a_1">General string conversion and hashing utilities:</a>

### `mmgen-tool b32tohex`

```text
Convert an MMGen-flavor base 32 string to hexadecimal

USAGE: mmgen-tool [OPTS] b32tohex ARG [KEYWORD ARG]

Required ARG (type shown in square brackets):

  b32_str [str] (use '-' to read from STDIN)

Optional KEYWORD ARG (type and default value shown in square brackets):

  pad [int=0] Pad output to this width
```

### `mmgen-tool b58chktohex`

```text
Convert a base58-check encoded string to hexadecimal

USAGE: mmgen-tool [OPTS] b58chktohex ARG

Required ARG (type shown in square brackets):

  b58chk_str [str] (use '-' to read from STDIN)
```

### `mmgen-tool b58tobytes`

```text
Convert a base 58 string to bytes (warning: outputs binary data)

USAGE: mmgen-tool [OPTS] b58tobytes ARG [KEYWORD ARG]

Required ARG (type shown in square brackets):

  b58_str [str] (use '-' to read from STDIN)

Optional KEYWORD ARG (type and default value shown in square brackets):

  pad [int=0] Pad output to this width
```

### `mmgen-tool b58tohex`

```text
Convert a base 58 string to hexadecimal

USAGE: mmgen-tool [OPTS] b58tohex ARG [KEYWORD ARG]

Required ARG (type shown in square brackets):

  b58_str [str] (use '-' to read from STDIN)

Optional KEYWORD ARG (type and default value shown in square brackets):

  pad [int=0] Pad output to this width
```

### `mmgen-tool b6dtohex`

```text
Convert a die roll base6 (base6d) string to hexadecimal

USAGE: mmgen-tool [OPTS] b6dtohex ARG [KEYWORD ARG]

Required ARG (type shown in square brackets):

  b6d_str [str] (use '-' to read from STDIN)

Optional KEYWORD ARG (type and default value shown in square brackets):

  pad [int=0] Pad output to this width
```

### `mmgen-tool bytespec`

```text
Convert a byte specifier such as ‘4GB’ into an integer

USAGE: mmgen-tool [OPTS] bytespec ARG

Required ARG (type shown in square brackets):

  dd_style_byte_specifier [str]

Valid specifiers:

  c  = 1
  w  = 2
  b  = 512
  kB = 1000
  K  = 1024
  MB = 1000000
  M  = 1048576
  GB = 1000000000
  G  = 1073741824
  TB = 1000000000000
  T  = 1099511627776
  PB = 1000000000000000
  P  = 1125899906842624
  EB = 1000000000000000000
  E  = 1152921504606846976
```

### `mmgen-tool bytestob58`

```text
Convert bytes to base 58 (supply data via STDIN)

USAGE: mmgen-tool [OPTS] bytestob58 ARG [KEYWORD ARG]

Required ARG (type shown in square brackets):

  infile [str]

Optional KEYWORD ARG (type and default value shown in square brackets):

  pad [int=0] Pad output to this width
```

### `mmgen-tool hash160`

```text
Compute ripemd160(sha256(data)) (convert hex pubkey to hex addr)

USAGE: mmgen-tool [OPTS] hash160 ARG

Required ARG (type shown in square brackets):

  hexstr [str] (use '-' to read from STDIN)
```

### `mmgen-tool hash256`

```text
Compute sha256(sha256(data)) (double sha256)

USAGE: mmgen-tool [OPTS] hash256 ARG [KEYWORD ARGS]

Required ARG (type shown in square brackets):

  data [str]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  file_input [bool=False] First arg is the name of a file containing the data
  hex_input  [bool=False] First arg is a hexadecimal string
```

### `mmgen-tool hexdump`

```text
Create hexdump of data from file (use '-' for stdin)

USAGE: mmgen-tool [OPTS] hexdump ARG [KEYWORD ARGS]

Required ARG (type shown in square brackets):

  infile [str]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  cols      [int=8]     Number of columns in output
  line_nums [str='hex'] Format for line numbers (valid choices: 'hex','dec')
```

### `mmgen-tool hexlify`

```text
Convert bytes in file to hexadecimal (use '-' for stdin)

USAGE: mmgen-tool [OPTS] hexlify ARG

Required ARG (type shown in square brackets):

  infile [str]
```

### `mmgen-tool hexreverse`

```text
Reverse bytes of a hexadecimal string

USAGE: mmgen-tool [OPTS] hexreverse ARG

Required ARG (type shown in square brackets):

  hexstr [str] (use '-' to read from STDIN)
```

### `mmgen-tool hextob32`

```text
Convert a hexadecimal string to an MMGen-flavor base 32 string

USAGE: mmgen-tool [OPTS] hextob32 ARG [KEYWORD ARG]

Required ARG (type shown in square brackets):

  hexstr [str] (use '-' to read from STDIN)

Optional KEYWORD ARG (type and default value shown in square brackets):

  pad [int=0] Pad output to this width
```

### `mmgen-tool hextob58`

```text
Convert a hexadecimal string to base 58

USAGE: mmgen-tool [OPTS] hextob58 ARG [KEYWORD ARG]

Required ARG (type shown in square brackets):

  hexstr [str] (use '-' to read from STDIN)

Optional KEYWORD ARG (type and default value shown in square brackets):

  pad [int=0] Pad output to this width
```

### `mmgen-tool hextob58chk`

```text
Convert a hexadecimal string to base58-check encoding

USAGE: mmgen-tool [OPTS] hextob58chk ARG

Required ARG (type shown in square brackets):

  hexstr [str] (use '-' to read from STDIN)
```

### `mmgen-tool hextob6d`

```text
Convert a hexadecimal string to die roll base6 (base6d)

USAGE: mmgen-tool [OPTS] hextob6d ARG [KEYWORD ARGS]

Required ARG (type shown in square brackets):

  hexstr [str] (use '-' to read from STDIN)

Optional KEYWORD ARGS (type and default value shown in square brackets):

  pad        [int=0]     Pad output to this width
  add_spaces [bool=True] Add a space after every 5th character
```

### `mmgen-tool id6`

```text
Generate 6-character MMGen ID for a file (use '-' for stdin)

USAGE: mmgen-tool [OPTS] id6 ARG

Required ARG (type shown in square brackets):

  infile [str]
```

### `mmgen-tool id8`

```text
Generate 8-character MMGen ID for a file (use '-' for stdin)

USAGE: mmgen-tool [OPTS] id8 ARG

Required ARG (type shown in square brackets):

  infile [str]
```

### `mmgen-tool randb58`

```text
Generate random data (default: 32 bytes) and convert it to base 58

USAGE: mmgen-tool [OPTS] randb58 [KEYWORD ARGS]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  nbytes [int=32] Number of bytes to output
  pad    [int=0]  Pad output to this width
```

### `mmgen-tool randhex`

```text
Print 'n' bytes (default 32) of random data in hex format

USAGE: mmgen-tool [OPTS] randhex [KEYWORD ARG]

Optional KEYWORD ARG (type and default value shown in square brackets):

  nbytes [int=32] Number of bytes to output
```

### `mmgen-tool str2id6`

```text
Generate 6-character MMGen ID for a string, ignoring spaces in string

USAGE: mmgen-tool [OPTS] str2id6 ARG

Required ARG (type shown in square brackets):

  string [str] (use '-' to read from STDIN)
```

### `mmgen-tool to_bytespec`

```text
Convert an integer to a byte specifier such as ‘4GB’

USAGE: mmgen-tool [OPTS] to_bytespec ARGS [KEYWORD ARGS]

Required ARGS (type shown in square brackets):

  n                       [int]
  dd_style_byte_specifier [str]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  fmt       [str='0.2']  Width and precision of output
  print_sym [bool=True]  Print the specifier after the numerical value
  strip     [bool=False] Strip trailing zeroes
  add_space [bool=False] With print_sym, add space between value and specifier

Supported specifiers:

  c  = 1
  w  = 2
  b  = 512
  kB = 1000
  K  = 1024
  MB = 1000000
  M  = 1048576
  GB = 1000000000
  G  = 1073741824
  TB = 1000000000000
  T  = 1099511627776
  PB = 1000000000000000
  P  = 1125899906842624
  EB = 1000000000000000000
  E  = 1152921504606846976
```

### `mmgen-tool unhexdump`

```text
Decode hexdump from file (use '-' for stdin) (warning: outputs binary data)

USAGE: mmgen-tool [OPTS] unhexdump ARG

Required ARG (type shown in square brackets):

  infile [str]
```

### `mmgen-tool unhexlify`

```text
Convert a hexadecimal string to bytes (warning: outputs binary data)

USAGE: mmgen-tool [OPTS] unhexlify ARG

Required ARG (type shown in square brackets):

  hexstr [str] (use '-' to read from STDIN)
```


## <a id="a_2">Cryptocoin key/address utilities:</a>

### `mmgen-tool addr2pubhash`

```text
Convert coin address to public key hash

USAGE: mmgen-tool [OPTS] addr2pubhash ARG

Required ARG (type shown in square brackets):

  addr [str] (use '-' to read from STDIN)
```

### `mmgen-tool addr2scriptpubkey`

```text
Convert coin address to scriptPubKey

USAGE: mmgen-tool [OPTS] addr2scriptpubkey ARG

Required ARG (type shown in square brackets):

  addr [str] (use '-' to read from STDIN)
```

### `mmgen-tool eth_checksummed_addr`

```text
Create a checksummed Ethereum address

USAGE: mmgen-tool [OPTS] eth_checksummed_addr ARG

Required ARG (type shown in square brackets):

  addr [str] (use '-' to read from STDIN)
```

### `mmgen-tool hex2wif`

```text
Convert a private key from hexadecimal to WIF format

USAGE: mmgen-tool [OPTS] hex2wif ARG

Required ARG (type shown in square brackets):

  privhex [str] (use '-' to read from STDIN)
```

### `mmgen-tool privhex2addr`

```text
Generate a coin address from raw hexadecimal private key data

USAGE: mmgen-tool [OPTS] privhex2addr ARG

Required ARG (type shown in square brackets):

  privhex [str] (use '-' to read from STDIN)
```

### `mmgen-tool privhex2pubhex`

```text
Generate a hexadecimal public key from raw hexadecimal private key data

USAGE: mmgen-tool [OPTS] privhex2pubhex ARG

Required ARG (type shown in square brackets):

  privhex [str] (use '-' to read from STDIN)
```

### `mmgen-tool pubhash2addr`

```text
Convert public key hash to address

USAGE: mmgen-tool [OPTS] pubhash2addr ARG

Required ARG (type shown in square brackets):

  pubhashhex [str] (use '-' to read from STDIN)
```

### `mmgen-tool pubhex2addr`

```text
Convert a hexadecimal pubkey to an address

USAGE: mmgen-tool [OPTS] pubhex2addr ARG

Required ARG (type shown in square brackets):

  pubkeyhex [str] (use '-' to read from STDIN)
```

### `mmgen-tool pubhex2redeem_script`

```text
Convert a hexadecimal pubkey to a Segwit P2SH-P2WPKH redeem script

USAGE: mmgen-tool [OPTS] pubhex2redeem_script ARG

Required ARG (type shown in square brackets):

  pubkeyhex [str] (use '-' to read from STDIN)
```

### `mmgen-tool privhex2pair`

```text
Generate a wifkey/address pair from the provided hexadecimal key

USAGE: mmgen-tool [OPTS] privhex2pair ARG

Required ARG (type shown in square brackets):

  privhex [str] (use '-' to read from STDIN)
```

### `mmgen-tool randpair`

```text
Generate a random wifkey/address pair

USAGE: mmgen-tool [OPTS] randpair
```

### `mmgen-tool randwif`

```text
Generate a random private key in WIF format

USAGE: mmgen-tool [OPTS] randwif
```

### `mmgen-tool redeem_script2addr`

```text
Convert a Segwit P2SH-P2WPKH redeem script to an address

USAGE: mmgen-tool [OPTS] redeem_script2addr ARG

Required ARG (type shown in square brackets):

  redeem_script_hex [str] (use '-' to read from STDIN)
```

### `mmgen-tool scriptpubkey2addr`

```text
Convert scriptPubKey to coin address

USAGE: mmgen-tool [OPTS] scriptpubkey2addr ARG

Required ARG (type shown in square brackets):

  hexstr [str] (use '-' to read from STDIN)
```

### `mmgen-tool wif2addr`

```text
Generate a coin address from a key in WIF format

USAGE: mmgen-tool [OPTS] wif2addr ARG

Required ARG (type shown in square brackets):

  wifkey [str] (use '-' to read from STDIN)
```

### `mmgen-tool wif2hex`

```text
Convert a private key from WIF to hexadecimal format

USAGE: mmgen-tool [OPTS] wif2hex ARG

Required ARG (type shown in square brackets):

  wifkey [str] (use '-' to read from STDIN)
```

### `mmgen-tool wif2redeem_script`

```text
Convert a WIF private key to a Segwit P2SH-P2WPKH redeem script

USAGE: mmgen-tool [OPTS] wif2redeem_script ARG

Required ARG (type shown in square brackets):

  wifkey [str] (use '-' to read from STDIN)
```

### `mmgen-tool wif2segwit_pair`

```text
Generate a Segwit P2SH-P2WPKH redeem script and address from a WIF private key

USAGE: mmgen-tool [OPTS] wif2segwit_pair ARG

Required ARG (type shown in square brackets):

  wifkey [str] (use '-' to read from STDIN)
```


## <a id="a_3">Seed phrase utilities:</a>

### `mmgen-tool hex2mn`

```text
Convert a 16, 24 or 32-byte hexadecimal string to a mnemonic seed phrase

USAGE: mmgen-tool [OPTS] hex2mn ARG [KEYWORD ARG]

Required ARG (type shown in square brackets):

  hexstr [str] (use '-' to read from STDIN)

Optional KEYWORD ARG (type and default value shown in square brackets):

  fmt [str='mmgen'] Seed phrase format (valid choices: 'mmgen','bip39','xmrseed')
```

### `mmgen-tool mn2hex`

```text
Convert a mnemonic seed phrase to a hexadecimal string

USAGE: mmgen-tool [OPTS] mn2hex ARG [KEYWORD ARG]

Required ARG (type shown in square brackets):

  seed_mnemonic [str] (use '-' to read from STDIN)

Optional KEYWORD ARG (type and default value shown in square brackets):

  fmt [str='mmgen'] Seed phrase format (valid choices: 'mmgen','bip39','xmrseed')
```

### `mmgen-tool mn2hex_interactive`

```text
Convert an interactively supplied mnemonic seed phrase to a hexadecimal string

USAGE: mmgen-tool [OPTS] mn2hex_interactive [KEYWORD ARGS]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  fmt      [str='mmgen'] Seed phrase format (valid choices: 'mmgen','bip39','xmrseed')
  mn_len   [int=24]      Length of seed phrase in words
  print_mn [bool=False]  Print the seed phrase after entry
```

### `mmgen-tool mn_printlist`

```text
Print a mnemonic wordlist

USAGE: mmgen-tool [OPTS] mn_printlist [KEYWORD ARGS]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  fmt   [str='mmgen'] Seed phrase format (valid choices: 'mmgen','bip39','xmrseed')
  enum  [bool=False]  Enumerate the list
  pager [bool=False]  Send output to pager
```

### `mmgen-tool mn_rand128`

```text
Generate a random 128-bit mnemonic seed phrase

USAGE: mmgen-tool [OPTS] mn_rand128 [KEYWORD ARG]

Optional KEYWORD ARG (type and default value shown in square brackets):

  fmt [str='mmgen'] Seed phrase format (valid choices: 'mmgen','bip39','xmrseed')
```

### `mmgen-tool mn_rand192`

```text
Generate a random 192-bit mnemonic seed phrase

USAGE: mmgen-tool [OPTS] mn_rand192 [KEYWORD ARG]

Optional KEYWORD ARG (type and default value shown in square brackets):

  fmt [str='mmgen'] Seed phrase format (valid choices: 'mmgen','bip39','xmrseed')
```

### `mmgen-tool mn_rand256`

```text
Generate a random 256-bit mnemonic seed phrase

USAGE: mmgen-tool [OPTS] mn_rand256 [KEYWORD ARG]

Optional KEYWORD ARG (type and default value shown in square brackets):

  fmt [str='mmgen'] Seed phrase format (valid choices: 'mmgen','bip39','xmrseed')
```

### `mmgen-tool mn_stats`

```text
Show stats for a mnemonic wordlist

USAGE: mmgen-tool [OPTS] mn_stats [KEYWORD ARG]

Optional KEYWORD ARG (type and default value shown in square brackets):

  fmt [str='mmgen'] Seed phrase format (valid choices: 'mmgen','bip39','xmrseed')
```


## <a id="a_4">Utilities for viewing/checking MMGen address and transaction files:</a>

### `mmgen-tool addrfile_chksum`

```text
Compute checksum for MMGen address file

USAGE: mmgen-tool [OPTS] addrfile_chksum ARG

Required ARG (type shown in square brackets):

  mmgen_addrfile [str]
```

### `mmgen-tool keyaddrfile_chksum`

```text
Compute checksum for MMGen key-address file

USAGE: mmgen-tool [OPTS] keyaddrfile_chksum ARG

Required ARG (type shown in square brackets):

  mmgen_keyaddrfile [str]
```

### `mmgen-tool viewkeyaddrfile_chksum`

```text
Compute checksum for MMGen key-address file

USAGE: mmgen-tool [OPTS] viewkeyaddrfile_chksum ARG

Required ARG (type shown in square brackets):

  mmgen_viewkeyaddrfile [str]
```

### `mmgen-tool passwdfile_chksum`

```text
Compute checksum for MMGen password file

USAGE: mmgen-tool [OPTS] passwdfile_chksum ARG

Required ARG (type shown in square brackets):

  mmgen_passwdfile [str]
```

### `mmgen-tool txview`

```text
Display specified raw or signed MMGen transaction files in human-readable form

USAGE: mmgen-tool [OPTS] txview ARG [KEYWORD ARGS]

Required ARG (type shown in square brackets):

  mmgen_tx_file(s) [str]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  pager    [bool=False]  Send output to pager
  terse    [bool=False]  Produce compact tabular output
  sort     [str='addr']  Sort order for transaction inputs and outputs (valid choices: 'addr','raw')
  filesort [str='mtime'] File sort order (valid choices: 'mtime','ctime','atime')
```


## <a id="a_5">File encryption and decryption:</a>

### `mmgen-tool decrypt`

```text
Decrypt a file

USAGE: mmgen-tool [OPTS] decrypt ARG [KEYWORD ARGS]

Required ARG (type shown in square brackets):

  infile [str]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  outfile     [str='']
  hash_preset [str='']
```

### `mmgen-tool encrypt`

```text
Encrypt a file

USAGE: mmgen-tool [OPTS] encrypt ARG [KEYWORD ARGS]

Required ARG (type shown in square brackets):

  infile [str]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  outfile     [str='']
  hash_preset [str='']
```


## <a id="a_6">File utilities:</a>

### `mmgen-tool decrypt_keystore`

```text
Decrypt the data in a keystore wallet, returning the decrypted data in binary format

USAGE: mmgen-tool [OPTS] decrypt_keystore ARG [KEYWORD ARG]

Required ARG (type shown in square brackets):

  wallet_file [str]

Optional KEYWORD ARG (type and default value shown in square brackets):

  output_hex [bool=False]
```

### `mmgen-tool decrypt_geth_keystore`

```text
Decrypt the private key in a Geth keystore wallet, returning the decrypted key in hex format

USAGE: mmgen-tool [OPTS] decrypt_geth_keystore ARG [KEYWORD ARG]

Required ARG (type shown in square brackets):

  wallet_file [str]

Optional KEYWORD ARG (type and default value shown in square brackets):

  check_addr [bool=True]
```

### `mmgen-tool find_incog_data`

```text
Use an Incog ID to find hidden incognito wallet data

USAGE: mmgen-tool [OPTS] find_incog_data ARGS [KEYWORD ARG]

Required ARGS (type shown in square brackets):

  filename [str]
  incog_id [str]

Optional KEYWORD ARG (type and default value shown in square brackets):

  keep_searching [bool=False] Continue search after finding data (ID collisions can yield false positives)
```

### `mmgen-tool rand2file`

```text
Write ‘nbytes’ bytes of random data to specified file (dd-style byte specifiers supported)

USAGE: mmgen-tool [OPTS] rand2file ARGS [KEYWORD ARGS]

Required ARGS (type shown in square brackets):

  outfile [str]
  nbytes  [str]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  threads [int=4]
  silent  [bool=False]

Valid specifiers:

  c  = 1
  w  = 2
  b  = 512
  kB = 1000
  K  = 1024
  MB = 1000000
  M  = 1048576
  GB = 1000000000
  G  = 1073741824
  TB = 1000000000000
  T  = 1099511627776
  PB = 1000000000000000
  P  = 1125899906842624
  EB = 1000000000000000000
  E  = 1152921504606846976
```


## <a id="a_7">Key, address or subseed generation from an MMGen wallet:</a>

### `mmgen-tool gen_addr`

```text
Generate a single MMGen address from default or specified wallet

USAGE: mmgen-tool [OPTS] gen_addr ARG [KEYWORD ARG]

Required ARG (type shown in square brackets):

  mmgen_addr [str]

Optional KEYWORD ARG (type and default value shown in square brackets):

  wallet [str='']
```

### `mmgen-tool gen_key`

```text
Generate a single WIF key for specified MMGen address from default or specified wallet

USAGE: mmgen-tool [OPTS] gen_key ARG [KEYWORD ARG]

Required ARG (type shown in square brackets):

  mmgen_addr [str]

Optional KEYWORD ARG (type and default value shown in square brackets):

  wallet [str='']
```

### `mmgen-tool get_subseed`

```text
Get the Seed ID of a single subseed by Subseed Index for default or specified wallet

USAGE: mmgen-tool [OPTS] get_subseed ARG [KEYWORD ARG]

Required ARG (type shown in square brackets):

  subseed_idx [str]

Optional KEYWORD ARG (type and default value shown in square brackets):

  wallet [str='']
```

### `mmgen-tool get_subseed_by_seed_id`

```text
Get the Subseed Index of a single subseed by Seed ID for default or specified wallet

USAGE: mmgen-tool [OPTS] get_subseed_by_seed_id ARG [KEYWORD ARGS]

Required ARG (type shown in square brackets):

  seed_id [str]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  wallet   [str='']
  last_idx [int=100]
```

### `mmgen-tool list_shares`

```text
List the Seed IDs of the shares resulting from a split of default or specified wallet

USAGE: mmgen-tool [OPTS] list_shares ARG [KEYWORD ARGS]

Required ARG (type shown in square brackets):

  share_count [int]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  id_str       [str='default']
  master_share [int=0]         (min:1, max:1024, 0=no master share)
  wallet       [str='']
```

### `mmgen-tool list_subseeds`

```text
List a range of subseed Seed IDs for default or specified wallet

USAGE: mmgen-tool [OPTS] list_subseeds ARG [KEYWORD ARG]

Required ARG (type shown in square brackets):

  subseed_idx_range [str]

Optional KEYWORD ARG (type and default value shown in square brackets):

  wallet [str='']
```


## <a id="a_8">Tracking-wallet commands using the JSON-RPC interface:</a>

### `mmgen-tool add_label`

```text
Add descriptive label for address in tracking wallet

USAGE: mmgen-tool [OPTS] add_label ARGS

Required ARGS (type shown in square brackets):

  mmgen_or_coin_addr [str]
  label              [str]
```

### `mmgen-tool daemon_version`

```text
Print coin daemon version

USAGE: mmgen-tool [OPTS] daemon_version
```

### `mmgen-tool getbalance`

```text
List confirmed/unconfirmed, spendable/unspendable balances in tracking wallet

USAGE: mmgen-tool [OPTS] getbalance [KEYWORD ARGS]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  minconf [int=1]      Minimum number of confirmations
  quiet   [bool=False] Produce quieter output
  pager   [bool=False] Send output to pager
```

### `mmgen-tool listaddress`

```text
List the specified MMGen address in the tracking wallet and its balance

USAGE: mmgen-tool [OPTS] listaddress ARG [KEYWORD ARGS]

Required ARG (type shown in square brackets):

  mmgen_addr [str]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  wide         [bool=False]  Display data in wide tabular format
  minconf      [int=1]       Minimum number of confirmations
  showcoinaddr [bool=True]   Display coin address in addition to MMGen ID
  age_fmt      [str='confs'] Format for the Age/Date column (valid choices: 'confs','block','days','date','date_time')
```

### `mmgen-tool listaddresses`

```text
List MMGen addresses in the tracking wallet and their balances

USAGE: mmgen-tool [OPTS] listaddresses [KEYWORD ARGS]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  pager         [bool=False]  Send output to pager
  reverse       [bool=False]  Reverse order of unspent outputs
  wide          [bool=False]  Display data in wide tabular format
  minconf       [int=1]       Minimum number of confirmations
  sort          [str='']      Address sort order (valid choices: 'reverse','mmid','addr','amt')
  age_fmt       [str='confs'] Format for the Age/Date column (valid choices: 'confs','block','days','date','date_time')
  interactive   [bool=False]  Enable interactive operation
  mmgen_addrs   [str='']      Hyphenated range or comma-separated list of addresses
  showcoinaddrs [bool=True]   Display coin addresses in addition to MMGen IDs
  showempty     [bool=True]   Show addresses with no balances
  showused      [int=1]       Show used addresses (tristate: 0=no, 1=yes, 2=all)
  all_labels    [bool=False]  Show all addresses with labels
```

### `mmgen-tool remove_address`

```text
Remove an address from tracking wallet

USAGE: mmgen-tool [OPTS] remove_address ARG

Required ARG (type shown in square brackets):

  mmgen_or_coin_addr [str]
```

### `mmgen-tool remove_label`

```text
Remove descriptive label for address in tracking wallet

USAGE: mmgen-tool [OPTS] remove_label ARG

Required ARG (type shown in square brackets):

  mmgen_or_coin_addr [str]
```

### `mmgen-tool rescan_address`

```text
Rescan an address in the tracking wallet to update its balance

USAGE: mmgen-tool [OPTS] rescan_address ARG

Required ARG (type shown in square brackets):

  mmgen_or_coin_addr [str]
```

### `mmgen-tool rescan_blockchain`

```text
Rescan the blockchain to update historical transactions in the tracking wallet

USAGE: mmgen-tool [OPTS] rescan_blockchain [KEYWORD ARGS]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  start_block [int=None]
  stop_block  [int=None]

NOTE:

  The rescanning process typically takes several hours and may be interrupted
  using Ctrl-C.  An interrupted rescan may be resumed using the ‘start_block’
  parameter.
```

### `mmgen-tool resolve_address`

```text
Resolve an MMGen address in the tracking wallet to a coin address or vice-versa

USAGE: mmgen-tool [OPTS] resolve_address ARG

Required ARG (type shown in square brackets):

  mmgen_or_coin_addr [str]
```

### `mmgen-tool twexport`

```text
Export a tracking wallet to JSON format

USAGE: mmgen-tool [OPTS] twexport [KEYWORD ARGS]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  include_amts [bool=True]
  pretty       [bool=False]
  prune        [bool=False]
  warn_used    [bool=False]
  force        [bool=False]

NOTES:

  If ‘include_amts’ is true (the default), Ethereum balances will be restored
  from the dump upon import. For Bitcoin and forks, amount fields in the dump
  are ignored.

  If ‘pretty’ is true, JSON will be dumped in human-readable format to allow
  for editing of comment fields.

  If ‘prune’ is true, an interactive menu will be launched allowing the user
  to prune unwanted addresses before creating the JSON dump.  Pruning has no
  effect on the existing tracking wallet.

  If ‘warn_used’ is true, the user will be prompted before pruning used
  addresses.

  If ‘force’ is true, any existing dump will be overwritten without prompting.
```

### `mmgen-tool twimport`

```text
Restore a tracking wallet from a JSON dump created by ‘twexport’

USAGE: mmgen-tool [OPTS] twimport ARG [KEYWORD ARGS]

Required ARG (type shown in square brackets):

  filename [str]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  ignore_checksum [bool=False]
  batch           [bool=False]

NOTES:

  If comment fields in the JSON dump have been edited, ‘ignore_checksum’ must
  be set to true.

  The restored tracking wallet will have correct balances but no record of
  historical transactions.  These may be restored by running ‘mmgen-tool
  rescan_blockchain’.
```

### `mmgen-tool twview`

```text
View tracking wallet unspent outputs

USAGE: mmgen-tool [OPTS] twview [KEYWORD ARGS]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  pager       [bool=False]  Send output to pager
  reverse     [bool=False]  Reverse order of unspent outputs
  wide        [bool=False]  Display data in wide tabular format
  minconf     [int=1]       Minimum number of confirmations
  sort        [str='age']   Unspent output sort order (valid choices: 'addr','age','amt','txid','twmmid')
  age_fmt     [str='confs'] Format for the Age/Date column (valid choices: 'confs','block','days','date','date_time')
  interactive [bool=False]  Enable interactive operation
  show_mmid   [bool=True]   Show MMGen IDs along with coin addresses
```

### `mmgen-tool txhist`

```text
View transaction history of tracking wallet

USAGE: mmgen-tool [OPTS] txhist [KEYWORD ARGS]

Optional KEYWORD ARGS (type and default value shown in square brackets):

  pager       [bool=False]  Send output to pager
  reverse     [bool=False]  Reverse order of transactions
  detail      [bool=False]  Produce detailed, non-tabular output
  sinceblock  [int=0]       Display transactions starting from this block
  sort        [str='age']   Transaction sort order (valid choices: 'age','blockheight','amt','total_amt','txid')
  age_fmt     [str='confs'] Format for the Age/Date column (valid choices: 'confs','block','days','date','date_time')
  interactive [bool=False]  Enable interactive operation
```

```text
MMGEN-WALLET 16.0.0            September 2025             MMGEN-TOOL(DETAIL)(1)
```
