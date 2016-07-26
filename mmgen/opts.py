#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2016 Philemon <mmgen-py@yandex.com>
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

class opt(object): pass

import mmgen.globalvars as g
import mmgen.share.Opts
from mmgen.util import *

pw_note = """
For passphrases all combinations of whitespace are equal and leading and
trailing space is ignored.  This permits reading passphrase or brainwallet
data from a multi-line file with free spacing and indentation.
""".strip()

bw_note = """
BRAINWALLET NOTE:

To thwart dictionary attacks, it's recommended to use a strong hash preset
with brainwallets.  For a brainwallet passphrase to generate the correct
seed, the same seed length and hash preset parameters must always be used.
""".strip()

def usage():
	Msg('USAGE: %s %s' % (g.prog_name, usage_txt))
	sys.exit(2)

def print_version_info():
	Msg("""
{pgnm_uc} version {g.version}
Part of the {pnm} suite, a Bitcoin cold-storage solution for the command line.
Copyright (C) {g.Cdates} {g.author} {g.email}
""".format(pnm=g.proj_name, g=g, pgnm_uc=g.prog_name.upper()).strip())

def die_on_incompatible_opts(incompat_list):
	for group in incompat_list:
		bad = [k for k in opt.__dict__ if opt.__dict__[k] and k in group]
		if len(bad) > 1:
			die(1,'Conflicting options: %s' % ', '.join([fmt_opt(b) for b in bad]))

def _typeconvert_from_dfl(key):

	global opt

	gval = g.__dict__[key]
	uval = opt.__dict__[key]
	gtype = type(gval)

	try:
		setattr(opt,key,gtype(uval))
	except:
		d = {
			'int':   'an integer',
			'str':   'a string',
			'float': 'a float',
			'bool':  'a boolean value',
		}
		die(1, "'%s': invalid parameter for '--%s' option (not %s)" % (
			uval,
			key.replace('_','-'),
			d[gtype.__name__]
		))

	if g.debug:
		Msg('Opt overriden by user:\n    %-18s: %s' % (
				key, ('%s -> %s' % (gval,uval))
			))

def fmt_opt(o): return '--' + o.replace('_','-')

def _show_hash_presets():
	fs = '  {:<7} {:<6} {:<3}  {}'
	msg('Available parameters for scrypt.hash():')
	msg(fs.format('Preset','N','r','p'))
	for i in sorted(g.hash_presets.keys()):
		msg(fs.format("'%s'" % i, *g.hash_presets[i]))
	msg('N = memory usage (power of two), p = iterations (rounds)')

def init(opts_data,add_opts=[],opt_filter=None):

	if len(sys.argv) == 2 and sys.argv[1] == '--version':
		print_version_info()
		sys.exit()

	uopts,args,short_opts,long_opts,skipped_opts = \
		mmgen.share.Opts.parse_opts(sys.argv,opts_data,opt_filter=opt_filter)

	if g.debug:
		d = (
			('Short opts',         short_opts),
			('Long opts',          long_opts),
			('Skipped opts',       skipped_opts),
			('User-selected opts', uopts),
			('Cmd args',           args),
		)
		Msg('\n=== opts.py debug ===')
		for e in d: Msg('    {:<20}: {}'.format(*e))

	# Save this for usage()
	global usage_txt
	usage_txt = opts_data['usage']

	# We don't need this data anymore
	del mmgen.share.Opts
	for k in 'prog_name','desc','usage','options','notes':
		if k in opts_data: del opts_data[k]

	# Transfer uopts into opt, setting program's opts + required opts to None if not set by user
	for o in [s.rstrip('=') for s in long_opts] + \
			g.required_opts + add_opts + skipped_opts:
		setattr(opt,o,uopts[o] if o in uopts else None)

	# A special case - do this here, before opt gets set from g.dfl_vars
	if opt.usr_randchars: g.use_urandchars = True

	# If user opt is set, convert its type based on value in mmgen.globalvars (g)
	# If unset, set it to default value in mmgen.globalvars (g)
	setattr(opt,'set_by_user',[])
	for k in g.dfl_vars:
		if k in opt.__dict__ and opt.__dict__[k] != None:
			_typeconvert_from_dfl(k)
			opt.set_by_user.append(k)
		else:
			setattr(opt,k,g.__dict__[k])

	# Check user-set opts without modifying them
	if not check_opts(uopts):
		sys.exit(1)

	if opt.show_hash_presets:
		_show_hash_presets()
		sys.exit()

	if opt.debug: opt.verbose = True

	if g.debug:
		a = [k for k in dir(opt) if k[:2] != '__' and getattr(opt,k) != None]
		b = [k for k in dir(opt) if k[:2] != '__' and getattr(opt,k) == None]
		Msg('    Opts after processing:')
		for k in a:
			v = getattr(opt,k)
			Msg('        %-18s: %-6s [%s]' % (k,v,type(v).__name__))
		Msg("    Opts set to 'None':")
		Msg('        %s\n' % '\n        '.join(b))

	die_on_incompatible_opts(g.incompatible_opts)

	return args


