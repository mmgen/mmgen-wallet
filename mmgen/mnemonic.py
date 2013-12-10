#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C) 2013 by philemon <mmgen-py@yandex.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
mnemonic.py:  Mnemomic routines for the mmgen suite
"""

wl_checksums = {
	"electrum": '5ca31424',
	"tirosh":   '1a5faeff'
}

# These are the only base-1626 specific configs:
mn_base = 1626
def mn_fill(mn):    return len(mn) * 8 / 3
def mn_len(hexnum): return len(hexnum) * 3 / 8

import sys

from mmgen.utils import msg,make_chksum_8
from mmgen.config import *

# These universal base-conversion routines work for any base

def baseNtohex(base,words,wordlist,fill=0):
	deconv = \
		[wordlist.index(words[::-1][i])*(base**i) for i in range(len(words))]
	return hex(sum(deconv))[2:].rstrip('L').zfill(fill)

def hextobaseN(base,hexnum,wordlist,mn_len):
	num = int(hexnum,16)
	return [wordlist[num / (base**i) % base] for i in range(mn_len)][::-1]

def get_seed_from_mnemonic(mn,wl):

	if len(mn) not in mnemonic_lens:
		msg("Bad mnemonic (%i words).  Allowed numbers of words: %s" %
				(len(mn)," ".join([str(i) for i in mnemonic_lens])))
		sys.exit(2)

	for w in mn:
		if w not in wl:
			msg("Bad mnemonic: '%s' is not in the wordlist" % w)
			sys.exit(2)

	from binascii import unhexlify
	seed = unhexlify(baseNtohex(mn_base,mn,wl,mn_fill(mn)))
	msg("Valid mnemomic for seed ID %s" % make_chksum_8(seed))

	return seed


def get_mnemonic_from_seed(seed, wl, label, print_info=False):

	from binascii import hexlify

	if print_info:
		msg("Wordlist:    %s" % label.capitalize())
		msg("Seed length: %s bits" % (len(seed) * 8))
		msg("Seed:        %s" % hexlify(seed))

	hseed = hexlify(seed)
	mn = hextobaseN(mn_base,hseed,wl,mn_len(hseed))

	if print_info:
		msg("mnemonic (%s words):\n%s" % (len(mn), " ".join(mn)))

	if int(baseNtohex(mn_base,mn,wl,mn_fill(mn)),16) != int(hexlify(seed),16):
		msg("ERROR: seed recomputed from wordlist not the same as original seed!")
		msg("Recomputed seed %s" % baseNtohex(mn_base,mn,wl,mn_fill(mn)))
		sys.exit(3)

	return mn


def check_wordlist(wl_str,label):

	wl = wl_str.strip().split("\n")

	print "Wordlist: %s" % label.capitalize()

	from hashlib import sha256

	print "Length:   %i" % len(wl)
	new_chksum = sha256(" ".join(wl)).hexdigest()[:8]

	if new_chksum != wl_checksums[label]:
		print "ERROR: Checksum mismatch.  Computed: %s, Saved: %s" % \
			(new_chksum,wl_checksums[label])
		sys.exit(3)

	print "Checksum: %s (matches)" % new_chksum

	if (sorted(wl) == wl):
		print "List is sorted"
	else:
		print "ERROR: List is not sorted!"
		sys.exit(3)
