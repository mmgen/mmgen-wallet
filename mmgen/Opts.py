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
import mmgen.config as g

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

	if g.debug:
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

	if g.debug: print "User-selected options: %s" % repr(opts)

	return opts,args


def show_opts_and_cmd_args(opts,cmd_args):
	print "Processed options:     %s" % repr(opts)
	print "Cmd args:              %s" % repr(cmd_args)


# Everything below here is MMGen-specific:

from mmgen.util import msg,check_infile

def check_opts(opts,long_opts):

	# These must be set to the default values in mmgen.config:
	for i in g.cl_override_vars:
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
			# TODO Non-portable:
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

			if len(label) > g.max_wallet_label_len:
				msg("Label must be %s characters or less" %
					g.max_wallet_label_len)
				sys.exit(1)

			for ch in list(label):
				if ch not in g.wallet_label_symbols:
					msg("""
"%s": illegal character in label.  Only ASCII characters are permitted.
""".strip() % ch)
					sys.exit(1)
		elif opt == 'hide_incog_data' or opt == 'hidden_incog_data':
			try:
				if opt == 'hide_incog_data':
					outfile,offset = val.split(",")
				else:
					outfile,offset,seed_len = val.split(",")
			except:
				msg("'%s': invalid %s" % (val,what))
				sys.exit(1)

			try:
				o = int(offset)
			except:
				msg("'%s': invalid 'o' %s (not an integer)" % (offset,what))
				sys.exit(1)

			if o < 0:
				msg("'%s': invalid 'o' %s (less than zero)" % (offset,what))
				sys.exit(1)

			if opt == 'hidden_incog_data':
				try:
					sl = int(seed_len)
				except:
					msg("'%s': invalid 'l' %s (not an integer)" % (sl,what))
					sys.exit(1)

				if sl not in g.seed_lens:
					msg("'%s': invalid 'l' %s (valid choices: %s)" %
						(sl,what," ".join(str(i) for i in g.seed_lens)))
					sys.exit(1)

			import os, stat
			try: mode = os.stat(outfile).st_mode
			except:
				msg("Unable to stat requested %s '%s'" % (what,outfile))
				sys.exit(1)

			if not (stat.S_ISREG(mode) or stat.S_ISBLK(mode)):
				msg("Requested %s '%s' is not a file or block device" %
						(what,outfile))
				sys.exit(1)

			ac,m = (os.W_OK,"writ") \
				if "hide_incog_data" in opts else (os.R_OK,"read")
			if not os.access(outfile, ac):
				msg("Requested %s '%s' is un%sable by you" % (what,outfile,m))
				sys.exit(1)

		elif opt == 'from_brain':
			try:
				l,p = val.split(",")
			except:
				msg("'%s': invalid %s" % (val,what))
				sys.exit(2)

			try:
				int(l)
			except:
				msg("'%s': invalid 'l' %s (not an integer)" % (l,what))
				sys.exit(1)

			if int(l) not in g.seed_lens:
				msg("'%s': invalid 'l' %s.  Options: %s" %
						(l, what, ", ".join([str(i) for i in g.seed_lens])))
				sys.exit(1)

			if p not in g.hash_presets:
				hps = ", ".join([i for i in sorted(g.hash_presets.keys())])
				msg("'%s': invalid 'p' %s.  Options: %s" % (p, what, hps))
				sys.exit(1)
		elif opt == 'seed_len':
			if val not in g.seed_lens:
				msg("'%s': invalid %s.  Options: %s"
				% (val,what,", ".join([str(i) for i in g.seed_lens])))
				sys.exit(2)
		elif opt == 'hash_preset':
			if val not in g.hash_presets:
				msg("'%s': invalid %s.  Options: %s"
				% (val,what,", ".join(sorted(g.hash_presets.keys()))))
				sys.exit(2)
		elif opt == 'usr_randlen':
			if val > g.max_randlen or val < g.min_randlen:
				msg("'%s': invalid %s (must be >= %s and <= %s)"
				% (val,what,g.min_randlen,g.max_randlen))
				sys.exit(2)
		else:
			if g.debug: print "check_opts(): No test for opt '%s'" % opt


def set_if_unset_and_typeconvert(opts,opt):

	if opt in g.cl_override_vars:
		if opt not in opts:
			# Set to similarly named default value in mmgen.config
			opts[opt] = eval("g."+opt)
		else:
			vtype = type(eval("g."+opt))
			if g.debug: print "Opt: %s, Type: %s" % (opt,vtype)
			if   vtype == int:   f,t = int,"an integer"
			elif vtype == str:   f,t = str,"a string"
			elif vtype == float: f,t = float,"a float"

			try:
				opts[opt] = f(opts[opt])
			except:
				msg("'%s': invalid parameter for '--%s' option (not %s)" %
						(opts[opt],opt.replace("_","-"),t))
				sys.exit(1)
