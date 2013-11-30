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

import sys, getopt
from mmgen.config import *

def usage(hd):
	print "USAGE: %s %s" % (hd['prog_name'], hd['usage'])
	sys.exit(2)

def print_help(progname,help_data):
	pn_len = str(len(progname)+2)
	print ("  %-"+pn_len+"s %s")    % (progname.upper()+":", help_data['desc'])
	print ("  %-"+pn_len+"s %s %s") % ("USAGE:", progname, help_data['usage'])
	sep = "\n    "
	print "  OPTIONS:"+sep+"%s" % sep.join(help_data['options'].strip().split("\n"))


def process_opts(argv,help_data,short_opts,long_opts):

	progname = argv[0].split("/")[-1]

	if debug:
		print "Short opts: %s" % repr(short_opts)
		print "Long opts:  %s" % repr(long_opts)

	long_opts  = [i.replace("_","-") for i in long_opts]

	try: cl_opts, args = getopt.getopt(argv[1:], short_opts, long_opts)
	except getopt.GetoptError as err:
		print str(err); sys.exit(2)

	opts,short_opts_l = {},[]

	for i in short_opts:
		if i == ":": short_opts_l[-1] += i
		else:        short_opts_l     += i

	for opt, arg in cl_opts:
		if   opt in ("-h","--help"): print_help(progname,help_data); sys.exit()
		elif opt[:2] == "--" and opt[2:] in long_opts:
			opts[opt[2:].replace("-","_")] = True
		elif opt[:2] == "--" and opt[2:]+"=" in long_opts:
			opts[opt[2:].replace("-","_")] = arg
		elif opt[0] == "-" and opt[1]     in short_opts_l:
			opts[long_opts[short_opts_l.index(opt[1:])].replace("-","_")] = True
		elif opt[0] == "-" and opt[1:]+":" in short_opts_l:
			opts[long_opts[short_opts_l.index(opt[1:]+":")][:-1].replace("-","_")] = arg
		else: assert False, "Invalid option"

	if debug: print "User-selected options: %s" % repr(opts)

	return opts,args
