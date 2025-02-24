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
help.subwallet: subwallet help notes for the MMGen Wallet suite
"""

def help(proto, cfg):
	from ..subseed import SubSeedIdxRange
	return f"""
SUBWALLETS:

Subwallets (subseeds) are specified by a ‘Subseed Index’ consisting of:

  a) an integer in the range 1-{SubSeedIdxRange.max_idx}, plus
  b) an optional single letter, ‘L’ or ‘S’

The letter designates the length of the subseed.  If omitted, ‘L’ is assumed.

Long (‘L’) subseeds are the same length as their parent wallet’s seed
(typically 256 bits), while short (‘S’) subseeds are always 128-bit.
The long and short subseeds for a given index are derived independently,
so both may be used.

MMGen Wallet has no notion of ‘depth’, and to an outside observer subwallets
are identical to ordinary wallets.  This is a feature rather than a bug, as
it denies an attacker any way of knowing whether a given wallet has a parent.

Since subwallets are just wallets, they may be used to generate other
subwallets, leading to hierarchies of arbitrary depth.  However, this is
inadvisable in practice for two reasons:  Firstly, it creates accounting
complexity, requiring the user to independently keep track of a derivation
tree.  More importantly, however, it leads to the danger of Seed ID
collisions between subseeds at different levels of the hierarchy, as
MMGen checks and avoids ID collisions only among sibling subseeds.

An exception to this caveat would be a multi-user setup where sibling
subwallets are distributed to different users as their default wallets.
Since the subseeds derived from these subwallets are private to each user,
Seed ID collisions among them doesn’t present a problem.

A safe rule of thumb, therefore, is for *each user* to derive all of his/her
subwallets from a single parent.  This leaves each user with a total of two
million subwallets, which should be enough for most practical purposes.
""".strip()
