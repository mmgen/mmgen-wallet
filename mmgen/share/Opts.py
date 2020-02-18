#!/usr/bin/env python3
#
# Opts.py, an options parsing library for Python.
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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
Opts.py:  Generic options parsing
"""

import sys,getopt
import collections

def usage(opts_data):
	print('USAGE: {} {}'.format(opts_data['prog_name'], opts_data['usage']))
	sys.exit(2)

def print_help(opts_data,opt_filter):
	t = opts_data['text']
	c = opts_data['code']

	# header
	pn = opts_data['prog_name']
	out  = '  {:<{p}} {}\n'.format(pn.upper()+':',t['desc'].strip(),p=len(pn)+1)
	out += '  {:<{p}} {} {}\n'.format('USAGE:',pn,t['usage'].strip(),p=len(pn)+1)

	# options
	if opts_data['do_help'] == 'longhelp':
		hdr,ls,es = ('  LONG OPTIONS:','','    ')
		text = t['long_options'].strip()
		code = c['long_options'] if 'long_options' in c else None
	else:
		hdr,ls,es = ('OPTIONS:','  ','')
		text = t['options']
		code = c['options'] if 'options' in c else None

	ftext = code(text) if code else text
	out += '{ls}{}\n{ls}{es}{}'.format(hdr,('\n'+ls).join(ftext.splitlines()),ls=ls,es=es)

	# notes
	if opts_data['do_help'] == 'help' and 'notes' in t:
		ftext = c['notes'](t['notes']) if 'notes' in c else t['notes']
		out += '\n  ' + '\n  '.join(ftext.rstrip().splitlines())

	print(out)
	sys.exit(0)

def process_opts(opts_data,short_opts,long_opts):

	import os
	opts_data['prog_name'] = os.path.basename(sys.argv[0])
	long_opts  = [i.replace('_','-') for i in long_opts]

	so_str = short_opts.replace('-:','').replace('-','')
	try: cl_opts,args = getopt.getopt(sys.argv[1:], so_str, long_opts)
	except getopt.GetoptError as err:
		print(str(err))
		sys.exit(2)

	sopts_list = ':_'.join(['_'.join(list(i)) for i in short_opts.split(':')]).split('_')
	opts = {}
	opts_data['do_help'] = False

	for opt,arg in cl_opts:
		if opt in ('-h','--help'):
			opts_data['do_help'] = 'help'
		elif opt == '--longhelp':
			opts_data['do_help'] = 'longhelp'
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
							'Option conflict:\n  --{}={}, with\n  --{}={}\n'.format(
								o_out.replace('_','-'),opts[o_out],
								o_in.replace('_','-'),opts[o_in]))
						sys.exit(1)
					else:
						opts[o_out] = v_out

	return opts,args

def parse_opts(opts_data,opt_filter=None,parse_only=False):

	import re
	pat = r'^-([a-zA-Z0-9-]), --([a-zA-Z0-9-]{2,64})(=| )(.+)'
	od_all = []

	for k in ('options','long_options'):
		if k not in opts_data['text']: continue
		od,skip = [],True
		for l in opts_data['text'][k].strip().splitlines():
			m = re.match(pat,l)
			if m:
				skip = bool(opt_filter) and m.group(1) not in opt_filter
				app = (['',''],[':','='])[m.group(3) == '=']
				od.append(list(m.groups()) + app + [skip])
			else:
				if not skip: od[-1][3] += '\n' + l

		if not parse_only:
			opts_data['text'][k] = '\n'.join(
				['{:<3} --{} {}'.format(
					('-'+d[0]+',','')[d[0]=='-'],d[1],d[3]) for d in od if d[6] == False]
			)
		od_all += od

	short_opts    = ''.join([d[0]+d[4] for d in od_all if d[6] == False])
	long_opts     = [d[1].replace('-','_')+d[5] for d in od_all if d[6] == False]
	skipped_opts  = [d[1].replace('-','_') for d in od_all if d[6] == True]

	opts,args = process_opts(opts_data,short_opts,long_opts)

	return opts,args,short_opts,long_opts,skipped_opts
