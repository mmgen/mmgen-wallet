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
mnemonic.py:  Test suite for mmgen.mnemonic module
"""

from mmgen.mnemonic import *
from test import *

import sys
from binascii import hexlify
from mmgen.mn_electrum  import electrum_words as el
from mmgen.mn_tirosh    import tirosh_words   as tl

def do_random_tests(n):
	r = get_random(n)
	em = get_mnemonic_from_seed(r,el.strip().split("\n"),
			"electrum",print_info=False)
	tm = get_mnemonic_from_seed(r,tl.strip().split("\n"),
			"tirosh",print_info=False)

	print "Seed:     %s (%s bits)" % (hexlify(r),len(r)*8)
	print "Electrum: %s" % " ".join(em)
	print "Tirosh:   %s" % " ".join(tm)


def hextobaseN_test(num_in,base,wl,quiet=False):
	do_msg = nomsg if quiet else msg
	do_msg("Input:         %s" % num_in)
	num_enc = "".join(hextobaseN(base,num_in,wl,len(num_in)*2))
	do_msg("Encoded value: %s" % num_enc)
	num_dec = baseNtohex(base,num_enc,wl)
	do_msg("Decoded value: %s" % num_dec)
	test_equality(num_in,num_dec,wl,quiet)
	return num_enc,num_dec


def baseNtohex_test(num_in,base,wl,quiet=False):
	do_msg = nomsg if quiet else msg
	do_msg("Input:         %s" % num_in)
	num_enc = baseNtohex(base,list(num_in),wl)
	do_msg("Encoded value: %s" % num_enc)
	num_dec = "".join(hextobaseN(base,num_enc,wl,len(num_enc)*2))
	do_msg("Decoded value: %s" % num_dec)
	test_equality(num_in,num_dec,wl,quiet)
	return num_enc,num_dec


def random128(): do_random_tests(16)
def random192(): do_random_tests(24)
def random256(): do_random_tests(32)
def random512(): do_random_tests(64)
def electrum():  check_wordlist(el,"electrum")
def tirosh():    check_wordlist(tl,"tirosh")

def base10tohex(num,quiet=False):
	enc,dec = baseNtohex_test(num,10,"0123456789",quiet)
	print "Decimal:           %s" % num
	print "Hex (encoded):     %s" % enc
	print "Decimal (recoded): %s" % dec.lstrip("0")

def hextobase10(num,quiet=False):
	enc,dec= hextobaseN_test(num,10,"0123456789",quiet)
	print "Hex:               %s" % num
	print "Decimal (encoded): %s" % enc.lstrip("0")
	print "Hex (recoded):     %s" % dec

def base8tohex(num,quiet=False):
	enc,dec = baseNtohex_test(num,8,"01234567",quiet)
	print "Octal:           %s" % num
	print "Hex (encoded):   %s" % enc
	print "Octal (recoded): %s" % "0" + dec.lstrip("0")

def hextobase8(num,quiet=False):
	enc,dec = hextobaseN_test(num,8,"01234567",quiet)
	print "Hex:           %s" % num
	print "Octal:         %s" % "0" + enc.lstrip("0")
	print "Hex (recoded): %s" % dec

tests = {
	"random128":      [],
	"random192":      [],
	"random256":      [],
	"random512":      [],
	"electrum":       [],
	"tirosh":         [],
	"base10tohex":    ['base10num [int]','quiet [bool=False]'],
	"hextobase10":    ['hexnum [str]',   'quiet [bool=False]'],
	"base8tohex":     ['base8num [int]', 'quiet [bool=False]'],
	"hextobase8":     ['hexnum [str]',   'quiet [bool=False]'],
}

args = process_test_args(sys.argv, tests)
eval(sys.argv[1])(*args)
