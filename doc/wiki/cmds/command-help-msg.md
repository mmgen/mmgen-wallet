```text
  MMGEN-MSG: Perform message signing operations for MMGen addresses
  USAGE:     mmgen-msg [opts] create MESSAGE_TEXT ADDRESS_SPEC [...]
             mmgen-msg [opts] sign   MESSAGE_FILE [WALLET_FILE ...]
             mmgen-msg [opts] verify MESSAGE_FILE [MMGen ID]
             mmgen-msg [opts] verify <exported JSON dump file> [address]
             mmgen-msg [opts] export MESSAGE_FILE [MMGen ID]
  OPTIONS:
  -h, --help           Print this help message
      --longhelp       Print help message for long (global) options
  -d, --outdir d       Output file to directory 'd' instead of working dir
  -t, --msghash-type T Specify the message hash type.  Supported values:
                       'eth_sign' (ETH default), 'raw' (non-ETH default)
  -q, --quiet          Produce quieter output


                               SUPPORTED OPERATIONS

  create - create a raw MMGen message file with specified message text for
           signing for addresses specified by ADDRESS_SPEC (see ADDRESS
           SPECIFIER below)
  sign   - perform signing operation on an unsigned MMGen message file
  verify - verify and display the contents of a signed MMGen message file
  export - dump signed MMGen message file to ‘signatures.json’, including only
           data relevant for a third-party verifier


                                ADDRESS SPECIFIER

  The `create` operation takes one or more ADDRESS_SPEC arguments with the
  following format:

      SEED_ID:ADDRTYPE_CODE:ADDR_IDX_SPEC

  where ADDRTYPE_CODE is a one-letter address type code from the list below, and
  ADDR_IDX_SPEC is a comma-separated list of address indexes or hyphen-separated
  address index ranges.


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


                                      NOTES

  Message signing operations are supported for Bitcoin, Ethereum and code forks
  thereof.

  By default, Ethereum messages are prefixed before hashing in conformity with
  the standard defined by the Geth ‘eth_sign’ JSON-RPC call.  This behavior may
  be overridden with the --msghash-type option.

  Messages signed for Segwit-P2SH addresses cannot be verified directly using
  the Bitcoin Core `verifymessage` RPC call, since such addresses are not hashes
  of public keys.  As a workaround for this limitation, this utility creates for
  each Segwit-P2SH address a non-Segwit address with the same public key to be
  used for verification purposes.  This non-Segwit verifying address should then
  be passed on to the verifying party together with the signature. The verifying
  party may then use a tool of their choice (e.g. `mmgen-tool addr2pubhash`) to
  assure themselves that the verifying address and Segwit address share the same
  public key.

  Unfortunately, the aforementioned limitation applies to Segwit-P2PKH (Bech32)
  addresses as well, despite the fact that Bech32 addresses are hashes of public
  keys (we consider this an implementation shortcoming of `verifymessage`).
  Therefore, the above procedure must be followed to verify messages for Bech32
  addresses too.  `mmgen-tool addr2pubhash` or `bitcoin-cli validateaddress`
  may then be used to demonstrate that the two addresses share the same public
  key.


                                     EXAMPLES

  Create a raw message file for the specified message and specified addresses,
  where DEADBEEF is the Seed ID of the user’s default wallet and BEEFCAFE one
  of its subwallets:
  $ mmgen-msg create '16/3/2022 Earthquake strikes Fukushima coast' DEADBEEF:B:1-3,10,98 BEEFCAFE:S:3,9

  Sign the raw message file created by the previous step:
  $ mmgen-msg sign <raw message file>

  Sign the raw message file using an explicitly supplied wallet:
  $ mmgen-msg sign <raw message file> DEADBEEF.bip39

  Verify and display all signatures in the signed message file:
  $ mmgen-msg verify <signed message file>

  Verify and display a single signature in the signed message file:
  $ mmgen-msg verify <signed message file> DEADBEEF:B:98

  Export data relevant for a third-party verifier to ‘signatures.json’:
  $ mmgen-msg export <signed message file>

  Same as above, but export only one signature:
  $ mmgen-msg export <signed message file> DEADBEEF:B:98

  Verify and display the exported JSON signature data:
  $ mmgen-msg verify signatures.json

  MMGEN-WALLET 16.0.0            September 2025                   MMGEN-MSG(1)
```
