#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C) 2013-2014 by philemon <mmgen-py@yandex.com>
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

def print_version_info(progname):
	print """
'{}' version {g.version}.  Part of the {g.proj_name} suite.
Copyright (C) {g.Cdates} by {g.author} {g.email}.
""".format(progname, g=g).strip()

def print_help(progname,help_data):
	pn_len = str(len(progname)+2)
	print ("  %-"+pn_len+"s %s") % (progname.upper()+":", help_data['desc'].strip())
	print ("  %-"+pn_len+"s %s %s")%("USAGE:", progname, help_data['usage'].strip())
	sep = "\n    "
	print "  OPTIONS:"+sep+"%s" % sep.join(help_data['options'].strip().split("\n"))
	if "notes" in help_data:
		print "  %s" % "\n  ".join(help_data['notes'][1:-1].split("\n"))


def process_opts(argv,help_data,short_opts,long_opts):

	progname = argv[0].split("/")[-1]

	if len(argv) == 2 and argv[1] == '--version': # MMGen only!
		print_version_info(progname); sys.exit()

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


def parse_opts(argv,help_data):

	lines = help_data['options'].strip().split("\n")
	import re
	pat = r"^-([a-zA-Z0-9]), --([a-zA-Z0-9-]{1,64})(=*) (.*)"
	opt_data = [m.groups() for m in [re.match(pat,l) for l in lines] if m]

	short_opts = "".join([d[0]+(":" if d[2] else "") for d in opt_data if d])
	long_opts = [d[1].replace("-","_")+d[2] for d in opt_data if d]
	help_data['options'] = "\n".join(
		["-{0}, --{1}{w} {3}".format(w=" " if m.group(3) else "", *m.groups())
			if m else k for m,k in [(re.match(pat,l),l) for l in lines]]
	)
	opts,infiles = process_opts(argv,help_data,short_opts,long_opts)

	if not check_opts(opts,long_opts): sys.exit(1) # MMGen only!

	return opts,infiles


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

	for opt,val in opts.items():

		what = "parameter for '--%s' option" % opt.replace("_","-")

		# Check for file existence and readability
		if opt in ('keys_from_file','addrlist','passwd_file','keysforaddrs'):
			check_infile(val)
			return True

		if opt == 'outdir':
			what = "output directory"
			import os
			if os.path.isdir(val):
				if os.access(val, os.W_OK|os.X_OK):
					opts[opt] = os.path.normpath(val)
				else:
					msg("Requested %s '%s' is unwritable by you" % (what,val))
					return False
			else:
				msg("Requested %s '%s' doen not exist" % (what,val))
				return False

		elif opt == 'label':

			if len(val) > g.max_wallet_label_len:
				msg("Label must be %s characters or less" %
					g.max_wallet_label_len)
				return False

			for ch in list(val):
				chs = g.wallet_label_symbols
				if ch not in chs:
					msg("'%s': ERROR: label contains an illegal symbol" % val)
					msg("The following symbols are permitted:\n%s" % "".join(chs))
					return False
		elif opt == 'export_incog_hidden' or opt == 'from_incog_hidden':
			try:
				if opt == 'export_incog_hidden':
					outfile,offset = val.split(",")
				else:
					outfile,offset,seed_len = val.split(",")
			except:
				msg("'%s': invalid %s" % (val,what))
				return False

			try:
				o = int(offset)
			except:
				msg("'%s': invalid 'o' %s (not an integer)" % (offset,what))
				return False

			if o < 0:
				msg("'%s': invalid 'o' %s (less than zero)" % (offset,what))
				return False

			if opt == 'from_incog_hidden':
				try:
					sl = int(seed_len)
				except:
					msg("'%s': invalid 'l' %s (not an integer)" % (sl,what))
					return False

				if sl not in g.seed_lens:
					msg("'%s': invalid 'l' %s (valid choices: %s)" %
						(sl,what," ".join(str(i) for i in g.seed_lens)))
					return False

			import os, stat
			try: mode = os.stat(outfile).st_mode
			except:
				msg("Unable to stat requested %s '%s'" % (what,outfile))
				return False

			if not (stat.S_ISREG(mode) or stat.S_ISBLK(mode)):
				msg("Requested %s '%s' is not a file or block device" %
						(what,outfile))
				return False

			ac,m = (os.W_OK,"writ") \
				if "export_incog_hidden" in opts else (os.R_OK,"read")
			if not os.access(outfile, ac):
				msg("Requested %s '%s' is un%sable by you" % (what,outfile,m))
				return False

		elif opt == 'from_brain':
			try:
				l,p = val.split(",")
			except:
				msg("'%s': invalid %s" % (val,what))
				return False

			try:
				int(l)
			except:
				msg("'%s': invalid 'l' %s (not an integer)" % (l,what))
				return False

			if int(l) not in g.seed_lens:
				msg("'%s': invalid 'l' %s.  Options: %s" %
						(l, what, ", ".join([str(i) for i in g.seed_lens])))
				return False

			if p not in g.hash_presets:
				hps = ", ".join([i for i in sorted(g.hash_presets.keys())])
				msg("'%s': invalid 'p' %s.  Options: %s" % (p, what, hps))
				return False
		elif opt == 'seed_len':
			if val not in g.seed_lens:
				msg("'%s': invalid %s.  Options: %s"
				% (val,what,", ".join([str(i) for i in g.seed_lens])))
				return False
		elif opt == 'hash_preset':
			if val not in g.hash_presets:
				msg("'%s': invalid %s.  Options: %s"
				% (val,what,", ".join(sorted(g.hash_presets.keys()))))
				return False
		elif opt == 'usr_randlen':
			if val > g.max_randlen or val < g.min_randlen:
				msg("'%s': invalid %s (must be >= %s and <= %s)"
				% (val,what,g.min_randlen,g.max_randlen))
				return False
		else:
			if g.debug: print "check_opts(): No test for opt '%s'" % opt

	return True


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
