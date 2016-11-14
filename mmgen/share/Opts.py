#!/usr/bin/env python
#
# Opts.py, an options parsing library for Python.  Copyright (C) 2014-2016
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

"""
Opts.py:  Generic options handling
"""

import sys, getopt
from mmgen.util import pp_die,pp_msg # DEBUG

def usage(opts_data):
	print 'USAGE: %s %s' % (opts_data['prog_name'], opts_data['usage'])
	sys.exit(2)

def print_help(opts_data):
	pn = opts_data['prog_name']
	pn_len = str(len(pn)+2)
	print ('  %-'+pn_len+'s %s') % (pn.upper()+':', opts_data['desc'].strip())
	print ('  %-'+pn_len+'s %s %s')%('USAGE:', pn, opts_data['usage'].strip())
	sep = '\n    '
	print '  OPTIONS:' + sep + sep.join(opts_data['options'].strip().splitlines())
	if 'notes' in opts_data:
		print '  ' + '\n  '.join(opts_data['notes'][1:-1].splitlines())


def process_opts(argv,opts_data,short_opts,long_opts):

	import os
	opts_data['prog_name'] = os.path.basename(sys.argv[0])
	long_opts  = [i.replace('_','-') for i in long_opts]

#	pp_msg(long_opts) # DEBUG
	try: cl_opts,args = getopt.getopt(argv[1:], short_opts.replace('-',''), long_opts)
	except getopt.GetoptError as err:
		print str(err); sys.exit(2)

	sopts_list = ':_'.join(['_'.join(list(i)) for i in short_opts.split(':')]).split('_')
	opts = {}

#	pp_msg(cl_opts) # DEBUG
#	pp_msg(sopts_list) # DEBUG
#	pp_die(args)
	for opt, arg in cl_opts:
		if   opt in ('-h','--help'): print_help(opts_data); sys.exit()
		elif opt[:2] == '--' and opt[2:] in long_opts:
			opts[opt[2:].replace('-','_')] = True
		elif opt[:2] == '--' and opt[2:]+'=' in long_opts:
			opts[opt[2:].replace('-','_')] = arg
		elif opt[1] != '-' and opt[1] in sopts_list:
			opts[long_opts[sopts_list.index(opt[1:])].replace('-','_')] = True
		elif opt[1] != '-' and opt[1:]+':' in sopts_list:
			opts[long_opts[sopts_list.index(
					opt[1:]+':')][:-1].replace('-','_')] = arg
		else: assert False, 'Invalid option'

	if 'sets' in opts_data:
		for o_in,v_in,o_out,v_out in opts_data['sets']:
			if o_in in opts:
				v = opts[o_in]
				if (v and v_in == bool) or v == v_in:
					if o_out in opts and opts[o_out] != v_out:
						sys.stderr.write(
				'Option conflict:\n  --%s=%s, with\n  --%s=%s\n' % (
					o_out.replace('_','-'),opts[o_out],
					o_in.replace('_','-'),opts[o_in]
				))
						sys.exit(1)
					else:
						opts[o_out] = v_out

	return opts,args


def parse_opts(argv,opts_data,opt_filter=None):

	import re
	pat = r'^-([a-zA-Z0-9-]), --([a-zA-Z0-9-]{2,64})(=| )(.+)'
	od,skip = [],True

	for l in opts_data['options'].strip().splitlines():
		m = re.match(pat,l)
		if m:
			skip = (False,True)[bool(opt_filter) and m.group(1) not in opt_filter]
			app = (['',''],[':','='])[m.group(3) == '=']
			od.append(list(m.groups()) + app + [skip])
		else:
			if not skip: od[-1][3] += '\n' + l

	opts_data['options'] = '\n'.join(
		['{:<3} --{} {}'.format(
			('-'+d[0]+',','')[d[0]=='-'],d[1],d[3]) for d in od if d[6] == False]
	)
#	print opts_data['options']; sys.exit() # DEBUG
# 	pp_die(od) # DEBUG
	short_opts    = ''.join([d[0]+d[4] for d in od if d[6] == False])
	long_opts     = [d[1].replace('-','_')+d[5] for d in od if d[6] == False]
	skipped_opts  = [d[1].replace('-','_') for d in od if d[6] == True]
#	pp_die(short_opts) # DEBUG
#	pp_msg(long_opts) # DEBUG

	opts,args = process_opts(argv,opts_data,short_opts,long_opts)
#	pp_die(opts) # DEBUG

	return opts,args,short_opts,long_opts,skipped_opts
