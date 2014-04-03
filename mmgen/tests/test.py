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
test.py:  Shared routines for mmgen test suite
"""

import sys
from mmgen.util import msg

def nomsg(s): pass

def test_equality(num_in,num_out,wl,quiet=False):

	do_msg = nomsg if quiet else msg

	if num_in != num_out:
		do_msg("WARNING! Recoded number doesn't match input stringwise!")
		do_msg("Input:  %s" % num_in)
		do_msg("Output: %s" % num_out)

	i = num_in.lstrip(wl[0])
	o = num_out.lstrip(wl[0])

	if i != o:
		print "ERROR! Recoded number doesn't match input numerically!"
		sys.exit(9)


def get_random(length):
	from Crypto import Random
	return Random.new().read(length)

def process_test_args(argv, tests):
	if (len(argv) == 1):
		print "Usage: %s <test>" % argv[0].split("/")[-1]
		ls = "\n   "
		print "Available tests:%s%s" % (ls,ls.join(sorted(tests.keys())))
		sys.exit(1)
	elif argv[1] not in tests:
		print "'%s': no such test" % argv[1]
		sys.exit(2)
	else:
		cargs = tests[argv[1]]
		uargs = argv[2:]
		if len(uargs) > len(cargs):
			print "Too many arguments\nUsage: %s(%s)" % \
				(argv[1], ", ".join(cargs))
			sys.exit()

		for i in range(len(cargs)):
			try:    uarg = uargs[i]
			except: uarg = None

			cname,ctype_arg = cargs[i].split()
			c = ctype_arg[1:-1].split("=")[0:]
			ctype,cdflt = c[0],c[1:]

			if uarg == None and not cdflt:
				print "Usage: %s(%s)" % \
					(argv[1], ", ".join(cargs))
				sys.exit()

#		print "%-10s %-7s %s" % (uarg, cargs[i], carg)

			if uarg:
				try: eval(ctype + "('" + uarg + "')")
				except:
					print "'%s' Invalid argument (%s required)" % (uarg, ctype)
					sys.exit()

		return uargs
