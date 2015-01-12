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
opts.py:  MMGen-specific options processing after generic processing by share.Opts
"""
import sys

import mmgen.config as g
import mmgen.share.Opts
import opt
from mmgen.util import msg,msgrepr_exit,msgrepr,Msg

def usage():
	Msg("USAGE: %s %s" % (g.prog_name, usage_txt))
	sys.exit(2)

def print_version_info():
	Msg("""
{progname_uc} version {g.version}.  Part of the {g.proj_name} suite, a Bitcoin
cold-storage solution for the command line.  Copyright (C) {g.Cdates}
by {g.author} {g.email}
""".format(g=g,progname_uc=g.prog_name.upper()).strip())

def warn_incompatible_opts(incompat_list):
	bad = [k for k in opt.__dict__ if opt.__dict__[k] and k in incompat_list]
	if len(bad) > 1:
		msg("Mutually exclusive options: %s" % " ".join(
					["--"+b.replace("_","-") for b in bad]))
		sys.exit(1)

def typeconvert_from_dfl(key):

	vtype = type(g.__dict__[key])
	if g.debug: Msg("Override opt: %-15s [%s]" % (key,vtype))

	global opt

	try:
		opt.__dict__[key] = vtype(opt.__dict__[key])
	except:
		d = {
			'int':   'an integer',
			'str':   'a string',
			'float': 'a float',
			'bool':  'a boolean value',
		}
		m = [d[k] for k in d if __builtins__[k] == vtype]
		msgrepr_exit(key,vtype)
		fs = "'%s': invalid parameter for '--%s' option (not %s)"
		msg(fs % (opt.__dict__[key],opt.replace("_","-"),m))
		sys.exit(1)

def init(opts_data,add_opts=[]):

	if len(sys.argv) == 2 and sys.argv[1] == '--version':
		print_version_info(); sys.exit()

	uopts,args,short_opts,long_opts = \
		mmgen.share.Opts.parse_opts(sys.argv,opts_data)

	if g.debug:
		d = (
			("short opts",         short_opts),
			("long opts",          long_opts),
			("user-selected opts", uopts),
			("cmd args",           args),
		)
		for e in d: Msg("{:<20}: {}".format(*e))

	# Save this for usage()
	global usage_txt
	usage_txt = opts_data['usage']

	# We don't need this data anymore
	del mmgen.share.Opts
	for k in 'prog_name','desc','usage','options','notes':
		if k in opts_data: del opts_data[k]

	# Remove all unneeded attributes from opt, our special global namespace
	for k in dir(opt):
		if k[:2] == "__": del opt.__dict__[k]

	# Transfer uopts into opt, setting required opts to None if not set by user
	for o in [s.rstrip("=") for s in long_opts] + g.required_opts + add_opts:
		opt.__dict__[o] = uopts[o] if o in uopts else None

	# check user-set opts without modifying them
	if not check_opts(uopts): sys.exit(1)

	# A special case - do this here, before opt gets set from g.dfl_vars
	if opt.usr_randchars: g.use_urandchars = True

	# If user opt is unset, set it to default value in mmgen.config (g):
	# If set, convert its type based on value in mmgen.config
	for k in g.dfl_vars:
		if k in opt.__dict__ and opt.__dict__[k] != None:
			typeconvert_from_dfl(k)
		else: opt.__dict__[k] = g.__dict__[k]

	if opt.debug: opt.verbose = True

	if g.debug:
		Msg("opts after typeconvert:")
		for k in opt.__dict__:
			if opt.__dict__[k] != None and k != "opts":
 				msg("    %-18s: %s" % (k,opt.__dict__[k]))

	for l in (
	('from_incog_hidden','from_incog','from_seed','from_mnemonic','from_brain'),
	('export_incog','export_incog_hex','export_incog_hidden','export_mnemonic',
	'export_seed'),
	('quiet','verbose')
	): warn_incompatible_opts(l)

	return args

# save for debugging
def show_all_opts():
	msg("Processed options:")
	d = opt.__dict__
	for k in [o for o in d if o != "opts"]:
		tstr = type(d[k]) if d[k] not in (None,False,True) else ""
		msg("%-20s: %-8s %s" % (k, d[k], tstr))

def check_opts(usr_opts):       # Returns false if any check fails

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

	global opt
	for key,val in [(k,getattr(opt,k)) for k in usr_opts]:

		what = "parameter for '--%s' option" % key.replace("_","-")

		# Check for file existence and readability
		if key in ('keys_from_file','mmgen_keys_from_file',
				'passwd_file','keysforaddrs','comment_file'):
			from mmgen.util import check_infile
			check_infile(val)  # exits on error
			continue

		if key == 'outdir':
			from mmgen.util import check_outdir
			check_outdir(val)  # exits on error
		elif key == 'label':
			if not opt_compares(len(val),"<=",g.max_wallet_label_len,"label length"):
				return False
			try: val.decode("ascii")
			except:
				msg("ERROR: label contains a non-ASCII symbol")
				return False
			w = "character in label"
			for ch in list(val):
				if not opt_is_in_list(ch,g.wallet_label_symbols,w): return False
		elif key == 'export_incog_hidden' or key == 'from_incog_hidden':
			if key == 'from_incog_hidden':
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
		elif key == 'from_brain':
			if not opt_splits(val,",",2,what): return False
			l,p = val.split(",")
			w = "seed length " + what
			if not opt_is_int(l,w): return False
			if not opt_is_in_list(int(l),g.seed_lens,w): return False
			w = "hash preset " + what
			if not opt_is_in_list(p,g.hash_presets.keys(),w): return False
		elif key == 'seed_len':
			if not opt_is_int(val,what): return False
			if not opt_is_in_list(int(val),g.seed_lens,what): return False
		elif key == 'hash_preset':
			if not opt_is_in_list(val,g.hash_presets.keys(),what): return False
		elif key == 'usr_randchars':
			if not opt_is_int(val,what): return False
			if not opt_compares(val,">=",g.min_urandchars,what): return False
			if not opt_compares(val,"<=",g.max_urandchars,what): return False
		else:
			if g.debug: Msg("check_opts(): No test for opt '%s'" % key)

	return True
