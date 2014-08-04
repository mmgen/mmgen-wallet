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

import sys
import mmgen.config as g
import mmgen.opt.Opts
from mmgen.util import msg,check_infile,check_outfile,check_outdir

def usage(hd): mmgen.opt.Opts.usage(hd)

def print_version_info():
	print """
'{g.prog_name}' version {g.version}.  Part of the {g.proj_name} suite.
Copyright (C) {g.Cdates} by {g.author} {g.email}.
""".format(g=g).strip()

def warn_incompatible_opts(opts,incompat_list):
	bad = [k for k in opts.keys() if k in incompat_list]
	if len(bad) > 1:
		msg("Mutually exclusive options: %s" % " ".join(
					["--"+b.replace("_","-") for b in bad]))
		sys.exit(1)

def parse_opts(argv,help_data):

	if len(argv) == 2 and argv[1] == '--version':
		print_version_info(); sys.exit()

	opts,args,short_opts,long_opts = mmgen.opt.Opts.parse_opts(argv,help_data)

	if g.debug:
		print "short opts: %s" % repr(short_opts)
		print "long opts:  %s" % repr(long_opts)
		print "user-selected opts: %s" % repr(opts)
		print "cmd args:           %s" % repr(args)

	for l in (
	('outdir', 'export_incog_hidden'),
	('from_incog_hidden','from_incog','from_seed','from_mnemonic','from_brain'),
	('export_incog','export_incog_hex','export_incog_hidden','export_mnemonic',
	 'export_seed'),
	('quiet','verbose')
	): warn_incompatible_opts(opts,l)

	# check_opts() doesn't touch opts[]
	if not check_opts(opts,long_opts): sys.exit(1)

	# If unset, set these to default values in mmgen.config:
	for v in g.cl_override_vars:
		if v in opts: typeconvert_override_var(opts,v)
		else: opts[v] = eval("g."+v)

	if g.debug: print "opts after typeconvert: %s" % opts

	return opts,args


def show_opts_and_cmd_args(opts,cmd_args):
	print "Processed options: %s" % repr(opts)
	print "Cmd args:          %s" % repr(cmd_args)

def check_opts(opts,long_opts):

	def opt_splits(val,sep,n,what):
		sepword = "comma" if sep == "," else (
					"colon" if sep == ":" else ("'"+sep+"'"))
		try: l = val.split(sep)
		except:
			msg("'%s': invalid %s (not %s-separated list)" % (val,what,sepword))
			return False

		if len(l) == n: return True
		else:
			msg("'%s': invalid %s (%s %s-separated items required)" %
					(val,what,n,sepword))
			return False

	def opt_compares(val,op,target,what):
		if not eval("%s %s %s" % (val, op, target)):
			msg("%s: invalid %s (not %s %s)" % (val,what,op,target))
			return False
		return True

	def opt_is_int(val,what):
		try: int(val)
		except:
			msg("'%s': invalid %s (not an integer)" % (val,what))
			return False
		return True

	def opt_is_in_list(val,lst,what):
		if val not in lst:
			q,sep = ("'","','") if type(lst[0]) == str else ("",",")
			msg("{q}{}{q}: invalid {}\nValid options: {q}{}{q}".format(
					val,what,sep.join([str(i) for i in sorted(lst)]),q=q))
			return False
		return True

	for opt,val in opts.items():

		what = "parameter for '--%s' option" % opt.replace("_","-")

		# Check for file existence and readability
		if opt in ('keys_from_file','all_keys_from_file','addrlist',
				'passwd_file','keysforaddrs'):
			check_infile(val)  # exits on error
			continue

		if opt == 'outdir':
			check_outdir(val)  # exits on error
		elif opt == 'label':
			if not opt_compares(len(val),"<=",g.max_wallet_label_len,"label length"):
				return False
			try: val.decode("ascii")
			except:
				msg("ERROR: label contains a non-ASCII symbol")
				return False
			w = "character in label"
			for ch in list(val):
				if not opt_is_in_list(ch,g.wallet_label_symbols,w): return False
		elif opt == 'export_incog_hidden' or opt == 'from_incog_hidden':
			if opt == 'from_incog_hidden':
				if not opt_splits(val,",",3,what): return False
				infile,offset,seed_len = val.split(",")
				check_infile(infile)
				w = "seed length " + what
				if not opt_is_int(seed_len,w): return False
				if not opt_is_in_list(int(seed_len),g.seed_lens,w): return False
			else:
				if not opt_splits(val,",",2,what): return False
				outfile,offset = val.split(",")
				check_outfile(outfile)
			w = "offset " + what
			if not opt_is_int(offset,w): return False
			if not opt_compares(offset,">=",0,what): return False
		elif opt == 'from_brain':
			if not opt_splits(val,",",2,what): return False
			l,p = val.split(",")
			w = "seed length " + what
			if not opt_is_int(l,w): return False
			if not opt_is_in_list(int(l),g.seed_lens,w): return False
			w = "hash preset " + what
			if not opt_is_in_list(p,g.hash_presets.keys(),w): return False
		elif opt == 'seed_len':
			if not opt_is_int(val,what): return False
			if not opt_is_in_list(int(val),g.seed_lens,what): return False
		elif opt == 'hash_preset':
			if not opt_is_in_list(val,g.hash_presets.keys(),what): return False
		elif opt == 'usr_randchars':
			if not opt_is_int(val,what): return False
			if not opt_compares(val,">=",g.min_urandchars,what): return False
			if not opt_compares(val,"<=",g.max_urandchars,what): return False
		else:
			if g.debug: print "check_opts(): No test for opt '%s'" % opt

	return True


def typeconvert_override_var(opts,opt):

	vtype = type(eval("g."+opt))
	if g.debug: print "Override opt: %-15s [%s]" % (opt,vtype)

	if   vtype == int:   f,t = int,"an integer"
	elif vtype == str:   f,t = str,"a string"
	elif vtype == float: f,t = float,"a float"

	try:
		opts[opt] = f(opts[opt])
	except:
		msg("'%s': invalid parameter for '--%s' option (not %s)" %
				(opts[opt],opt.replace("_","-"),t))
		sys.exit(1)