def check_opts(usr_opts):       # Returns false if any check fails

	def opt_splits(val,sep,n,desc):
		sepword = 'comma' if sep == ',' else 'colon' if sep == ':' else "'%s'" % sep
		try: l = val.split(sep)
		except:
			msg("'%s': invalid %s (not %s-separated list)" % (val,desc,sepword))
			return False

		if len(l) == n: return True
		else:
			msg("'%s': invalid %s (%s %s-separated items required)" %
					(val,desc,n,sepword))
			return False

	def opt_compares(val,op,target,desc,what=''):
		if what: what += ' '
		if not eval('%s %s %s' % (val, op, target)):
			msg('%s: invalid %s (%snot %s %s)' % (val,desc,what,op,target))
			return False
		return True

	def opt_is_int(val,desc):
		try: int(val)
		except:
			msg("'%s': invalid %s (not an integer)" % (val,desc))
			return False
		return True

	def opt_is_in_list(val,lst,desc):
		if val not in lst:
			q,sep = (('',','),("'","','"))[type(lst[0]) == str]
			msg('{q}{v}{q}: invalid {w}\nValid choices: {q}{o}{q}'.format(
					v=val,w=desc,q=q,
					o=sep.join([str(i) for i in sorted(lst)])
				))
			return False
		return True

	def opt_unrecognized(key,val,desc):
		msg("'%s': unrecognized %s for option '%s'"
				% (val,desc,fmt_opt(key)))
		return False

	def opt_display(key,val='',beg='For selected',end=':\n'):
		s = '%s=%s' % (fmt_opt(key),val) if val else fmt_opt(key)
		msg_r("%s option '%s'%s" % (beg,s,end))

	global opt
	for key,val in [(k,getattr(opt,k)) for k in usr_opts]:

		desc = "parameter for '%s' option" % fmt_opt(key)

		from mmgen.util import check_infile,check_outfile,check_outdir
		# Check for file existence and readability
		if key in ('keys_from_file','mmgen_keys_from_file',
				'passwd_file','keysforaddrs','comment_file'):
			check_infile(val)  # exits on error
			continue

		if key == 'outdir':
			check_outdir(val)  # exits on error
# 		# NEW
		elif key in ('in_fmt','out_fmt'):
			from mmgen.seed import SeedSource,IncogWallet,Brainwallet,IncogWalletHidden
			sstype = SeedSource.fmt_code_to_type(val)
			if not sstype:
				return opt_unrecognized(key,val,'format code')
			if key == 'out_fmt':
				p = 'hidden_incog_output_params'
				if sstype == IncogWalletHidden and not getattr(opt,p):
						die(1,'Hidden incog format output requested. You must supply'
						+ " a file and offset with the '%s' option" % fmt_opt(p))
				if issubclass(sstype,IncogWallet) and opt.old_incog_fmt:
					opt_display(key,val,beg='Selected',end=' ')
					opt_display('old_incog_fmt',beg='conflicts with',end=':\n')
					die(1,'Export to old incog wallet format unsupported')
				elif issubclass(sstype,Brainwallet):
					die(1,'Output to brainwallet format unsupported')
		elif key in ('hidden_incog_input_params','hidden_incog_output_params'):
			a = val.split(',')
			if len(a) != 2:
				opt_display(key,val)
				msg('Option requires two comma-separated arguments')
				return False
			if not opt_is_int(a[1],desc): return False
			if key == 'hidden_incog_input_params':
				check_infile(a[0],blkdev_ok=True)
				key2 = 'in_fmt'
			else:
				import os
				try: os.stat(a[0])
				except:
					b = os.path.dirname(a[0])
					if b: check_outdir(b)
				else: check_outfile(a[0],blkdev_ok=True)
				key2 = 'out_fmt'
			if hasattr(opt,key2):
				val2 = getattr(opt,key2)
				from mmgen.seed import IncogWalletHidden
				if val2 and val2 not in IncogWalletHidden.fmt_codes:
					die(1,
						'Option conflict:\n  %s, with\n  %s=%s' % (
						fmt_opt(key),fmt_opt(key2),val2
					))
		elif key == 'seed_len':
			if not opt_is_int(val,desc): return False
			if not opt_is_in_list(int(val),g.seed_lens,desc): return False
		elif key == 'hash_preset':
			if not opt_is_in_list(val,g.hash_presets.keys(),desc): return False
		elif key == 'brain_params':
			a = val.split(',')
			if len(a) != 2:
				opt_display(key,val)
				msg('Option requires two comma-separated arguments')
				return False
			d = 'seed length ' + desc
			if not opt_is_int(a[0],d): return False
			if not opt_is_in_list(int(a[0]),g.seed_lens,d): return False
			d = 'hash preset ' + desc
			if not opt_is_in_list(a[1],g.hash_presets.keys(),d): return False
		elif key == 'usr_randchars':
			if val == 0: continue
			if not opt_is_int(val,desc): return False
			if not opt_compares(val,'>=',g.min_urandchars,desc): return False
			if not opt_compares(val,'<=',g.max_urandchars,desc): return False
		else:
			if g.debug: Msg("check_opts(): No test for opt '%s'" % key)

	return True
