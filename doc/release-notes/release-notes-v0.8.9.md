### MMGen version 0.8.9 Release Notes

This release brings full functionality and wider testing to the MS Windows port.
MMGen now works with both WinXP/MinGW32 and Win7+/MinGW64, and separate, updated
installation instructions for both platforms have been added to the wiki. A
working MinGW environment is now required to run MMGen.

#### New Windows features:

  - Full non-interactive test suite support with pexpect (PopenSpawn)
  - secp256k1 address generation support
  - Secure wallet deletion with sdelete

#### Windows bugfixes:

  - A critical bug in writing the encrypted keyaddrfile has been fixed. This bug
    would have affected only online wallet use and would not have led to the loss
    of coins
  - Cookie filename fixed; RPC cookie authentication now functional

#### General features:

  - --bitcoin-data-dir, --rpc-port, --rpc-user, and --rpc-password options
