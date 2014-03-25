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
from mmgen.utils import msg

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


def check_opts(opts,long_opts):

	# These must be set to the default values in mmgen.config:
	for i in cl_override_vars:
		if i+"=" in long_opts:
			set_if_unset_and_typeconvert(opts,i)

	for opt in opts.keys():

		val = opts[opt]
		what = "parameter for '--%s' option" % opt.replace("_","-")

		# Check for file existence and readability
		for i in 'keys_from_file','addrlist','passwd_file','keysforaddrs':
			if opt == i:
				check_infile(val)
				return

		if opt == 'outdir':
			what = "output directory"
			import re, os, stat
			d = re.sub(r'/*$','', val)
			opts[opt] = d

			try: mode = os.stat(d).st_mode
			except:
				msg("Unable to stat requested %s '%s'" % (what,d))
				sys.exit(1)

			if not stat.S_ISDIR(mode):
				msg("Requested %s '%s' is not a directory" % (what,d))
				sys.exit(1)

			if not os.access(d, os.W_OK|os.X_OK):
				msg("Requested %s '%s' is unwritable by you" % (what,d))
				sys.exit(1)
		elif opt == 'label':
			label = val.strip()
			opts[opt] = label

			if len(label) > 32:
				msg("Label must be 32 characters or less")
				sys.exit(1)

			from string import ascii_letters, digits
			label_chrs = list(ascii_letters + digits) + [".", "_", " "]
			for ch in list(label):
				if ch not in label_chrs:
					msg("'%s': illegal character in label" % ch)
					sys.exit(1)
		elif opt == 'from_brain':
			try:
				l,p = val.split(",")
			except:
				msg("'%s': invalid %s" % (val,what))
				sys.exit(1)

			try:
				int(l)
			except:
				msg("'%s': invalid 'l' %s (not an integer)" % (l,what))
				sys.exit(1)

			if int(l) not in seed_lens:
				msg("'%s': invalid 'l' %s.  Options: %s" %
						(l, what, ", ".join([str(i) for i in seed_lens])))
				sys.exit(1)

			if p not in hash_presets:
				hps = ", ".join([i for i in sorted(hash_presets.keys())])
				msg("'%s': invalid 'p' %s.  Options: %s" % (p, what, hps))
				sys.exit(1)
		elif opt == 'seed_len':
			if val not in seed_lens:
				msg("'%s': invalid %s.  Options: %s"
				% (val,what,", ".join([str(i) for i in seed_lens])))
				sys.exit(2)
		elif opt == 'hash_preset':
			if val not in hash_presets:
				msg("'%s': invalid %s.  Options: %s"
				% (val,what,", ".join(sorted(hash_presets.keys()))))
				sys.exit(2)
		elif opt == 'usr_randlen':
			if val > max_randlen or val < min_randlen:
				msg("'%s': invalid %s (must be >= %s and <= %s)"
				% (val,what,min_randlen,max_randlen))
				sys.exit(2)
		else:
			if debug: print "check_opts(): No test for opt '%s'" % opt


def show_opts_and_cmd_args(opts,cmd_args):
	print "Processed options:     %s" % repr(opts)
	print "Cmd args:              %s" % repr(cmd_args)


def set_if_unset_and_typeconvert(opts,opt):

	if opt in cl_override_vars:
		if opt not in opts:
			# Set to similarly named default value in mmgen.config
			opts[opt] = eval(opt)
		else:
			vtype = type(eval(opt))
			if   vtype == int: f,t = int,"an integer"
			elif vtype == str: f,t = str,"a string"

			try:
				opts[opt] = f(opts[opt])
			except:
				msg("'%s': invalid parameter for '--%s' option (not %s)" %
						(opts[opt],opt.replace("_","-"),t))
				sys.exit(1)
