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
bitcoin.py:  Test suite for mmgen.bitcoin module
"""

import mmgen.bitcoin as b
from   mmgen.util import msg
from   mmgen.tests.test import *
from   binascii import hexlify
import sys

def keyconv_compare_randloop(loops, quiet=False):
	for i in range(1,int(loops)+1):


		wif = _numtowif_rand(quiet=True)

		if not quiet: sys.stderr.write("-- %s --\n" % i)
		ret = keyconv_compare(wif,quiet)
		if ret == False: sys.exit(9)

		if quiet:
			sys.stderr.write("\riteration: %i " % i)

	if quiet:
		sys.stderr.write("\r%s iterations completed\n" % i)
	else:
		print "%s iterations completed" % i

def keyconv_compare(wif,quiet=False):
	do_msg = nomsg if quiet else msg
	do_msg("WIF:               %s" % wif)
	from subprocess import Popen, PIPE
	try:
		p = Popen(["keyconv", wif], stdout=PIPE)
	except:
		print "Error with execution of keyconv"
		sys.exit(3)
	kc_addr = dict([j.split() for j in p.stdout.readlines()])['Address:']
	addr = b.privnum2addr(b.wiftonum(wif))
	do_msg("Address (mmgen):   %s" % addr)
	do_msg("Address (keyconv): %s" % kc_addr)
	if (kc_addr != addr):
		print "'keyconv' addr differs from internally-generated addr!"
		print "WIF:      %s" % wif
		print "keyconv:  %s" % kc_addr
		print "internal: %s" % addr
		return False
	else:
		return True

def _do_hextowif(hex_in,quiet=False):
	do_msg = nomsg if quiet else msg
	do_msg("Input:        %s" % hex_in)
	wif = b.numtowif(int(hex_in,16))
	do_msg("WIF encoded:  %s" % wif)
	wif_dec = b.wiftohex(wif)
	do_msg("WIF decoded:  %s" % wif_dec)
	if hex_in != wif_dec:
		print "ERROR!  Decoded data doesn't match original data"
		sys.exit(9)
	return wif

def _numtowif_rand(quiet=False):
	r_hex = hexlify(get_random(32))

	return _do_hextowif(r_hex,quiet)


tests = {
	"keyconv_compare":          ['wif [str]','quiet [bool=False]'],
	"keyconv_compare_randloop": ['iterations [int]','quiet [bool=False]'],
}

args = process_test_args(sys.argv, tests)
eval(sys.argv[1])(*args)
