#!/usr/bin/env python3
#
# MMGen Wallet, a terminal-based cryptocurrency wallet
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
help.seedsplit: seedsplit help notes for MMGen suite
"""

def help(proto, cfg):
	from ..seedsplit import SeedShareIdx, SeedShareCount, MasterShareIdx
	return """
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
{si.min_val}-{si.max_val} and the share count (the total number of shares in the split)
in the range {sc.min_val}-{sc.max_val}.

Master Shares

Each seed has a total of {mi.max_val} master shares, which can be used as the first
shares in multiple splits if desired.  To generate a master share, use the
--master-share (-M) option with an index in the range {mi.min_val}-{mi.max_val} and omit
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

    $ mmgen-seedjoin -o bip39 \\
        '03BAE887-default-2of2[67BFD36E][128].bip39' \\
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

""".strip().format(
	si = SeedShareIdx,
	sc = SeedShareCount,
	mi = MasterShareIdx)
