#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2017 Philemon <mmgen-py@yandex.com>
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
mmgen-tool:  Perform various MMGen- and Bitcoin-related operations.
             Part of the MMGen suite
"""

from mmgen.common import *
import mmgen.tool as tool

def opts_data(): return {
	'desc':    'Perform various {pnm}- and Bitcoin-related operations'.format(pnm=g.proj_name),
	'usage':   '[opts] <command> <command args>',
	'options': """
-d, --outdir=       d Specify an alternate directory 'd' for output
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-P, --passwd-file= f  Get passphrase from file 'f'.
-q, --quiet           Produce quieter output
-r, --usr-randchars=n Get 'n' characters of additional randomness from
                      user (min={g.min_urandchars}, max={g.max_urandchars})
-v, --verbose         Produce more verbose output
""".format(g=g),
	'notes': """

                               COMMANDS
{}
Type '{} help <command> for help on a particular command
""".format(tool.cmd_help,g.prog_name)
}

cmd_args = opts.init(opts_data,add_opts=['hidden_incog_input_params','in_fmt'])

if len(cmd_args) < 1: opts.usage()

Command = cmd_args.pop(0).capitalize()

if Command == 'Help' and not cmd_args: tool.usage(None)

if Command not in tool.cmd_data:
	die(1,"'%s': no such command" % Command.lower())

args,kwargs = tool.process_args(Command,cmd_args)
ret = tool.__dict__[Command](*args,**kwargs)
sys.exit(0 if ret in (None,True) else 1) # some commands die, some return False on failure
