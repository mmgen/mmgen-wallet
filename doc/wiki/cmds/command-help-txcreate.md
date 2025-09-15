```text
  MMGEN-TXCREATE: Create a transaction with outputs to specified coin or MMGen addresses
  USAGE:          mmgen-txcreate [opts] [ADDR,AMT ... | DATA_SPEC] ADDR [addr file ...]
  OPTIONS:
  -h, --help            Print this help message
      --longhelp        Print help message for long (global) options
  -a, --autosign        Create a transaction for offline autosigning (see
                        ‘mmgen-autosign’). The removable device is mounted and
                        unmounted automatically
  -A, --fee-adjust   f  Adjust transaction fee by factor ‘f’ (see below)
  -B, --no-blank        Don't blank screen before displaying unspent outputs
  -c, --comment-file f  Source the transaction's comment from file 'f'
  -C, --fee-estimate-confs c Desired number of confirmations for fee estimation
                        (default: 3)
  -d, --outdir       d  Specify an alternate directory 'd' for output
  -E, --fee-estimate-mode M Specify the network fee estimate mode.  Choices:
                        'conservative','economical'.  Default: 'conservative'
  -f, --fee          f  Transaction fee, as a decimal BTC amount or as
                        satoshis per byte (an integer followed by ‘s’).
                        See FEE SPECIFICATION below.  If omitted, fee will be
                        calculated using network fee estimation.
  -i, --info            Display unspent outputs and exit
  -I, --inputs       i  Specify transaction inputs (comma-separated list of
                        MMGen IDs or coin addresses).  Note that ALL unspent
                        outputs associated with each address will be included.
  -l, --locktime     t  Lock time (block height or unix seconds) (default: 0)
  -L, --autochg-ignore-labels Ignore labels when autoselecting change addresses
  -m, --minconf      n  Minimum number of confirmations required to spend
                        outputs (default: 1)
  -q, --quiet           Suppress warnings; overwrite files without prompting
  -R, --no-rbf          Make transaction non-replaceable (non-replace-by-fee
                        according to BIP 125)
  -v, --verbose         Produce more verbose output
  -V, --vsize-adj    f  Adjust transaction's estimated vsize by factor 'f'
  -y, --yes             Answer 'yes' to prompts, suppress non-essential output


  The transaction’s outputs are listed on the command line, while its inputs
  are chosen from a list of the wallet’s unspent outputs via an interactive
  menu.  Alternatively, inputs may be specified using the --inputs option.

  Addresses on the command line can be either native coin addresses or MMGen
  IDs in the form SEED_ID:ADDRTYPE_CODE:INDEX.

  Outputs are specified in the form ADDRESS,AMOUNT or ADDRESS.  The first form
  creates an output sending the given amount to the given address.  The bare
  address form designates the given address as either the change output or the
  sole output of the transaction (excluding any data output).  Exactly one bare
  address argument is required.

  For convenience, the bare address argument may be given as ADDRTYPE_CODE or
  SEED_ID:ADDRTYPE_CODE (see ADDRESS TYPES below). In the first form, the first
  unused address of type ADDRTYPE_CODE for each Seed ID in the tracking wallet
  will be displayed in a menu, with the user prompted to select one.  In the
  second form, the user specifies the Seed ID as well, allowing the script to
  select the transaction’s change output or single output without prompting.
  See EXAMPLES below.

  A single DATA_SPEC argument may also be given on the command line to create
  an OP_RETURN data output with a zero spend amount.  This is the preferred way
  to embed data in the blockchain.  DATA_SPEC may be of the form "data":DATA
  or "hexdata":DATA. In the first form, DATA is a string in your system’s native
  encoding, typically UTF-8.  In the second, DATA is a hexadecimal string (with
  the leading ‘0x’ omitted) encoding the binary data to be embedded.  In both
  cases, the resulting byte string must not exceed 80 bytes in length.

  If the transaction fee is not specified on the command line (see FEE
  SPECIFICATION below), it will be calculated dynamically using network fee
  estimation for the default (or user-specified) number of confirmations.
  If network fee estimation fails, the user will be prompted for a fee.

  Network-estimated fees will be multiplied by the value of --fee-adjust, if
  specified.


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


                                 FEE SPECIFICATION

  Transaction fees, both on the command line and at the interactive prompt, may
  be specified as either absolute coin amounts, using a plain decimal number, or
  as satoshis per byte, using an integer followed by ‘s’, for satoshi.


  EXAMPLES:

    Send 0.123 BTC to an external Bitcoin address, returning the change to a
    specific MMGen address in the tracking wallet:

      $ mmgen-txcreate bc1qj87nveegsvwmz8yj759xgua2vx2tzsywlny44t,0.123 01ABCDEF:B:7

    Same as above, but select the change address automatically:

      $ mmgen-txcreate bc1qj87nveegsvwmz8yj759xgua2vx2tzsywlny44t,0.123 01ABCDEF:B

    Same as above, but select the change address automatically by address type:

      $ mmgen-txcreate bc1qj87nveegsvwmz8yj759xgua2vx2tzsywlny44t,0.123 B

    Same as above, but reduce verbosity and specify fee of 20 satoshis
    per byte:

      $ mmgen-txcreate -q -f 20s bc1qj87nveegsvwmz8yj759xgua2vx2tzsywlny44t,0.123 B

    Send entire balance of selected inputs minus fee to an external Bitcoin
    address:

      $ mmgen-txcreate bc1qj87nveegsvwmz8yj759xgua2vx2tzsywlny44t

    Send entire balance of selected inputs minus fee to first unused wallet
    address of specified type:

      $ mmgen-txcreate B

  MMGEN-WALLET 16.0.0            September 2025              MMGEN-TXCREATE(1)
```
