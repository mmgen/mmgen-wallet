#!/usr/bin/env python
#
# Opts.py, an options parsing library for Python.  Copyright (C) 2014 by
# Philemon <mmgen-py@yandex.com>.
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

def usage(opts_data):
	print "USAGE: %s %s" % (opts_data['prog_name'], opts_data['usage'])
	sys.exit(2)

def print_help(opts_data):
	pn = opts_data['prog_name']
	pn_len = str(len(pn)+2)
	print ("  %-"+pn_len+"s %s") % (pn.upper()+":", opts_data['desc'].strip())
	print ("  %-"+pn_len+"s %s %s")%("USAGE:", pn, opts_data['usage'].strip())
	sep = "\n    "
	print "  OPTIONS:"+sep+"%s" % sep.join(opts_data['options'].strip().split("\n"))
	if "notes" in opts_data:
		print "  %s" % "\n  ".join(opts_data['notes'][1:-1].split("\n"))


def process_opts(argv,opts_data,short_opts,long_opts):

	import os
	opts_data['prog_name'] = os.path.split(sys.argv[0])[1]
	long_opts  = [i.replace("_","-") for i in long_opts]

	try: cl_opts, args = getopt.getopt(argv[1:], short_opts, long_opts)
	except getopt.GetoptError as err:
		print str(err); sys.exit(2)

	opts,short_opts_l = {},[]

	for i in short_opts:
		if i == ":": short_opts_l[-1] += i
		else:        short_opts_l     += i

	for opt, arg in cl_opts:
		if   opt in ("-h","--help"): print_help(opts_data); sys.exit()
		elif opt[:2] == "--" and opt[2:] in long_opts:
			opts[opt[2:].replace("-","_")] = True
		elif opt[:2] == "--" and opt[2:]+"=" in long_opts:
			opts[opt[2:].replace("-","_")] = arg
		elif opt[0] == "-" and opt[1]     in short_opts_l:
			opts[long_opts[short_opts_l.index(opt[1:])].replace("-","_")] = True
		elif opt[0] == "-" and opt[1:]+":" in short_opts_l:
			opts[long_opts[short_opts_l.index(
					opt[1:]+":")][:-1].replace("-","_")] = arg
		else: assert False, "Invalid option"

	return opts,args


def parse_opts(argv,opts_data):

	lines = opts_data['options'].strip().split("\n")
	import re
	pat = r"^-([a-zA-Z0-9]), --([a-zA-Z0-9-]{1,64})(=| )(.+)"
	rep = r"-{0}, --{1}{w}{3}"
	opt_data = [list(m.groups()) for m in [re.match(pat,l) for l in lines] if m]

	for d in opt_data:
		if d[2] == " ": d[2] = ""
	short_opts = "".join([d[0]+d[2].replace("=",":") for d in opt_data])
	long_opts = [d[1].replace("-","_")+d[2] for d in opt_data]
	opts_data['options'] = "\n".join(
		[rep.format(w=" ", *m.groups())
			if m else k for m,k in [(re.match(pat,l),l) for l in lines]]
	)
	opts,args = process_opts(argv,opts_data,short_opts,long_opts)

	return opts,args,short_opts,long_opts
