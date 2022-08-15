#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
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
tool/help.py: Help screen routines for the 'mmgen-tool' utility
"""

from .common import tool_cmd_base
import mmgen.main_tool as main_tool

def main_help():

	from ..util import pretty_format

	def do():
		for clsname,cmdlist in main_tool.mods.items():
			cls = main_tool.get_mod_cls(clsname)
			cls_doc = cls.__doc__.strip().split('\n')
			for l in cls_doc:
				if l is cls_doc[0]:
					l += ':'
				l = l.replace('\t','',1)
				if l:
					l = l.replace('\t','  ')
					yield l[0].upper() + l[1:]
				else:
					yield ''
			yield ''

			max_w = max(map(len,cmdlist))

			for cmdname in cmdlist:
				code = getattr(cls,cmdname)
				if code.__doc__:
					yield '  {:{}} - {}'.format(
						cmdname,
						max_w,
						pretty_format(
							code.__doc__.strip().split('\n')[0].strip(),
							width = 79-(max_w+7),
							pfx   = ' '*(max_w+5)).lstrip()
					)
			yield ''

	return '\n'.join(do())

def gen_tool_usage():

	from ..util import capfirst

	m1 = """
		USAGE INFORMATION FOR MMGEN-TOOL COMMANDS:

		  Arguments with only type specified in square brackets are required

		  Arguments with both type and default value specified in square brackets are
		  optional and must be specified in the form ‘name=value’

		  For more detailed usage information for a particular tool command, type
		  ‘mmgen-tool help <command name>’
		"""

	m2 = """
		  To force a command to read from STDIN instead of file (for commands taking
		  a filename as their first argument), substitute "-" for the filename.


		EXAMPLES:

		  Generate a random LTC Bech32 public/private keypair:
		  $ mmgen-tool -r0 --coin=ltc --type=bech32 randpair

		  Generate a DASH address with compressed public key from the supplied WIF key:
		  $ mmgen-tool --coin=dash --type=compressed wif2addr XJkVRC3eGKurc9Uzx1wfQoio3yqkmaXVqLMTa6y7s3M3jTBnmxfw

		  Generate a well-known burn address:
		  $ mmgen-tool hextob58chk 000000000000000000000000000000000000000000

		  Generate a random 12-word seed phrase:
		  $ mmgen-tool -r0 mn_rand128 fmt=bip39

		  Same as above, but get additional entropy from user:
		  $ mmgen-tool mn_rand128 fmt=bip39

		  Encode bytes from a file to base 58:
		  $ mmgen-tool bytestob58 /etc/timezone pad=20

		  Reverse a hex string:
		  $ mmgen-tool hexreverse "deadbeefcafe"

		  Same as above, but supply input via STDIN:
		  $ echo "deadbeefcafe" | mmgen-tool hexreverse -
		"""

	for line in m1.lstrip().split('\n'):
		yield line.lstrip('\t')

	for clsname,cmdlist in main_tool.mods.items():
		cls = main_tool.get_mod_cls(clsname)
		cls_docstr = cls.__doc__.strip()
		yield ''
		yield '  {}:'.format( capfirst(cls_docstr.split('\n')[0].strip()) )
		yield ''

		if '\n' in cls_docstr:
			for line in cls_docstr.split('\n')[2:]:
				yield '    ' + line.lstrip('\t')
			yield ''

		max_w = max(map(len,cmdlist))
		for cmdname in cmdlist:
			yield '    {a:{w}} {b}'.format(
				a = cmdname,
				b = main_tool.create_call_sig(cmdname,cls,as_string=True),
				w = max_w )
		yield ''

	for line in m2.rstrip().split('\n'):
		yield line.lstrip('\t')

def gen_tool_cmd_usage(mod,cmdname):

	from ..globalvars import g
	from ..util import capfirst

	cls = main_tool.get_mod_cls(mod)
	docstr = getattr(cls,cmdname).__doc__.strip()
	args,kwargs,kwargs_types,flag = main_tool.create_call_sig(cmdname,cls)

	yield '{a}\n\nUSAGE: {b} {c} {d}{e}'.format(
		a = capfirst( docstr.split('\n')[0].strip() ),
		b = g.prog_name,
		c = cmdname,
		d = main_tool.create_call_sig(cmdname,cls,as_string=True),
		e = '\n\n' + fmt('\n'.join(docstr.split('\n')[1:]),strip_char='\t').rstrip()
			if '\n' in docstr else '' )

def usage(cmdname=None,exit_val=1):

	from ..util import Msg,die,do_pager

	if cmdname:
		for mod,cmdlist in main_tool.mods.items():
			if cmdname in cmdlist:
				Msg('\n'.join(gen_tool_cmd_usage(mod,cmdname)))
				break
		else:
			die(1,f'{cmdname!r}: no such tool command')
	else:
		do_pager('\n'.join(gen_tool_usage()))

	import sys
	sys.exit(exit_val)

class tool_cmd(tool_cmd_base):
	"help/usage commands"

	def help(self,command_name=''):
		"display usage information for a single command or all commands"
		usage(command_name,exit_val=0)

	def usage(self,command_name=''):
		"display usage information for a single command or all commands"
		usage(command_name,exit_val=0)
