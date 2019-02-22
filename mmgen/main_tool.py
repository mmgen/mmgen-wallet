#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2019 The MMGen Project <mmgen@tuta.io>
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
mmgen-tool:  Perform various MMGen- and cryptocoin-related operations.
             Part of the MMGen suite
"""

from mmgen.common import *

def make_cmd_help():
	import mmgen.tool
	out = []
	for bc in mmgen.tool.MMGenToolCmd.__bases__:
		cls_doc = bc.__doc__.strip().split('\n')
		for l in cls_doc:
			if l is cls_doc[0]: l += ':'
			l = l.replace('\t','',1)
			if l:
				l = l.replace('\t','  ')
				out.append(l[0].upper() + l[1:])
			else:
				out.append('')
		out.append('')

		cls_funcs = bc.user_commands()
		max_w = max(map(len,cls_funcs))
		fs = '  {{:{}}} - {{}}'.format(max_w)
		for func in cls_funcs:
			m = getattr(bc,func)
			if m.__doc__:
				out.append(fs.format(func,
					pretty_format(  m.__doc__.strip().replace('\n\t\t',' '),
									width=79-(max_w+7),
									pfx=' '*(max_w+5)).lstrip()
				))
		out.append('')

	return '\n'.join(out)

opts_data = lambda: {
	'desc':    'Perform various {pnm}- and cryptocoin-related operations'.format(pnm=g.proj_name),
	'usage':   '[opts] <command> <command args>',
	'options': """
-d, --outdir=       d Specify an alternate directory 'd' for output
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-P, --passwd-file= f  Get passphrase from file 'f'.
-q, --quiet           Produce quieter output
-r, --usr-randchars=n Get 'n' characters of additional randomness from
                      user (min={g.min_urandchars}, max={g.max_urandchars})
-t, --type=t          Specify address type (valid options: 'legacy',
                      'compressed', 'segwit', 'bech32', 'zcash_z')
-v, --verbose         Produce more verbose output
""".format(g=g),
	'notes': """

                               COMMANDS

{ch}
Type '{pn} help <command>' for help on a particular command
""".format(pn=g.prog_name,ch=make_cmd_help())
}

cmd_args = opts.init(opts_data,add_opts=['hidden_incog_input_params','in_fmt','use_old_ed25519'])

if len(cmd_args) < 1: opts.usage()
cmd = cmd_args.pop(0)

import mmgen.tool as tool
tc = tool.MMGenToolCmd()

if cmd in ('help','usage') and cmd_args:
	cmd_args[0] = 'command_name=' + cmd_args[0]

if cmd not in dir(tc):
	die(1,"'{}': no such command".format(cmd))

args,kwargs = tool._process_args(cmd,cmd_args)

ret = getattr(tc,cmd)(*args,**kwargs)

tool._process_result(ret,to_screen=True,pager='pager' in kwargs and kwargs['pager'])
