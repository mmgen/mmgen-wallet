#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2015 Philemon <mmgen-py@yandex.com>
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
mnemonic.py:  Mnemonic routines for the MMGen suite
"""

import sys
from binascii import hexlify
from mmgen.util import msg,msg_r,make_chksum_8,Vmsg,Msg
from mmgen.crypto import get_random
import mmgen.globalvars as g
import mmgen.opt as opt

wl_checksums = {
	"electrum": '5ca31424',
	"tirosh":   '1a5faeff'
}

# These are the only base-1626 specific configs:
mn_base = 1626
def mn2hex_pad(mn):     return len(mn) * 8 / 3
def hex2mn_pad(hexnum): return len(hexnum) * 3 / 8

# Universal base-conversion routines:
def baseNtohex(base,words,wordlist,pad=0):
	deconv = \
		[wordlist.index(words[::-1][i])*(base**i) for i in range(len(words))]
	ret = ("{:0%sx}" % pad).format(sum(deconv))
	return "%s%s" % (('0' if len(ret) % 2 else ''), ret)

def hextobaseN(base,hexnum,wordlist,pad=0):
	num,ret = int(hexnum,16),[]
	while num:
		ret.append(num % base)
		num /= base
	return [wordlist[n] for n in [0] * (pad-len(ret)) + ret[::-1]]

def get_seed_from_mnemonic(mn,wl,silent=False,label=""):

	if len(mn) not in g.mn_lens:
		msg("Invalid mnemonic (%i words).  Allowed numbers of words: %s" %
				(len(mn),", ".join([str(i) for i in g.mn_lens])))
		sys.exit(3)

	for n,w in enumerate(mn,1):
		if w not in wl:
			msg("Invalid mnemonic: word #%s is not in the wordlist" % n)
			sys.exit(3)

	from binascii import unhexlify
	hseed = baseNtohex(mn_base,mn,wl,mn2hex_pad(mn))

	rev = hextobaseN(mn_base,hseed,wl,hex2mn_pad(hseed))
	if rev != mn:
		msg("ERROR: mnemonic recomputed from seed not the same as original")
		msg("Recomputed mnemonic:\n%s" % " ".join(rev))
		sys.exit(3)

	if not silent:
		msg("Valid mnemonic for seed ID %s" % make_chksum_8(unhexlify(hseed)))

	return unhexlify(hseed)


def get_mnemonic_from_seed(seed, wl, label="", verbose=False):

	if len(seed)*8 not in g.seed_lens:
		msg("%s: invalid seed length" % len(seed))
		sys.exit(3)

	from binascii import hexlify

	hseed = hexlify(seed)
	mn = hextobaseN(mn_base,hseed,wl,hex2mn_pad(hseed))

	if verbose:
		msg("Wordlist:    %s"          % label.capitalize())
		msg("Seed length: %s bits"     % (len(seed) * 8))
		msg("Seed:        %s"          % hseed)
		msg("mnemonic (%s words):\n%s" % (len(mn), " ".join(mn)))

	rev = baseNtohex(mn_base,mn,wl,mn2hex_pad(mn))
	if rev != hseed:
		msg("ERROR: seed recomputed from wordlist not the same as original seed!")
		msg("Original seed:   %s" % hseed)
		msg("Recomputed seed: %s" % rev)
		sys.exit(3)

	return mn


def check_wordlist(wl,label):

	Msg("Wordlist: %s" % label.capitalize())

	from hashlib import sha256

	Msg("Length:   %i words" % len(wl))
	new_chksum = sha256(" ".join(wl)).hexdigest()[:8]

	if new_chksum != wl_checksums[label]:
		Msg("ERROR: Checksum mismatch.  Computed: %s, Saved: %s" % \
			(new_chksum,wl_checksums[label]))
		sys.exit(3)

	Msg("Checksum: %s (matches)" % new_chksum)

	if (sorted(wl) == wl):
		Msg("List is sorted")
	else:
		Msg("ERROR: List is not sorted!")
		sys.exit(3)

from mmgen.mn_electrum  import words as el
from mmgen.mn_tirosh    import words as tl
wordlists = sorted(wl_checksums)

def get_wordlist(wordlist):
	wordlist = wordlist.lower()
	if wordlist not in wordlists:
		Msg('"%s": invalid wordlist.  Valid choices: %s' %
			(wordlist,'"'+'" "'.join(wordlists)+'"'))
		sys.exit(1)
	return (el if wordlist == "electrum" else tl).strip().split("\n")

def do_random_mn(nbytes,wordlist):
	r = get_random(nbytes)
	Vmsg("Seed: %s" % hexlify(r))
	for wlname in (wordlists if wordlist == "all" else [wordlist]):
		wl = get_wordlist(wlname)
		mn = get_mnemonic_from_seed(r,wl,wordlist)
		Vmsg("%s wordlist mnemonic:" % (wlname.capitalize()))
		Msg(" ".join(mn))
