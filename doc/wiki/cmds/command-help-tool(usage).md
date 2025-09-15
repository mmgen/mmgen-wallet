```text
GENERAL USAGE INFORMATION FOR MMGEN-TOOL COMMANDS

  Arguments with only type specified in square brackets are required

  Arguments with both type and default value specified in square brackets are
  optional and must be specified in the form ‘name=value’

  For more detailed usage information for a particular tool command, type
  ‘mmgen-tool help <command name>’


  Help/usage commands:

    help  command_name [str='']
    usage command_name [str='']


  General string conversion and hashing utilities:

    b32tohex    b32_str [str or STDIN] pad [int=0]
    b58chktohex b58chk_str [str or STDIN]
    b58tobytes  b58_str [str or STDIN] pad [int=0]
    b58tohex    b58_str [str or STDIN] pad [int=0]
    b6dtohex    b6d_str [str or STDIN] pad [int=0]
    bytespec    dd_style_byte_specifier [str]
    bytestob58  infile [str] pad [int=0]
    hash160     hexstr [str or STDIN]
    hash256     data [str] file_input [bool=False] hex_input [bool=False]
    hexdump     infile [str] cols [int=8] line_nums [str='hex']
    hexlify     infile [str]
    hexreverse  hexstr [str or STDIN]
    hextob32    hexstr [str or STDIN] pad [int=0]
    hextob58    hexstr [str or STDIN] pad [int=0]
    hextob58chk hexstr [str or STDIN]
    hextob6d    hexstr [str or STDIN] pad [int=0] add_spaces [bool=True]
    id6         infile [str]
    id8         infile [str]
    randb58     nbytes [int=32] pad [int=0]
    randhex     nbytes [int=32]
    str2id6     string [str or STDIN]
    to_bytespec n [int] dd_style_byte_specifier [str] fmt [str='0.2'] print_sym [bool=True] strip [bool=False] add_space [bool=False]
    unhexdump   infile [str]
    unhexlify   hexstr [str or STDIN]


  Cryptocoin key/address utilities:

    May require use of the '--coin', '--type' and/or '--testnet' options

    Examples:
      mmgen-tool --coin=ltc --type=bech32 wif2addr <wif key>
      mmgen-tool --coin=zec --type=zcash_z randpair

    addr2pubhash         addr [str or STDIN]
    addr2scriptpubkey    addr [str or STDIN]
    eth_checksummed_addr addr [str or STDIN]
    hex2wif              privhex [str or STDIN]
    privhex2addr         privhex [str or STDIN]
    privhex2pubhex       privhex [str or STDIN]
    pubhash2addr         pubhashhex [str or STDIN]
    pubhex2addr          pubkeyhex [str or STDIN]
    pubhex2redeem_script pubkeyhex [str or STDIN]
    privhex2pair         privhex [str or STDIN]
    randpair
    randwif
    redeem_script2addr   redeem_script_hex [str or STDIN]
    scriptpubkey2addr    hexstr [str or STDIN]
    wif2addr             wifkey [str or STDIN]
    wif2hex              wifkey [str or STDIN]
    wif2redeem_script    wifkey [str or STDIN]
    wif2segwit_pair      wifkey [str or STDIN]


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

    hex2mn             hexstr [str or STDIN] fmt [str='mmgen']
    mn2hex             seed_mnemonic [str or STDIN] fmt [str='mmgen']
    mn2hex_interactive fmt [str='mmgen'] mn_len [int=24] print_mn [bool=False]
    mn_printlist       fmt [str='mmgen'] enum [bool=False] pager [bool=False]
    mn_rand128         fmt [str='mmgen']
    mn_rand192         fmt [str='mmgen']
    mn_rand256         fmt [str='mmgen']
    mn_stats           fmt [str='mmgen']


  Utilities for viewing/checking MMGen address and transaction files:

    addrfile_chksum        mmgen_addrfile [str]
    keyaddrfile_chksum     mmgen_keyaddrfile [str]
    viewkeyaddrfile_chksum mmgen_viewkeyaddrfile [str]
    passwdfile_chksum      mmgen_passwdfile [str]
    txview                 mmgen_tx_file(s) [str] pager [bool=False] terse [bool=False] sort [str='addr'] filesort [str='mtime']


  File encryption and decryption:

    MMGen encryption suite:
    * Key: Scrypt (user-configurable hash parameters, 32-byte salt)
    * Enc: AES256_CTR, 16-byte rand IV, sha256 hash + 32-byte nonce + data
    * The encrypted file is indistinguishable from random data

    decrypt infile [str] outfile [str=''] hash_preset [str='']
    encrypt infile [str] outfile [str=''] hash_preset [str='']


  File utilities:

    decrypt_keystore      wallet_file [str] output_hex [bool=False]
    decrypt_geth_keystore wallet_file [str] check_addr [bool=True]
    find_incog_data       filename [str] incog_id [str] keep_searching [bool=False]
    rand2file             outfile [str] nbytes [str] threads [int=4] silent [bool=False]


  Key, address or subseed generation from an MMGen wallet:

    gen_addr               mmgen_addr [str] wallet [str='']
    gen_key                mmgen_addr [str] wallet [str='']
    get_subseed            subseed_idx [str] wallet [str='']
    get_subseed_by_seed_id seed_id [str] wallet [str=''] last_idx [int=100]
    list_shares            share_count [int] id_str [str='default'] master_share [int=0] wallet [str='']
    list_subseeds          subseed_idx_range [str] wallet [str='']


  Tracking-wallet commands using the JSON-RPC interface:

    add_label         mmgen_or_coin_addr [str] label [str]
    daemon_version
    getbalance        minconf [int=1] quiet [bool=False] pager [bool=False]
    listaddress       mmgen_addr [str] wide [bool=False] minconf [int=1] showcoinaddr [bool=True] age_fmt [str='confs']
    listaddresses     pager [bool=False] reverse [bool=False] wide [bool=False] minconf [int=1] sort [str=''] age_fmt [str='confs'] interactive [bool=False] mmgen_addrs [str=''] showcoinaddrs [bool=True] showempty [bool=True] showused [int=1] all_labels [bool=False]
    remove_address    mmgen_or_coin_addr [str]
    remove_label      mmgen_or_coin_addr [str]
    rescan_address    mmgen_or_coin_addr [str]
    rescan_blockchain start_block [int=None] stop_block [int=None]
    resolve_address   mmgen_or_coin_addr [str]
    twexport          include_amts [bool=True] pretty [bool=False] prune [bool=False] warn_used [bool=False] force [bool=False]
    twimport          filename [str] ignore_checksum [bool=False] batch [bool=False]
    twview            pager [bool=False] reverse [bool=False] wide [bool=False] minconf [int=1] sort [str='age'] age_fmt [str='confs'] interactive [bool=False] show_mmid [bool=True]
    txhist            pager [bool=False] reverse [bool=False] detail [bool=False] sinceblock [int=0] sort [str='age'] age_fmt [str='confs'] interactive [bool=False]


  To force a command to read from STDIN instead of file (for commands taking
  a filename as their first argument), substitute "-" for the filename.


EXAMPLES:

  Generate a random LTC Bech32 public/private keypair:
  $ mmgen-tool -r0 --coin=ltc --type=bech32 randpair

  Generate a DASH address with compressed public key from the supplied WIF key:
  $ mmgen-tool --coin=dash --type=compressed wif2addr XJkVRC3eGKurc9Uzx1wfQoio3yqkmaXVqLMTa6y7s3M3jTBnmxfw

  Generate a well-known burn address:
  $ mmgen-tool hextob58chk 000000000000000000000000000000000000000000

  Generate a random 12-word seed phrase:
  $ mmgen-tool -r0 mn_rand128 fmt=bip39

  Same as above, but get additional entropy from user:
  $ mmgen-tool mn_rand128 fmt=bip39

  Encode bytes from a file to base 58:
  $ mmgen-tool bytestob58 /etc/timezone pad=20

  Reverse a hex string:
  $ mmgen-tool hexreverse "deadbeefcafe"

  Same as above, but supply input via STDIN:
  $ echo "deadbeefcafe" | mmgen-tool hexreverse -

  MMGEN-WALLET 16.0.0            September 2025           MMGEN-TOOL(USAGE)(1)
```
