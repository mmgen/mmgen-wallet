#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2015 Philemon <mmgen-py@yandex.com>
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
opts.py:  Further options processing after mmgen.share.Opts
"""
import sys

import mmgen.config as g
import mmgen.share.Opts
import opt
from mmgen.util import msg,msgrepr_exit,msgrepr

def usage(opts_data):
	print "USAGE: %s %s" % (opts_data['prog_name'], opts_data['usage'])
	sys.exit(2)

def print_version_info():
	print """
'{g.prog_name}' version {g.version}.  Part of the {g.proj_name} suite.
Copyright (C) {g.Cdates} by {g.author} {g.email}.
""".format(g=g).strip()

def warn_incompatible_opts(incompat_list):
	bad = [k for k in opt.__dict__ if opt.__dict__[k] and k in incompat_list]
	if len(bad) > 1:
		msg("Mutually exclusive options: %s" % " ".join(
					["--"+b.replace("_","-") for b in bad]))
		sys.exit(1)

def typeconvert_from_dfl(opts,opt):

	vtype = type(g.__dict__[opt])
	if g.debug: print "Override opt: %-15s [%s]" % (opt,vtype)

	try:
		opts[opt] = vtype(opts[opt])
	except:
		d = {
			'int':   'an integer',
			'str':   'a string',
			'float': 'a float',
			'bool':  'a boolean value',
		}
		m = [d[k] for k in d if __builtins__[k] == vtype][0]
		msg("'%s': invalid parameter for '--%s' option (not %s)" %
				(opts[opt],opt.replace("_","-"),m))
		sys.exit(1)

def init(opts_data,add_opts=[]):

	if len(sys.argv) == 2 and sys.argv[1] == '--version':
		print_version_info(); sys.exit()

	opts,args,short_opts,long_opts = mmgen.share.Opts.parse_opts(sys.argv,opts_data)

	if g.debug:
		print "short opts: %s" % repr(short_opts)
		print "long opts:  %s" % repr(long_opts)
		print "user-selected opts: %s" % repr(opts)
		print "cmd args:           %s" % repr(args)

	# check opts without modifying them
	if not check_opts(opts,long_opts): sys.exit(1)

	# If user opt is set, an opt in mmgen.config is set to 'True'
	for v in g.usr_set_vars:
		if v in opts:
			g.__dict__[g.usr_set_vars[v]] = True

	# If user opt is unset, set it to default value in mmgen.config (g):
	# If set, convert its type based on value in mmgen.config
	for v in g.dfl_vars:
		if v in opts: typeconvert_from_dfl(opts,v)
		else: opts[v] = g.__dict__[v]

	if g.debug: print "opts after typeconvert: %s" % opts

	# A hack, but harmless
	extra_opts = [
		"quiet","verbose","debug",
		"outdir","echo_passphrase","passwd_file"
	] + add_opts

	# Transfer opts into our custom namespace
	for o in [s.rstrip("=") for s in long_opts] + extra_opts:
		opt.__dict__[o] = opts[o] if o in opts else None

	for l in (
	('from_incog_hidden','from_incog','from_seed','from_mnemonic','from_brain'),
	('export_incog','export_incog_hex','export_incog_hidden','export_mnemonic',
	'export_seed'),
	('quiet','verbose')
	): warn_incompatible_opts(l)

	del mmgen.share.Opts
	return args

def show_opts_and_cmd_args(cmd_args):
	print "Processed options:"
	d = opt.__dict__
	for k in d:
		if k[:2] != "__" and k != "opts" and d[k] != None:
			msg("%-20s: %s" % (k, d[k]))
	print "Cmd args: %s" % repr(cmd_args)

def show_all_opts():
	msg("Processed options:")
	d = opt.__dict__
	for k in d:
		if k[:2] != "__" and k != "opts":
			msg("%-20s: %s" % (k, d[k]))

def check_opts(opts,long_opts):       # Returns false if any check fails

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
		if opt in ('keys_from_file','mmgen_keys_from_file',
				'passwd_file','keysforaddrs','comment_file'):
			from mmgen.util import check_infile
			check_infile(val)  # exits on error
			continue

		if opt == 'outdir':
			from mmgen.util import check_outdir
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
				from mmgen.util import check_infile
				check_infile(infile)
				w = "seed length " + what
				if not opt_is_int(seed_len,w): return False
				if not opt_is_in_list(int(seed_len),g.seed_lens,w): return False
			else:
				from mmgen.util import check_outfile
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
			if 'debug' in opts: print "check_opts(): No test for opt '%s'" % opt

	return True
