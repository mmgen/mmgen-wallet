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
from   binascii import hexlify, unhexlify

import sys

def b58_randenc():
	r = get_random(24)
	r_enc = b.b58encode(r)
	print "Data (hex):    %s" % hexlify(r)
	print "Base 58:       %s" % r_enc
	r_dec = b.b58decode(r_enc)
	print "Decoded data:  %s" % hexlify(r_dec)
	if r_dec != r:
		print "ERROR!  Decoded data doesn't match original"
		sys.exit(9)

def keyconv_compare_randloop(loops, quiet=False):
	for i in range(1,int(loops)+1):


		wif = numtowif_rand(quiet=True)

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
	wif = numtowif(int(hex_in,16))
	do_msg("WIF encoded:  %s" % wif)
	wif_dec = wiftohex(wif)
	do_msg("WIF decoded:  %s" % wif_dec)
	if hex_in != wif_dec:
		print "ERROR!  Decoded data doesn't match original data"
		sys.exit(9)
	return wif


def hextowiftopubkey(hex_in,quiet=False):
	if len(hex_in) != 64:
		print "Input must be a hex number 64 bits in length (%s input)" \
			% len(hex_in)
		sys.exit(2)

	wif = _do_hextowif(hex_in,quiet=quiet)

	keyconv_compare(wif)


def numtowif_rand(quiet=False):
	r_hex = hexlify(get_random(32))

	return _do_hextowif(r_hex,quiet)


def strtob58(s,quiet=False):
	print "Input:         %s" % s
	s_enc = b.b58encode(s)
	print "Encoded data:  %s" % s_enc
	s_dec = b.b58decode(s_enc)
	print "Decoded data:  %s" % s_dec
	test_equality(s,s_dec,[""],quiet)

def hextob58(s_in,f_enc=b.b58encode, f_dec=b.b58decode, quiet=False):
	do_msg = nomsg if quiet else msg
	do_msg("Input:         %s" % s_in)
	s_bin = unhexlify(s_in)
	s_enc = f_enc(s_bin)
	do_msg("Encoded data:  %s" % s_enc)
	s_dec = hexlify(f_dec(s_enc))
	do_msg("Recoded data:  %s" % s_dec)
	test_equality(s_in,s_dec,["0"],quiet)

def b58tohex(s_in,f_dec=b.b58decode, f_enc=b.b58encode,quiet=False):
	print "Input:         %s" % s_in
	s_dec = f_dec(s_in)
	print "Decoded data:  %s" % hexlify(s_dec)
	s_enc = f_enc(s_dec)
	print "Recoded data:  %s" % s_enc
	test_equality(s_in,s_enc,["1"],quiet)

def hextob58_pad(s_in, quiet=False):
	hextob58(s_in,f_enc=b.b58encode_pad, f_dec=b.b58decode_pad, quiet=quiet)

def b58tohex_pad(s_in, quiet=False):
	b58tohex(s_in,f_dec=b.b58decode_pad, f_enc=b.b58encode_pad, quiet=quiet)

def	hextob58_pad_randloop(loops, quiet=False):
	for i in range(1,int(loops)+1):
		r = hexlify(get_random(32))
		hextob58(r,f_enc=b.b58encode_pad, f_dec=b.b58decode_pad, quiet=quiet)
		if not quiet: print
		if not i % 100 and quiet:
			sys.stderr.write("\riteration: %i " % i)

	sys.stderr.write("\r%s iterations completed\n" % i)

def test_wiftohex(s_in,f_dec=b.wiftohex,f_enc=b.numtowif):
	print "Input:         %s" % s_in
	s_dec = f_dec(s_in)
	print "Decoded data:  %s" % s_dec
	s_enc = f_enc(int(s_dec,16))
	print "Recoded data:  %s" % s_enc

def hextosha256(s_in):
	print "Entered data:   %s" % s_in
	s_enc = sha256(unhexlify(s_in)).hexdigest()
	print "Encoded data:   %s" % s_enc

def pubhextoaddr(s_in):
	print "Entered data:   %s" % s_in
	s_enc = b.pubhex2addr(s_in)
	print "Encoded data:   %s" % s_enc

def hextowif_comp(s_in):
	print "Entered data:   %s" % s_in
	s_enc = b.hextowif(s_in,compressed=True)
	print "Encoded data:   %s" % s_enc
	s_dec = b.wiftohex(s_enc,compressed=True)
	print "Decoded data:   %s" % s_dec

def wiftohex_comp(s_in):
	print "Entered data:   %s" % s_in
	s_enc = b.wiftohex(s_in,compressed=True)
	print "Encoded data:   %s" % s_enc
	s_dec = b.hextowif(s_enc,compressed=True)
	print "Decoded data:   %s" % s_dec

def privhextoaddr_comp(hexpriv):
	print b.privnum2addr(int(hexpriv,16),compressed=True)

def wiftoaddr_comp(s_in):
	print "Entered data:   %s" % s_in
	s_enc = b.wiftohex(s_in,compressed=True)
	print "Encoded data:   %s" % s_enc
	s_enc = b.privnum2addr(int(s_enc,16),compressed=True)
	print "Encoded data:   %s" % s_enc

tests = {
	"keyconv_compare":          ['wif [str]','quiet [bool=False]'],
	"keyconv_compare_randloop": ['iterations [int]','quiet [bool=False]'],
	"b58_randenc":              ['quiet [bool=False]'],
	"strtob58":                 ['string [str]','quiet [bool=False]'],
	"hextob58":                 ['hexnum [str]','quiet [bool=False]'],
	"b58tohex":                 ['b58num [str]','quiet [bool=False]'],
	"hextob58_pad":             ['hexnum [str]','quiet [bool=False]'],
	"b58tohex_pad":             ['b58num [str]','quiet [bool=False]'],
	"hextob58_pad_randloop":    ['iterations [int]','quiet [bool=False]'],
	"test_wiftohex":            ['wif [str]',       'quiet [bool=False]'],
	"numtowif_rand":            ['quiet [bool=False]'],
	"hextosha256":              ['hexnum [str]','quiet [bool=False]'],
	"hextowiftopubkey":         ['hexnum [str]','quiet [bool=False]'],
	"pubhextoaddr":             ['hexnum [str]','quiet [bool=False]'],
	"hextowif_comp":            ['hexnum [str]'],
	"wiftohex_comp":            ['wif [str]'],
	"privhextoaddr_comp":       ['hexnum [str]'],
	"wiftoaddr_comp":           ['wif [str]'],
}

args = process_test_args(sys.argv, tests)
eval(sys.argv[1])(*args)
