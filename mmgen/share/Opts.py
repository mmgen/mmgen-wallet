#!/usr/bin/env python3
#
# Opts.py, an options parsing library for Python.
# Copyright (C)2013-2021 The MMGen Project <mmgen@tuta.io>
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

import sys,re
from collections import namedtuple

pat = re.compile(r'^-([a-zA-Z0-9-]), --([a-zA-Z0-9-]{2,64})(=| )(.+)')

def usage(opts_data):
	print('USAGE: {} {}'.format(opts_data['prog_name'], opts_data['usage']))
	sys.exit(2)

def print_help(proto,po,opts_data,opt_filter):

	def parse_lines(text):
		filtered = False
		for line in text.strip().splitlines():
			m = pat.match(line)
			if m:
				filtered = bool(opt_filter and m[1] not in opt_filter)
				if not filtered:
					yield fs.format( ('-'+m[1]+',','')[m[1]=='-'], m[2], m[4] )
			elif not filtered:
				yield line

	opts_type,fs = ('options','{:<3} --{} {}') if 'help' in po.user_opts else ('long_options','{}  --{} {}')
	t = opts_data['text']
	c = opts_data['code']
	nl = '\n  '

	pn = opts_data['prog_name']

	from mmgen.help import help_notes_func
	def help_notes(k):
		return help_notes_func(proto,k)

	def gen_arg_tuple(func,text):
		d = {'proto': proto,'help_notes':help_notes}
		for arg in func.__code__.co_varnames:
			yield d[arg] if arg in d else text

	def gen_text():
		yield '  {:<{p}} {}'.format(pn.upper()+':',t['desc'].strip(),p=len(pn)+1)
		yield '{:<{p}} {} {}'.format('USAGE:',pn,t['usage'].strip(),p=len(pn)+1)
		yield opts_type.upper().replace('_',' ') + ':'

		# process code for options
		opts_text = nl.join(parse_lines(t[opts_type]))
		if opts_type in c:
			arg_tuple = tuple(gen_arg_tuple(c[opts_type],opts_text))
			yield c[opts_type](*arg_tuple)
		else:
			yield opts_text

		# process code for notes
		if opts_type == 'options' and 'notes' in t:
			notes_text = t['notes']
			if 'notes' in c:
				arg_tuple = tuple(gen_arg_tuple(c['notes'],notes_text))
				notes_text = c['notes'](*arg_tuple)
			for line in notes_text.splitlines():
				yield line

	print(nl.join(gen_text()))
	sys.exit(0)

def process_uopts(opts_data,short_opts,long_opts):

	import os,getopt
	opts_data['prog_name'] = os.path.basename(sys.argv[0])

	try:
		cl_uopts,uargs = getopt.getopt(sys.argv[1:],''.join(short_opts),long_opts)
	except getopt.GetoptError as e:
		print(e.args[0])
		sys.exit(1)

	def get_uopts():
		for uopt,uparm in cl_uopts:
			if uopt.startswith('--'):
				lo = uopt[2:]
				if lo in long_opts:
					yield (lo.replace('-','_'), True)
				else: # lo+'=' in long_opts
					yield (lo.replace('-','_'), uparm)
			else: # uopt.startswith('-')
				so = uopt[1]
				if so in short_opts:
					yield (long_opts[short_opts.index(so)].replace('-','_'), True)
				else: # so+':' in short_opts
					yield (long_opts[short_opts.index(so+':')][:-1].replace('-','_'), uparm)

	uopts = dict(get_uopts())

	if 'sets' in opts_data:
		for a_opt,a_val,b_opt,b_val in opts_data['sets']:
			if a_opt in uopts:
				u_val = uopts[a_opt]
				if (u_val and a_val == bool) or u_val == a_val:
					if b_opt in uopts and uopts[b_opt] != b_val:
						sys.stderr.write(
							'Option conflict:'
							+ '\n  --{}={}, with'.format(b_opt.replace('_','-'),uopts[b_opt])
							+ '\n  --{}={}\n'.format(a_opt.replace('_','-'),uopts[a_opt]) )
						sys.exit(1)
					else:
						uopts[b_opt] = b_val

	return uopts,uargs

def parse_opts(opts_data,opt_filter=None,parse_only=False):

	short_opts,long_opts,skipped_opts = [],[],[]
	def parse_lines(opts_type):
		for line in opts_data['text'][opts_type].strip().splitlines():
			m = pat.match(line)
			if m:
				if bool(opt_filter and m[1] not in opt_filter):
					skipped_opts.append(m[2])
				else:
					if opts_type == 'options':
						short_opts.append(m[1] + ('',':')[m[3] == '='])
					long_opts.append(m[2] + ('','=')[m[3] == '='])

	for opts_type in ('options','long_options'):
		parse_lines(opts_type)

	uopts,uargs = process_uopts(opts_data,short_opts,long_opts)

	po = namedtuple('parsed_cmd_opts',['user_opts','cmd_args','opts','skipped_opts'])
	return po(
		uopts, # dict
		uargs, # list, callers can pop
		tuple(o.replace('-','_').rstrip('=') for o in long_opts),
		tuple(o.replace('-','_') for o in skipped_opts),
	)
