```text
  MMGEN-TOOL: Perform various MMGen- and cryptocoin-related operations
  USAGE:      mmgen-tool [opts] <command> <command args>
  OPTIONS:
  -d, --outdir        d  Specify an alternate directory 'd' for output
  -h, --help             Print this help message
      --longhelp         Print help message for long (global) options
  -e, --echo-passphrase  Echo passphrase or mnemonic to screen upon entry
  -k, --use-internal-keccak-module Force use of the internal keccak module
  -K, --keygen-backend n Use backend 'n' for public key generation.  Options
                         for BTC: 1:libsecp256k1 [default] 2:python-ecdsa
  -l, --list             List available commands
  -p, --hash-preset  p   Use the scrypt hash parameters defined by preset 'p'
                         for password hashing (default: '3')
  -P, --passwd-file  f   Get passphrase from file 'f'.
  -q, --quiet            Produce quieter output
  -r, --usr-randchars n  Get 'n' characters of additional randomness from
                         user (min=10, max=80)
  -t, --type t           Specify address type (valid choices: 'legacy',
                         'compressed', 'segwit', 'bech32', 'zcash_z')
  -v, --verbose          Produce more verbose output
  -x, --proxy P          Proxy HTTP connections via SOCKS5h proxy ‘P’ (host:port).
                         Use special value ‘env’ to honor *_PROXY environment
                         vars instead.
  -y, --yes              Answer 'yes' to prompts, suppress non-essential output


                                 COMMANDS

  Help/usage commands:

    help  - display usage information for a single command or all commands
    usage - display usage information for a single command or all commands

  General string conversion and hashing utilities:

    b32tohex    - convert an MMGen-flavor base 32 string to hexadecimal
    b58chktohex - convert a base58-check encoded string to hexadecimal
    b58tobytes  - convert a base 58 string to bytes (warning: outputs binary
                  data)
    b58tohex    - convert a base 58 string to hexadecimal
    b6dtohex    - convert a die roll base6 (base6d) string to hexadecimal
    bytespec    - convert a byte specifier such as ‘4GB’ into an integer
    bytestob58  - convert bytes to base 58 (supply data via STDIN)
    hash160     - compute ripemd160(sha256(data)) (convert hex pubkey to hex
                  addr)
    hash256     - compute sha256(sha256(data)) (double sha256)
    hexdump     - create hexdump of data from file (use '-' for stdin)
    hexlify     - convert bytes in file to hexadecimal (use '-' for stdin)
    hexreverse  - reverse bytes of a hexadecimal string
    hextob32    - convert a hexadecimal string to an MMGen-flavor base 32
                  string
    hextob58    - convert a hexadecimal string to base 58
    hextob58chk - convert a hexadecimal string to base58-check encoding
    hextob6d    - convert a hexadecimal string to die roll base6 (base6d)
    id6         - generate 6-character MMGen ID for a file (use '-' for stdin)
    id8         - generate 8-character MMGen ID for a file (use '-' for stdin)
    randb58     - generate random data (default: 32 bytes) and convert it to
                  base 58
    randhex     - print 'n' bytes (default 32) of random data in hex format
    str2id6     - generate 6-character MMGen ID for a string, ignoring spaces
                  in string
    to_bytespec - convert an integer to a byte specifier such as ‘4GB’
    unhexdump   - decode hexdump from file (use '-' for stdin) (warning:
                  outputs binary data)
    unhexlify   - convert a hexadecimal string to bytes (warning: outputs
                  binary data)

  Cryptocoin key/address utilities:

    May require use of the '--coin', '--type' and/or '--testnet' options

    Examples:
      mmgen-tool --coin=ltc --type=bech32 wif2addr <wif key>
      mmgen-tool --coin=zec --type=zcash_z randpair

    addr2pubhash         - convert coin address to public key hash
    addr2scriptpubkey    - convert coin address to scriptPubKey
    eth_checksummed_addr - create a checksummed Ethereum address
    hex2wif              - convert a private key from hexadecimal to WIF format
    privhex2addr         - generate a coin address from raw hexadecimal
                           private key data
    privhex2pubhex       - generate a hexadecimal public key from raw
                           hexadecimal private key data
    pubhash2addr         - convert public key hash to address
    pubhex2addr          - convert a hexadecimal pubkey to an address
    pubhex2redeem_script - convert a hexadecimal pubkey to a Segwit
                           P2SH-P2WPKH redeem script
    privhex2pair         - generate a wifkey/address pair from the provided
                           hexadecimal key
    randpair             - generate a random wifkey/address pair
    randwif              - generate a random private key in WIF format
    redeem_script2addr   - convert a Segwit P2SH-P2WPKH redeem script to an
                           address
    scriptpubkey2addr    - convert scriptPubKey to coin address
    wif2addr             - generate a coin address from a key in WIF format
    wif2hex              - convert a private key from WIF to hexadecimal format
    wif2redeem_script    - convert a WIF private key to a Segwit P2SH-P2WPKH
                           redeem script
    wif2segwit_pair      - generate a Segwit P2SH-P2WPKH redeem script and
                           address from a WIF private key

  Seed phrase utilities:

    Supported seed phrase formats: 'mmgen' (default), 'bip39', 'xmrseed'

    IMPORTANT NOTE: MMGen Wallet’s default seed phrase format uses the
    Electrum wordlist, however seed phrases are computed using a different
    algorithm and are NOT Electrum-compatible!

    BIP39 support is fully compatible with the standard, allowing users to
    import and export seed entropy from BIP39-compatible wallets.  However,
    users should be aware that BIP39 support does not imply BIP32 support!
    MMGen uses its own key derivation scheme differing from the one described
    by the BIP32 protocol.

    For Monero (‘xmrseed’) seed phrases, input data is reduced to a spendkey
    before conversion so that a canonical seed phrase is produced.  This is
    required because Monero seeds, unlike ordinary wallet seeds, are tied
    to a concrete key/address pair.  To manually generate a Monero spendkey,
    use the ‘hex2wif’ command.

    hex2mn             - convert a 16, 24 or 32-byte hexadecimal string to a
                         mnemonic seed phrase
    mn2hex             - convert a mnemonic seed phrase to a hexadecimal string
    mn2hex_interactive - convert an interactively supplied mnemonic seed
                         phrase to a hexadecimal string
    mn_printlist       - print a mnemonic wordlist
    mn_rand128         - generate a random 128-bit mnemonic seed phrase
    mn_rand192         - generate a random 192-bit mnemonic seed phrase
    mn_rand256         - generate a random 256-bit mnemonic seed phrase
    mn_stats           - show stats for a mnemonic wordlist

  Utilities for viewing/checking MMGen address and transaction files:

    addrfile_chksum        - compute checksum for MMGen address file
    keyaddrfile_chksum     - compute checksum for MMGen key-address file
    viewkeyaddrfile_chksum - compute checksum for MMGen key-address file
    passwdfile_chksum      - compute checksum for MMGen password file
    txview                 - display specified raw or signed MMGen transaction
                             files in human-readable form

  File encryption and decryption:

    MMGen encryption suite:
    * Key: Scrypt (user-configurable hash parameters, 32-byte salt)
    * Enc: AES256_CTR, 16-byte rand IV, sha256 hash + 32-byte nonce + data
    * The encrypted file is indistinguishable from random data

    decrypt - decrypt a file
    encrypt - encrypt a file

  File utilities:

    decrypt_keystore      - decrypt the data in a keystore wallet, returning
                            the decrypted data in binary format
    decrypt_geth_keystore - decrypt the private key in a Geth keystore wallet,
                            returning the decrypted key in hex format
    find_incog_data       - Use an Incog ID to find hidden incognito wallet
                            data
    rand2file             - write ‘nbytes’ bytes of random data to specified
                            file (dd-style byte specifiers supported)

  Key, address or subseed generation from an MMGen wallet:

    gen_addr               - generate a single MMGen address from default or
                             specified wallet
    gen_key                - generate a single WIF key for specified MMGen
                             address from default or specified wallet
    get_subseed            - get the Seed ID of a single subseed by Subseed
                             Index for default or specified wallet
    get_subseed_by_seed_id - get the Subseed Index of a single subseed by Seed
                             ID for default or specified wallet
    list_shares            - list the Seed IDs of the shares resulting from a
                             split of default or specified wallet
    list_subseeds          - list a range of subseed Seed IDs for default or
                             specified wallet

  Tracking-wallet commands using the JSON-RPC interface:

    add_label         - add descriptive label for address in tracking wallet
    daemon_version    - print coin daemon version
    getbalance        - list confirmed/unconfirmed, spendable/unspendable
                        balances in tracking wallet
    listaddress       - list the specified MMGen address in the tracking
                        wallet and its balance
    listaddresses     - list MMGen addresses in the tracking wallet and their
                        balances
    remove_address    - remove an address from tracking wallet
    remove_label      - remove descriptive label for address in tracking wallet
    rescan_address    - rescan an address in the tracking wallet to update its
                        balance
    rescan_blockchain - rescan the blockchain to update historical
                        transactions in the tracking wallet
    resolve_address   - resolve an MMGen address in the tracking wallet to a
                        coin address or vice-versa
    twexport          - export a tracking wallet to JSON format
    twimport          - restore a tracking wallet from a JSON dump created by
                        ‘twexport’
    twview            - view tracking wallet unspent outputs
    txhist            - view transaction history of tracking wallet

  Type ‘mmgen-tool help <command>’ for help on a particular command

  MMGEN-WALLET 16.0.0            September 2025                  MMGEN-TOOL(1)
```
